"""Document analysis agent using OpenAI SDK."""
from openai import OpenAI
from typing import Dict, List, Optional
import json
from utils.config import Config

class DocumentAgent:
    """Agent for analyzing medical documents and extracting key information."""
    
    def __init__(self):
        """Initialize the document agent."""
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
    
    def analyze_document(self, document_text: str, file_name: str) -> Dict:
        """Analyze medical document and extract structured information."""
        
        system_prompt = """You are a medical document analysis expert. Your task is to extract key information from medical documents including:
- Patient information (name, DOB, ID if available)
- Provider information (name, NPI if available)
- Chief complaint and clinical history
- Diagnosis and clinical findings
- Treatment plans and procedures
- Any mentioned CPT or ICD codes
- Insurance information if available

Return a structured JSON response with all extracted information."""
        
        user_prompt = f"""Analyze the following medical document and extract all relevant information:

Document Name: {file_name}

Document Content:
{document_text}

Please provide a JSON response with the following structure:
{{
    "patient": {{
        "name": "patient name or null",
        "dob": "date of birth or null",
        "patient_id": "patient ID or null"
    }},
    "provider": {{
        "name": "provider name or null",
        "npi": "NPI number or null",
        "specialty": "specialty or null"
    }},
    "clinical_info": {{
        "chief_complaint": "chief complaint or null",
        "history": "clinical history or null",
        "diagnosis": "diagnosis or null",
        "findings": "clinical findings or null"
    }},
    "treatment": {{
        "plan": "treatment plan or null",
        "procedures": ["list of procedures"],
        "medications": ["list of medications"]
    }},
    "insurance": {{
        "payer": "insurance payer name or null",
        "policy_number": "policy number or null"
    }},
    "notes": "any additional relevant notes"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for accuracy
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                "success": True,
                "data": result,
                "raw_text": document_text
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
