"""Streamlit frontend for Prior Authorization Automation."""
import streamlit as st
import os
import tempfile
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime

from utils.config import Config
from core.database import PriorAuthDatabase
from core.batch_processor import BatchProcessor
from core.document_parser import DocumentParser

# Page configuration
st.set_page_config(
    page_title="Prior Authorization Automation",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "db" not in st.session_state:
    try:
        Config.validate()
        st.session_state.db = PriorAuthDatabase(Config.DATABASE_PATH)
        st.session_state.processor = BatchProcessor(st.session_state.db, Config.DEFAULT_BATCH_SIZE)
    except ValueError as e:
        st.error(f"Configuration Error: {e}")
        st.stop()

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "current_batch" not in st.session_state:
    st.session_state.current_batch = None

if "processing_status" not in st.session_state:
    st.session_state.processing_status = "idle"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-pending {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
    }
    .status-approved {
        background-color: #d4edda;
        border: 1px solid #28a745;
    }
    .status-denied {
        background-color: #f8d7da;
        border: 1px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

def confirmation_callback(batch_results: Dict, file_result: Dict, file_index: int) -> bool:
    """Callback for batch processing confirmation."""
    # Store batch results for display
    st.session_state.current_batch = batch_results
    st.session_state.current_file_result = file_result
    st.session_state.current_file_index = file_index
    # Always continue processing (confirmation handled in UI)
    return True

def main():
    """Main application."""
    st.markdown('<div class="main-header">🏥 Prior Authorization Automation</div>', unsafe_allow_html=True)
    st.markdown("**Automated AI-powered prior authorization processing for healthcare providers**")
    
    # Sidebar
    with st.sidebar:
        st.header("Configuration")
        batch_size = st.slider("Batch Size", 1, Config.MAX_BATCH_SIZE, Config.DEFAULT_BATCH_SIZE)
        st.session_state.processor.batch_size = batch_size
        
        st.header("Navigation")
        page = st.radio(
            "Select Page",
            ["Upload & Process", "View Prior Auths", "Track Status", "Appeals & Alternatives"]
        )
    
    # Main content based on selected page
    if page == "Upload & Process":
        upload_and_process_page()
    elif page == "View Prior Auths":
        view_prior_auths_page()
    elif page == "Track Status":
        track_status_page()
    elif page == "Appeals & Alternatives":
        appeals_page()

def upload_and_process_page():
    """File upload and processing page."""
    st.header("📤 Upload Medical Documents")
    
    st.info("Upload medical documents (PDF, DOCX, TXT) to automatically extract CPT/ICD codes and prepare prior authorization requests.")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["pdf", "docx", "txt", "doc"],
        accept_multiple_files=True,
        help="Upload multiple files for batch processing"
    )
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        
        # Display uploaded files
        st.subheader("Uploaded Files")
        for idx, file in enumerate(uploaded_files):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{idx + 1}. {file.name}** ({file.size / 1024:.2f} KB)")
            with col2:
                st.write(file.type)
            with col3:
                if st.button("Remove", key=f"remove_{idx}"):
                    st.session_state.uploaded_files.pop(idx)
                    st.rerun()
        
        # Process files
        if st.button("🚀 Process Files", type="primary", use_container_width=True):
            process_uploaded_files()
    
    # Show processing status
    if st.session_state.processing_status == "processing":
        st.warning("Processing in progress...")
        if st.session_state.current_batch:
            display_batch_progress(st.session_state.current_batch)
    
    elif st.session_state.processing_status == "awaiting_confirmation":
        st.info("Batch processing paused for confirmation")
        if st.session_state.current_batch:
            display_batch_confirmation(st.session_state.current_batch)

def process_uploaded_files():
    """Process uploaded files in batches."""
    if not st.session_state.uploaded_files:
        st.error("No files uploaded")
        return
    
    # Save uploaded files to temporary directory
    temp_dir = tempfile.mkdtemp()
    file_paths = []
    
    for uploaded_file in st.session_state.uploaded_files:
        file_path = os.path.join(temp_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_paths.append({
            "file_name": uploaded_file.name,
            "file_path": file_path
        })
    
    # Process in batches
    st.session_state.processing_status = "processing"
    
    total_files = len(file_paths)
    batch_size = st.session_state.processor.batch_size
    num_batches = (total_files + batch_size - 1) // batch_size
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    all_results = []
    
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_files)
        batch_files = file_paths[start_idx:end_idx]
        
        status_text.text(f"Processing batch {batch_num + 1} of {num_batches} ({len(batch_files)} files)...")
        
        # Process batch
        with st.spinner(f"Processing batch {batch_num + 1}..."):
            batch_results = st.session_state.processor.process_batch(
                batch_files,
                batch_num + 1,
                confirmation_callback
            )
        
        all_results.append(batch_results)
        
        # Show batch results
        st.success(f"✅ Batch {batch_num + 1} completed!")
        st.markdown(f"### 📋 Batch {batch_num + 1} Results - {batch_results['successful']} successful, {batch_results['failed']} failed")
        display_batch_results(batch_results)
        
        # Ask for confirmation before next batch
        if batch_num < num_batches - 1:
            st.info(f"📊 Batch {batch_num + 1} of {num_batches} completed. Review the results above.")
            st.info("💡 **Note:** Processing will continue automatically. Review results as they appear.")
        else:
            st.balloons()  # Celebrate completion!
        
        progress_bar.progress((batch_num + 1) / num_batches)
    
    st.session_state.processing_status = "completed"
    status_text.text("✅ All batches processed!")
    progress_bar.progress(1.0)
    
    # Summary
    total_processed = sum(r["processed"] for r in all_results)
    total_successful = sum(r["successful"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    
    st.success(f"**Processing Complete!** Processed: {total_processed}, Successful: {total_successful}, Failed: {total_failed}")

def display_batch_results(batch_results: Dict):
    """Display batch processing results."""
    st.write(f"**Batch {batch_results['batch_number']}** - Status: {batch_results['status']}")
    st.write(f"Processed: {batch_results['processed']}/{batch_results['total_files']}")
    st.write(f"✅ Successful: {batch_results['successful']} | ❌ Failed: {batch_results['failed']}")
    
    for idx, result in enumerate(batch_results["results"]):
        # Use container with border for each result
        with st.container():
            status_icon = "✅" if result['success'] else "❌"
            status_text = "Success" if result['success'] else "Failed"
            st.markdown(f"#### {status_icon} {result['file_name']} - {status_text}")
            
            if result["success"]:
                data = result.get("data", {})
                
                # Document Analysis
                st.markdown("##### Document Analysis")
                doc_analysis = data.get("document_analysis", {})
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Patient:**", doc_analysis.get("patient", {}).get("name", "N/A"))
                    st.write("**Provider:**", doc_analysis.get("provider", {}).get("name", "N/A"))
                with col2:
                    diagnosis = doc_analysis.get("clinical_info", {}).get("diagnosis", "N/A")
                    if isinstance(diagnosis, list):
                        diagnosis = ", ".join(diagnosis) if diagnosis else "N/A"
                    st.write("**Diagnosis:**", diagnosis)
                
                # Codes
                st.markdown("##### Extracted Codes")
                codes = data.get("codes", {})
                col1, col2 = st.columns(2)
                with col1:
                    cpt_codes = codes.get("cpt_codes", [])
                    st.write("**CPT Codes:**", ", ".join(cpt_codes) if cpt_codes else "None")
                with col2:
                    icd_codes = codes.get("icd_codes", [])
                    st.write("**ICD Codes:**", ", ".join(icd_codes) if icd_codes else "None")
                
                # Prior Auth Request - Use expander for JSON (this is fine, not nested)
                with st.expander("📄 View Prior Authorization Request (JSON)", expanded=False):
                    prior_auth = data.get("prior_auth_request", {})
                    st.json(prior_auth)
                
                # Formatted Request - Use expander for formatted text
                with st.expander("📝 View Formatted Prior Authorization Request", expanded=False):
                    formatted_request = data.get("formatted_request", "")
                    st.text_area("Submission-Ready Format", formatted_request, height=300, key=f"formatted_{idx}", label_visibility="collapsed")
                
                st.info(f"**Prior Auth ID:** {result.get('prior_auth_id')}")
            else:
                st.error(f"**Error:** {result.get('error', 'Unknown error')}")
            
            # Add separator between results
            if idx < len(batch_results["results"]) - 1:
                st.divider()

def display_batch_progress(batch_results: Dict):
    """Display batch processing progress."""
    st.progress(batch_results["processed"] / batch_results["total_files"])
    st.write(f"Processing: {batch_results['processed']}/{batch_results['total_files']} files")

def display_batch_confirmation(batch_results: Dict):
    """Display batch confirmation dialog."""
    st.warning("Please review the current batch before continuing")
    display_batch_results(batch_results)

def view_prior_auths_page():
    """View all prior authorizations page."""
    st.header("📋 Prior Authorization Records")
    
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "pending", "prepared", "submitted", "approved", "denied"])
    with col2:
        search_term = st.text_input("Search", placeholder="Search by patient name, file name, or ID")
    
    # Get prior auths
    if status_filter == "All":
        prior_auths = st.session_state.db.get_all_prior_auths()
    else:
        prior_auths = st.session_state.db.get_all_prior_auths(status_filter)
    
    # Filter by search term
    if search_term:
        prior_auths = [pa for pa in prior_auths if search_term.lower() in str(pa).lower()]
    
    st.write(f"**Total Records:** {len(prior_auths)}")
    
    # Display prior auths
    for pa in prior_auths:
        with st.expander(f"Prior Auth #{pa['id']} - {pa['file_name']} - Status: {pa['status']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Patient:**", pa.get("patient_name", "N/A"))
                st.write("**Provider:**", pa.get("provider_name", "N/A"))
                st.write("**Created:**", pa.get("created_at", "N/A"))
            with col2:
                st.write("**Status:**", pa.get("status", "N/A"))
                st.write("**CPT Codes:**", ", ".join(json.loads(pa.get("cpt_codes", "[]"))) or "None")
                st.write("**ICD Codes:**", ", ".join(json.loads(pa.get("icd_codes", "[]"))) or "None")
            
            if pa.get("denial_reason"):
                st.error(f"**Denial Reason:** {pa.get('denial_reason')}")
            
            if pa.get("alternative_treatments"):
                st.info("**Alternative Treatments Available**")
                alternatives = json.loads(pa.get("alternative_treatments", "[]"))
                for alt in alternatives:
                    st.write(f"- {alt.get('treatment_name', 'N/A')}")

def track_status_page():
    """Track prior authorization status page."""
    st.header("📊 Track Prior Authorization Status")
    
    prior_auth_id = st.number_input("Prior Authorization ID", min_value=1, step=1)
    
    if st.button("Lookup"):
        prior_auth = st.session_state.db.get_prior_auth(prior_auth_id)
        if prior_auth:
            display_prior_auth_details(prior_auth)
        else:
            st.error("Prior authorization not found")
    
    # Response input
    st.subheader("Update with Insurance Response")
    response_text = st.text_area("Paste insurance response here", height=200)
    
    if st.button("Process Response"):
        if prior_auth_id:
            with st.spinner("Processing response..."):
                result = st.session_state.processor.process_response(prior_auth_id, response_text)
                if result["success"]:
                    st.success("Response processed successfully!")
                    analysis = result.get("analysis", {})
                    st.json(analysis)
                else:
                    st.error(f"Error: {result.get('error')}")

def display_prior_auth_details(prior_auth: Dict):
    """Display detailed prior authorization information."""
    st.subheader(f"Prior Authorization #{prior_auth['id']}")
    
    # Status box
    status = prior_auth.get("status", "unknown")
    status_class = f"status-{status}" if status in ["pending", "approved", "denied"] else "status-pending"
    st.markdown(f'<div class="status-box {status_class}">Status: {status.upper()}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**File Name:**", prior_auth.get("file_name"))
        st.write("**Patient:**", prior_auth.get("patient_name", "N/A"))
        st.write("**Provider:**", prior_auth.get("provider_name", "N/A"))
    with col2:
        st.write("**Created:**", prior_auth.get("created_at"))
        st.write("**Updated:**", prior_auth.get("updated_at"))
        if prior_auth.get("response_date"):
            st.write("**Response Date:**", prior_auth.get("response_date"))
    
    st.write("**CPT Codes:**", ", ".join(json.loads(prior_auth.get("cpt_codes", "[]"))) or "None")
    st.write("**ICD Codes:**", ", ".join(json.loads(prior_auth.get("icd_codes", "[]"))) or "None")
    
    if prior_auth.get("denial_reason"):
        st.error(f"**Denial Reason:** {prior_auth.get('denial_reason')}")

def appeals_page():
    """Appeals and alternatives page."""
    st.header("🔄 Appeals & Alternative Treatments")
    
    prior_auth_id = st.number_input("Prior Authorization ID", min_value=1, step=1, key="appeal_id")
    
    if st.button("Load Prior Auth"):
        prior_auth = st.session_state.db.get_prior_auth(prior_auth_id)
        if prior_auth:
            if prior_auth.get("status") == "denied":
                # Prepare appeal
                if st.button("Prepare Appeal"):
                    with st.spinner("Preparing appeal..."):
                        appeal = st.session_state.processor.prepare_appeal(prior_auth_id)
                        if appeal["success"]:
                            st.success("Appeal prepared!")
                            st.json(appeal.get("appeal", {}))
                        else:
                            st.error(f"Error: {appeal.get('error')}")
                
                # Show alternatives
                alternatives = json.loads(prior_auth.get("alternative_treatments", "[]"))
                if alternatives:
                    st.subheader("Alternative Treatments")
                    for alt in alternatives:
                        with st.expander(alt.get("treatment_name", "Unknown")):
                            st.write("**Coverage Likelihood:**", alt.get("coverage_likelihood", "N/A"))
                            st.write("**Clinical Appropriateness:**", alt.get("clinical_appropriateness", "N/A"))
                            st.write("**Description:**", alt.get("description", "N/A"))
                            st.write("**CPT Codes:**", ", ".join(alt.get("cpt_codes", [])))
            else:
                st.info("This prior authorization is not denied. Appeals are only available for denied requests.")
        else:
            st.error("Prior authorization not found")

if __name__ == "__main__":
    main()
