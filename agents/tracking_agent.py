"""Prior authorization tracking and appeals agent using OpenAI SDK."""
from openai import OpenAI
from typing import Dict, Optional
import json
from datetime import datetime
from utils.config import Config

class TrackingAgent:
    """Agent for tracking prior authorization status and managing appeals."""
    
    def __init__(self):
        """Initialize the tracking agent."""
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
    
    def analyze_response(self, prior_auth_id: int, response_text: str, original_request: Dict) -> Dict:
        """Analyze insurance response and determine status."""
        
        system_prompt = """You are a prior authorization response analyst. Your task is to:
1. Determine if the request was approved, denied, or requires additional information
2. Extract key information from the response
3. Identify denial reasons if applicable
4. Determine if an appeal is warranted
5. Suggest next steps

Return a structured analysis of the response."""
        
        user_prompt = f"""Analyze the following prior authorization response:

Original Request Summary:
{json.dumps(original_request.get('request_summary', {}), indent=2)}

Insurance Response:
{response_text}

Please provide a JSON response with the following structure:
{{
    "status": "approved/denied/pending/additional_info_required",
    "response_date": "date from response or current date",
    "approval_details": {{
        "approved_codes": ["list of approved CPT codes"],
        "approved_diagnoses": ["list of approved ICD codes"],
        "authorization_number": "authorization number if provided",
        "valid_until": "expiration date if provided",
        "limitations": "any limitations or restrictions"
    }},
    "denial_details": {{
        "denial_reason": "reason for denial",
        "denial_code": "denial code if provided",
        "denied_codes": ["list of denied CPT codes"],
        "appeal_deadline": "appeal deadline if provided",
        "appeal_eligible": true/false
    }},
    "additional_info_required": {{
        "required_documents": ["list of required documents"],
        "deadline": "deadline for submission",
        "contact_info": "contact information if provided"
    }},
    "next_steps": ["list of recommended next steps"],
    "appeal_recommendation": {{
        "should_appeal": true/false,
        "appeal_strength": "strong/moderate/weak",
        "appeal_strategy": "recommended appeal strategy"
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
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "analysis": result,
                "prior_auth_id": prior_auth_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis": {
                    "status": "unknown",
                    "response_date": datetime.now().isoformat()
                }
            }
    
    def prepare_appeal(self, prior_auth_id: int, denial_reason: str, original_request: Dict) -> Dict:
        """Prepare an appeal for a denied prior authorization."""
        
        system_prompt = """You are a prior authorization appeal specialist. Your task is to prepare compelling appeals that:
1. Address specific denial reasons
2. Provide additional clinical justification
3. Include supporting evidence
4. Follow payer-specific appeal requirements
5. Maximize appeal success chances"""
        
        user_prompt = f"""Prepare an appeal for the following denied prior authorization:

Original Request:
{json.dumps(original_request, indent=2)}

Denial Reason:
{denial_reason}

Please provide a JSON response with the following structure:
{{
    "appeal_summary": "brief summary of the appeal",
    "denial_address": {{
        "denial_reason": "the specific denial reason",
        "counter_argument": "why the denial should be overturned",
        "supporting_evidence": "evidence supporting the appeal"
    }},
    "additional_justification": {{
        "clinical_evidence": "additional clinical evidence",
        "peer_review": "peer-reviewed literature if applicable",
        "guidelines": "clinical guidelines supporting the request"
    }},
    "revised_request": {{
        "changes_made": "any changes to the original request",
        "additional_codes": ["any additional codes"],
        "clarifications": "clarifications provided"
    }},
    "appeal_strength": "strong/moderate/weak",
    "recommended_actions": ["list of recommended actions"],
    "appeal_ready": true/false
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
                "appeal": result,
                "prior_auth_id": prior_auth_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "appeal": {}
            }
