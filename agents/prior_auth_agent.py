"""Prior authorization request preparation agent using OpenAI SDK."""
from openai import OpenAI
from typing import Dict
import json
from utils.config import Config

class PriorAuthAgent:
    """Agent for preparing prior authorization requests."""
    
    def __init__(self):
        """Initialize the prior auth agent."""
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
    
    def prepare_prior_auth_request(self, document_data: Dict, codes: Dict, patient_info: Dict) -> Dict:
        """Prepare a complete prior authorization request."""
        
        system_prompt = """You are a prior authorization specialist. Your task is to prepare comprehensive prior authorization requests that include:
1. Complete patient information
2. Provider information
3. Clinical justification
4. Medical necessity documentation
5. All required CPT and ICD codes
6. Supporting documentation summary

Create a well-structured, professional prior authorization request that maximizes approval chances."""
        
        user_prompt = f"""Prepare a prior authorization request based on the following information:

Patient Information:
{json.dumps(patient_info, indent=2)}

Clinical Information:
{json.dumps(document_data.get('clinical_info', {}), indent=2)}

Extracted Codes:
CPT Codes: {', '.join(codes.get('cpt_codes', []))}
ICD Codes: {', '.join(codes.get('icd_codes', []))}

Treatment Plan:
{json.dumps(document_data.get('treatment', {}), indent=2)}

Please provide a JSON response with the following structure:
{{
    "request_summary": "brief summary of the prior auth request",
    "patient_section": {{
        "name": "patient name",
        "dob": "date of birth",
        "member_id": "member ID if available",
        "insurance": "insurance information"
    }},
    "provider_section": {{
        "name": "provider name",
        "npi": "NPI number",
        "specialty": "specialty",
        "contact": "contact information"
    }},
    "clinical_justification": {{
        "diagnosis": "primary diagnosis",
        "symptoms": "patient symptoms",
        "clinical_history": "relevant clinical history",
        "previous_treatments": "previous treatments attempted"
    }},
    "medical_necessity": {{
        "rationale": "why this treatment is medically necessary",
        "urgency": "urgency level",
        "expected_outcomes": "expected treatment outcomes"
    }},
    "procedure_codes": {{
        "cpt_codes": ["list of CPT codes"],
        "primary_procedure": "primary procedure description",
        "procedure_details": "detailed procedure information"
    }},
    "diagnosis_codes": {{
        "icd_codes": ["list of ICD codes"],
        "primary_diagnosis": "primary diagnosis",
        "supporting_diagnoses": ["supporting diagnoses"]
    }},
    "supporting_documentation": {{
        "clinical_notes": "summary of clinical notes",
        "test_results": "relevant test results",
        "imaging": "imaging findings if applicable"
    }},
    "request_priority": "standard/urgent/expedited",
    "completeness_check": {{
        "all_required_fields": true/false,
        "missing_items": ["list any missing items"],
        "ready_for_submission": true/false
    }}
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "prior_auth_request": result,
                "ready_for_submission": result.get("completeness_check", {}).get("ready_for_submission", False)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "prior_auth_request": {},
                "ready_for_submission": False
            }
    
    def format_for_submission(self, prior_auth_request: Dict) -> str:
        """Format the prior auth request as a submission-ready document."""
        request = prior_auth_request.get("prior_auth_request", {})
        
        formatted = f"""
PRIOR AUTHORIZATION REQUEST
{'=' * 50}

REQUEST SUMMARY
{request.get('request_summary', 'N/A')}

PATIENT INFORMATION
{'-' * 50}
Name: {request.get('patient_section', {}).get('name', 'N/A')}
DOB: {request.get('patient_section', {}).get('dob', 'N/A')}
Member ID: {request.get('patient_section', {}).get('member_id', 'N/A')}
Insurance: {request.get('patient_section', {}).get('insurance', 'N/A')}

PROVIDER INFORMATION
{'-' * 50}
Name: {request.get('provider_section', {}).get('name', 'N/A')}
NPI: {request.get('provider_section', {}).get('npi', 'N/A')}
Specialty: {request.get('provider_section', {}).get('specialty', 'N/A')}

CLINICAL JUSTIFICATION
{'-' * 50}
Diagnosis: {request.get('clinical_justification', {}).get('diagnosis', 'N/A')}
Symptoms: {request.get('clinical_justification', {}).get('symptoms', 'N/A')}
Clinical History: {request.get('clinical_justification', {}).get('clinical_history', 'N/A')}

MEDICAL NECESSITY
{'-' * 50}
{request.get('medical_necessity', {}).get('rationale', 'N/A')}

PROCEDURE CODES (CPT)
{'-' * 50}
{', '.join(request.get('procedure_codes', {}).get('cpt_codes', []))}
Primary Procedure: {request.get('procedure_codes', {}).get('primary_procedure', 'N/A')}

DIAGNOSIS CODES (ICD-10)
{'-' * 50}
{', '.join(request.get('diagnosis_codes', {}).get('icd_codes', []))}
Primary Diagnosis: {request.get('diagnosis_codes', {}).get('primary_diagnosis', 'N/A')}

REQUEST PRIORITY: {request.get('request_priority', 'standard').upper()}
"""
        return formatted
