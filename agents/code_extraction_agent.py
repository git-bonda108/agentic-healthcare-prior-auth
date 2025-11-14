"""CPT/ICD code extraction agent using OpenAI SDK."""
from openai import OpenAI
from typing import Dict, List
import json
import re
from utils.config import Config
from utils.validators import CodeValidator

class CodeExtractionAgent:
    """Agent for extracting and validating CPT and ICD codes."""
    
    def __init__(self):
        """Initialize the code extraction agent."""
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.validator = CodeValidator()
    
    def extract_codes(self, document_text: str, clinical_info: Dict) -> Dict:
        """Extract CPT and ICD codes from document and clinical information."""
        
        system_prompt = """You are a medical coding expert specializing in CPT and ICD-10 code extraction. 
Your task is to:
1. Identify all CPT codes (procedure codes) mentioned in the document
2. Identify all ICD-10 codes (diagnosis codes) mentioned in the document
3. Infer appropriate codes based on procedures and diagnoses described
4. Validate code formats
5. Provide code descriptions when possible

Return a structured JSON response with extracted codes and their descriptions."""
        
        user_prompt = f"""Extract all CPT and ICD-10 codes from the following medical information:

Clinical Information:
{json.dumps(clinical_info, indent=2)}

Document Text (excerpt):
{document_text[:2000]}

Please provide a JSON response with the following structure:
{{
    "cpt_codes": [
        {{
            "code": "CPT code",
            "description": "procedure description",
            "confidence": "high/medium/low",
            "source": "explicit/inferred"
        }}
    ],
    "icd_codes": [
        {{
            "code": "ICD-10 code",
            "description": "diagnosis description",
            "confidence": "high/medium/low",
            "source": "explicit/inferred"
        }}
    ],
    "primary_cpt": "primary CPT code if identified",
    "primary_icd": "primary ICD code if identified",
    "extraction_notes": "any notes about the extraction process"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Also use regex extraction as backup
            regex_cpt = self.validator.extract_cpt_codes(document_text)
            regex_icd = self.validator.extract_icd_codes(document_text)
            
            # Merge AI-extracted codes with regex-extracted codes
            ai_cpt_codes = [item.get("code") for item in result.get("cpt_codes", [])]
            ai_icd_codes = [item.get("code") for item in result.get("icd_codes", [])]
            
            all_cpt = list(set(ai_cpt_codes + regex_cpt))
            all_icd = list(set(ai_icd_codes + regex_icd))
            
            # Validate all codes
            validated_cpt = [code for code in all_cpt if self.validator.validate_cpt_code(code)]
            validated_icd = [code for code in all_icd if self.validator.validate_icd_code(code)]
            
            return {
                "success": True,
                "cpt_codes": validated_cpt,
                "icd_codes": validated_icd,
                "detailed_cpt": result.get("cpt_codes", []),
                "detailed_icd": result.get("icd_codes", []),
                "primary_cpt": result.get("primary_cpt"),
                "primary_icd": result.get("primary_icd"),
                "extraction_notes": result.get("extraction_notes", "")
            }
        except Exception as e:
            # Fallback to regex extraction
            regex_cpt = self.validator.extract_cpt_codes(document_text)
            regex_icd = self.validator.extract_icd_codes(document_text)
            
            return {
                "success": False,
                "error": str(e),
                "cpt_codes": regex_cpt,
                "icd_codes": regex_icd,
                "detailed_cpt": [],
                "detailed_icd": [],
                "extraction_notes": "Used regex fallback due to AI extraction error"
            }
