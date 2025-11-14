"""Alternative treatment suggestion agent using OpenAI SDK."""
from openai import OpenAI
from typing import Dict, List
import json
from utils.config import Config

class AlternativeTreatmentAgent:
    """Agent for suggesting alternative covered treatments when prior auth is denied."""
    
    def __init__(self):
        """Initialize the alternative treatment agent."""
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
    
    def suggest_alternatives(self, denied_request: Dict, denial_reason: str, insurance_info: Dict) -> Dict:
        """Suggest alternative covered treatments."""
        
        system_prompt = """You are a healthcare treatment alternative specialist. Your task is to:
1. Identify clinically appropriate alternative treatments
2. Verify which alternatives are typically covered by insurance
3. Compare effectiveness and appropriateness
4. Consider patient-specific factors
5. Provide evidence-based recommendations

Focus on treatments that are both medically appropriate and likely to be covered."""
        
        user_prompt = f"""The following prior authorization request was denied. Suggest alternative covered treatments:

Original Request:
CPT Codes: {', '.join(denied_request.get('cpt_codes', []))}
ICD Codes: {', '.join(denied_request.get('icd_codes', []))}
Diagnosis: {denied_request.get('diagnosis', 'N/A')}
Treatment Plan: {denied_request.get('treatment_plan', 'N/A')}

Denial Reason:
{denial_reason}

Insurance Information:
{json.dumps(insurance_info, indent=2)}

Please provide a JSON response with the following structure:
{{
    "alternatives": [
        {{
            "treatment_name": "name of alternative treatment",
            "cpt_codes": ["alternative CPT codes"],
            "icd_codes": ["applicable ICD codes"],
            "description": "description of the alternative",
            "coverage_likelihood": "high/medium/low",
            "clinical_appropriateness": "high/medium/low",
            "effectiveness_comparison": "how it compares to original",
            "patient_considerations": "patient-specific considerations",
            "cost_implications": "cost comparison if known",
            "prior_auth_required": true/false,
            "recommendation_strength": "strong/moderate/weak"
        }}
    ],
    "primary_recommendation": {{
        "treatment": "recommended alternative",
        "rationale": "why this is recommended",
        "next_steps": ["steps to pursue this alternative"]
    }},
    "coverage_notes": "notes about insurance coverage patterns",
    "clinical_notes": "clinical considerations for alternatives"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "alternatives": result.get("alternatives", []),
                "primary_recommendation": result.get("primary_recommendation", {}),
                "coverage_notes": result.get("coverage_notes", ""),
                "clinical_notes": result.get("clinical_notes", "")
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "alternatives": [],
                "primary_recommendation": {}
            }
