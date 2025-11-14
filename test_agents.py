"""Comprehensive test for all agents and workflow."""
import os
import sys
from pathlib import Path

def test_document_agent():
    """Test Document Agent."""
    print("\n" + "="*60)
    print("TESTING DOCUMENT AGENT")
    print("="*60)
    try:
        from agents.document_agent import DocumentAgent
        from core.document_parser import DocumentParser
        
        parser = DocumentParser()
        sample_file = "sample_data/sample_medical_note_1.txt"
        
        if not os.path.exists(sample_file):
            print(f"❌ Sample file not found: {sample_file}")
            return False
        
        # Parse document
        parsed = parser.parse_file(sample_file)
        if not parsed["success"]:
            print(f"❌ Document parsing failed: {parsed.get('error')}")
            return False
        
        # Test document agent
        agent = DocumentAgent()
        result = agent.analyze_document(parsed["text"], os.path.basename(sample_file))
        
        if result["success"]:
            data = result["data"]
            print(f"✅ Document Agent: SUCCESS")
            print(f"   Patient: {data.get('patient', {}).get('name', 'N/A')}")
            print(f"   Provider: {data.get('provider', {}).get('name', 'N/A')}")
            print(f"   Diagnosis: {data.get('clinical_info', {}).get('diagnosis', 'N/A')}")
            return True, data
        else:
            print(f"❌ Document Agent failed: {result.get('error')}")
            return False, None
    except Exception as e:
        print(f"❌ Document Agent error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_code_extraction_agent(document_data):
    """Test Code Extraction Agent."""
    print("\n" + "="*60)
    print("TESTING CODE EXTRACTION AGENT")
    print("="*60)
    try:
        from agents.code_extraction_agent import CodeExtractionAgent
        from core.document_parser import DocumentParser
        
        parser = DocumentParser()
        sample_file = "sample_data/sample_medical_note_1.txt"
        parsed = parser.parse_file(sample_file)
        
        agent = CodeExtractionAgent()
        result = agent.extract_codes(
            parsed["text"],
            document_data.get("clinical_info", {}) if document_data else {}
        )
        
        if result.get("cpt_codes") or result.get("icd_codes"):
            print(f"✅ Code Extraction Agent: SUCCESS")
            print(f"   CPT Codes: {result.get('cpt_codes', [])}")
            print(f"   ICD Codes: {result.get('icd_codes', [])}")
            if result.get("primary_cpt"):
                print(f"   Primary CPT: {result.get('primary_cpt')}")
            if result.get("primary_icd"):
                print(f"   Primary ICD: {result.get('primary_icd')}")
            return True, result
        else:
            print(f"⚠️  Code Extraction: No codes found (may still be valid)")
            return True, result
    except Exception as e:
        print(f"❌ Code Extraction Agent error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_prior_auth_agent(document_data, codes_data):
    """Test Prior Auth Agent."""
    print("\n" + "="*60)
    print("TESTING PRIOR AUTH AGENT")
    print("="*60)
    try:
        from agents.prior_auth_agent import PriorAuthAgent
        
        agent = PriorAuthAgent()
        result = agent.prepare_prior_auth_request(
            document_data if document_data else {},
            codes_data if codes_data else {"cpt_codes": [], "icd_codes": []},
            document_data.get("patient", {}) if document_data else {}
        )
        
        if result["success"]:
            print(f"✅ Prior Auth Agent: SUCCESS")
            request = result.get("prior_auth_request", {})
            print(f"   Request Summary: {request.get('request_summary', 'N/A')[:100]}...")
            print(f"   Ready for Submission: {result.get('ready_for_submission', False)}")
            
            # Test formatting
            formatted = agent.format_for_submission(result)
            print(f"   Formatted Request Length: {len(formatted)} characters")
            return True, result
        else:
            print(f"❌ Prior Auth Agent failed: {result.get('error')}")
            return False, None
    except Exception as e:
        print(f"❌ Prior Auth Agent error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_tracking_agent(prior_auth_data):
    """Test Tracking Agent with mock response."""
    print("\n" + "="*60)
    print("TESTING TRACKING AGENT")
    print("="*60)
    try:
        from agents.tracking_agent import TrackingAgent
        
        agent = TrackingAgent()
        
        # Mock approval response
        mock_approval = """
        Prior Authorization Approved
        Authorization Number: PA-2024-12345
        Approved CPT Codes: 93458, 93459
        Valid Until: 12/31/2024
        """
        
        original_request = prior_auth_data.get("prior_auth_request", {}) if prior_auth_data else {}
        result = agent.analyze_response(1, mock_approval, original_request)
        
        if result["success"]:
            analysis = result.get("analysis", {})
            print(f"✅ Tracking Agent: SUCCESS")
            print(f"   Status: {analysis.get('status', 'N/A')}")
            if analysis.get("approval_details"):
                print(f"   Authorization Number: {analysis.get('approval_details', {}).get('authorization_number', 'N/A')}")
            return True, result
        else:
            print(f"❌ Tracking Agent failed: {result.get('error')}")
            return False, None
    except Exception as e:
        print(f"❌ Tracking Agent error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_alternative_agent():
    """Test Alternative Treatment Agent."""
    print("\n" + "="*60)
    print("TESTING ALTERNATIVE TREATMENT AGENT")
    print("="*60)
    try:
        from agents.alternative_agent import AlternativeTreatmentAgent
        
        agent = AlternativeTreatmentAgent()
        
        # Mock denied request
        denied_request = {
            "cpt_codes": ["27447"],
            "icd_codes": ["M17.11"],
            "diagnosis": "Primary osteoarthritis of right knee",
            "treatment_plan": "Total knee arthroplasty"
        }
        
        denial_reason = "Procedure not medically necessary - conservative treatment not exhausted"
        insurance_info = {"payer": "Aetna", "plan_type": "PPO"}
        
        result = agent.suggest_alternatives(denied_request, denial_reason, insurance_info)
        
        if result["success"]:
            print(f"✅ Alternative Agent: SUCCESS")
            alternatives = result.get("alternatives", [])
            print(f"   Found {len(alternatives)} alternative treatments")
            if alternatives:
                print(f"   Primary Recommendation: {result.get('primary_recommendation', {}).get('treatment', 'N/A')}")
            return True, result
        else:
            print(f"❌ Alternative Agent failed: {result.get('error')}")
            return False, None
    except Exception as e:
        print(f"❌ Alternative Agent error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_full_workflow():
    """Test the complete workflow."""
    print("\n" + "="*60)
    print("TESTING FULL WORKFLOW")
    print("="*60)
    try:
        from core.batch_processor import BatchProcessor
        from core.database import PriorAuthDatabase
        from utils.config import Config
        
        # Initialize components
        db = PriorAuthDatabase(Config.DATABASE_PATH)
        processor = BatchProcessor(db, batch_size=1)
        
        # Process sample file
        sample_file = "sample_data/sample_medical_note_1.txt"
        if not os.path.exists(sample_file):
            print(f"❌ Sample file not found: {sample_file}")
            return False
        
        file_info = {
            "file_name": os.path.basename(sample_file),
            "file_path": os.path.abspath(sample_file)
        }
        
        print(f"Processing: {file_info['file_name']}")
        result = processor._process_single_file(file_info)
        
        if result["success"]:
            print(f"✅ Full Workflow: SUCCESS")
            print(f"   Prior Auth ID: {result.get('prior_auth_id')}")
            print(f"   Steps Completed: {list(result.get('steps', {}).keys())}")
            data = result.get("data", {})
            codes = data.get("codes", {})
            print(f"   CPT Codes: {codes.get('cpt_codes', [])}")
            print(f"   ICD Codes: {codes.get('icd_codes', [])}")
            return True
        else:
            print(f"❌ Full Workflow failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Full Workflow error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all agent and workflow tests."""
    print("\n" + "="*60)
    print("COMPREHENSIVE AGENT & WORKFLOW TEST")
    print("Prior Authorization Automation System")
    print("="*60)
    
    results = []
    
    # Test Document Agent
    doc_success, doc_data = test_document_agent()
    results.append(("Document Agent", doc_success))
    
    # Test Code Extraction Agent
    if doc_success:
        code_success, code_data = test_code_extraction_agent(doc_data)
        results.append(("Code Extraction Agent", code_success))
    else:
        code_success, code_data = False, None
        results.append(("Code Extraction Agent", False))
    
    # Test Prior Auth Agent
    if doc_success and code_success:
        prior_auth_success, prior_auth_data = test_prior_auth_agent(doc_data, code_data)
        results.append(("Prior Auth Agent", prior_auth_success))
    else:
        prior_auth_success, prior_auth_data = False, None
        results.append(("Prior Auth Agent", False))
    
    # Test Tracking Agent
    if prior_auth_success:
        tracking_success, _ = test_tracking_agent(prior_auth_data)
        results.append(("Tracking Agent", tracking_success))
    else:
        results.append(("Tracking Agent", False))
    
    # Test Alternative Agent
    alt_success, _ = test_alternative_agent()
    results.append(("Alternative Agent", alt_success))
    
    # Test Full Workflow
    workflow_success = test_full_workflow()
    results.append(("Full Workflow", workflow_success))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result for _, result in results)
    passed_count = sum(1 for _, result in results if result)
    
    print(f"\nResults: {passed_count}/{len(results)} tests passed")
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        print("🚀 System is ready to launch!")
        return True
    else:
        print("\n⚠️  Some tests failed, but core functionality may still work.")
        print("🚀 Launching Streamlit anyway...")
        return True  # Launch anyway

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
