# Sample Medical Documents for Testing

This folder contains realistic medical documents for testing the Prior Authorization Automation system.

## Available Test Documents

### 1. `sample_medical_note_1.txt` - Cardiac Catheterization
- **Patient:** Sarah Johnson
- **Procedure:** Cardiac catheterization with coronary angiography
- **CPT Codes:** 93458, 93459, 93460
- **ICD Codes:** R06.02, I25.9, I10, E11.9
- **Specialty:** Cardiology

### 2. `sample_medical_note_2.txt` - Knee Replacement
- **Patient:** Robert Martinez
- **Procedure:** Total knee arthroplasty
- **CPT Code:** 27447
- **ICD Codes:** M17.11, S83.231A, M17.31
- **Specialty:** Orthopedic Surgery

### 3. `sample_medical_note_3.txt` - Brain MRI
- **Patient:** Jennifer Williams
- **Procedure:** MRI Brain with and without contrast
- **CPT Code:** 70553
- **ICD Codes:** R51.9, R42, H53.9, G35, D49.6
- **Specialty:** Neurology

### 4. `doctor_note_cardiac_stent.txt` - Cardiac Stent Placement
- **Patient:** David Thompson
- **Procedure:** Percutaneous coronary intervention with stent
- **CPT Codes:** 92920, 92928, 92921, 92929
- **ICD Codes:** I20.0, I25.119, I10, E11.9
- **Specialty:** Interventional Cardiology

### 5. `doctor_note_spine_surgery.txt` - Lumbar Microdiscectomy
- **Patient:** Maria Garcia
- **Procedure:** Lumbar microdiscectomy and decompression
- **CPT Code:** 63030
- **ICD Codes:** M51.06, M54.16, M47.16, M51.27
- **Specialty:** Neurosurgery

### 6. `doctor_note_hip_replacement.txt` - Hip Arthroplasty
- **Patient:** James Wilson
- **Procedure:** Total hip arthroplasty
- **CPT Code:** 27130
- **ICD Codes:** M16.11, M16.12, M21.7
- **Specialty:** Orthopedic Surgery

### 7. `doctor_note_shoulder_surgery.txt` - Shoulder Arthroscopy
- **Patient:** Susan Lee
- **Procedure:** Arthroscopic rotator cuff repair
- **CPT Codes:** 29827, 29826, 29807
- **ICD Codes:** M75.101, M75.111, S43.431A
- **Specialty:** Orthopedic Surgery - Sports Medicine

## Usage

1. **Upload via Streamlit UI:**
   - Navigate to "Upload & Process" page
   - Click "Choose files"
   - Select one or more test documents
   - Click "🚀 Process Files"

2. **Test Batch Processing:**
   - Upload all 7 files at once
   - Set batch size (e.g., 3 files per batch)
   - Review results after each batch

3. **Verify Extraction:**
   - Check that CPT codes are extracted correctly
   - Verify ICD codes are identified
   - Review prior authorization requests

## Document Structure

Each document includes:
- Patient demographics
- Provider information
- Clinical history and examination
- Diagnosis codes
- Procedure codes
- Medical necessity justification
- Treatment plan

All documents are formatted to match real-world medical documentation standards.
