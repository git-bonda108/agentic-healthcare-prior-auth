# Testing Guide

## Sample Medical Document Format

For testing purposes, you can create sample medical documents with the following information:

### Sample Document Content (TXT format)

```
PATIENT INFORMATION
Name: John Doe
DOB: 01/15/1975
Patient ID: P123456

PROVIDER INFORMATION
Name: Dr. Jane Smith, MD
NPI: 1234567890
Specialty: Cardiology

CHIEF COMPLAINT
Patient presents with chest pain and shortness of breath.

CLINICAL HISTORY
65-year-old male with history of hypertension and diabetes. 
Patient reports chest pain that started 2 days ago, associated with exertion.
No previous cardiac events.

DIAGNOSIS
1. Chest pain, unspecified (ICD-10: R06.02)
2. Suspected coronary artery disease (ICD-10: I25.9)

PLANNED PROCEDURES
1. Cardiac catheterization (CPT: 93458)
2. Coronary angiography (CPT: 93459)

MEDICAL NECESSITY
Cardiac catheterization is medically necessary to evaluate coronary artery disease 
and determine appropriate treatment. Patient has risk factors and symptoms 
consistent with coronary artery disease.

TREATMENT PLAN
Proceed with cardiac catheterization to assess coronary anatomy and determine 
if revascularization is needed.
```

### Expected Output

When processing this document, the system should:
- Extract patient name: John Doe
- Extract provider: Dr. Jane Smith
- Extract CPT codes: 93458, 93459
- Extract ICD codes: R06.02, I25.9
- Create a prior authorization request with all relevant information

## Testing Workflow

1. **Upload Test Document**
   - Create a text file with sample medical content
   - Upload via the Streamlit interface

2. **Verify Extraction**
   - Check that CPT and ICD codes are correctly extracted
   - Verify patient and provider information

3. **Review Prior Auth Request**
   - Check that the request is properly formatted
   - Verify all required fields are present

4. **Test Batch Processing**
   - Upload multiple files
   - Verify batch processing works correctly
   - Test confirmation prompts

5. **Test Response Processing**
   - Simulate an insurance response
   - Test denial handling
   - Verify alternative treatment suggestions

## Sample Insurance Responses

### Approval Response
```
Prior Authorization Approved
Authorization Number: PA-2024-12345
Approved CPT Codes: 93458, 93459
Valid Until: 12/31/2024
```

### Denial Response
```
Prior Authorization Denied
Denial Reason: Procedure not medically necessary based on provided documentation
Denial Code: DN-001
Appeal Deadline: 30 days from receipt
```

## Troubleshooting

### Common Issues

1. **No codes extracted**
   - Check document format
   - Verify codes are in standard format (CPT: 5 digits, ICD: Letter + digits)

2. **API errors**
   - Verify OPENAI_API_KEY is set correctly
   - Check API quota and billing

3. **File upload errors**
   - Verify file format is supported (PDF, DOCX, TXT)
   - Check file size limits
