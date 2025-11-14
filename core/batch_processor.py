"""Batch processing system for prior authorization requests."""
from typing import List, Dict, Callable, Optional
from datetime import datetime
import json
from core.database import PriorAuthDatabase
from agents.document_agent import DocumentAgent
from agents.code_extraction_agent import CodeExtractionAgent
from agents.prior_auth_agent import PriorAuthAgent
from agents.tracking_agent import TrackingAgent
from agents.alternative_agent import AlternativeTreatmentAgent
from core.document_parser import DocumentParser

class BatchProcessor:
    """Process prior authorization requests in batches."""
    
    def __init__(self, db: PriorAuthDatabase, batch_size: int = 5):
        """Initialize batch processor."""
        self.db = db
        self.batch_size = batch_size
        self.document_agent = DocumentAgent()
        self.code_agent = CodeExtractionAgent()
        self.prior_auth_agent = PriorAuthAgent()
        self.tracking_agent = TrackingAgent()
        self.alternative_agent = AlternativeTreatmentAgent()
        self.parser = DocumentParser()
    
    def process_batch(self, files: List[Dict], batch_number: int, 
                     confirmation_callback: Optional[Callable] = None) -> Dict:
        """Process a batch of files."""
        
        batch_results = {
            "batch_number": batch_number,
            "total_files": len(files),
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
            "status": "processing"
        }
        
        # Create batch record
        batch_id = self.db.create_batch(batch_number, len(files))
        
        try:
            for idx, file_info in enumerate(files):
                file_result = self._process_single_file(file_info)
                batch_results["results"].append(file_result)
                
                if file_result["success"]:
                    batch_results["successful"] += 1
                else:
                    batch_results["failed"] += 1
                
                batch_results["processed"] += 1
                
                # Update batch progress
                self.db.update_batch(batch_id, batch_results["processed"], "processing")
                
                # Call confirmation callback if provided
                if confirmation_callback:
                    should_continue = confirmation_callback(batch_results, file_result, idx + 1)
                    if not should_continue:
                        batch_results["status"] = "stopped_by_user"
                        break
            
            batch_results["status"] = "completed"
            self.db.update_batch(batch_id, batch_results["processed"], "completed")
            
        except Exception as e:
            batch_results["status"] = "error"
            batch_results["error"] = str(e)
            self.db.update_batch(batch_id, batch_results["processed"], "error")
        
        return batch_results
    
    def _process_single_file(self, file_info: Dict) -> Dict:
        """Process a single file through the entire workflow."""
        result = {
            "file_name": file_info.get("file_name", "unknown"),
            "file_path": file_info.get("file_path", ""),
            "success": False,
            "steps": {},
            "prior_auth_id": None
        }
        
        try:
            # Step 1: Parse document
            parsed = self.parser.parse_file(file_info["file_path"])
            if not parsed["success"]:
                result["error"] = f"Document parsing failed: {parsed.get('error')}"
                return result
            
            result["steps"]["parsing"] = "success"
            
            # Step 2: Analyze document with AI
            doc_analysis = self.document_agent.analyze_document(
                parsed["text"], 
                file_info["file_name"]
            )
            if not doc_analysis["success"]:
                result["error"] = f"Document analysis failed: {doc_analysis.get('error')}"
                return result
            
            result["steps"]["document_analysis"] = "success"
            doc_data = doc_analysis["data"]
            
            # Step 3: Extract codes
            code_extraction = self.code_agent.extract_codes(
                parsed["text"],
                doc_data.get("clinical_info", {})
            )
            result["steps"]["code_extraction"] = "success" if code_extraction.get("cpt_codes") or code_extraction.get("icd_codes") else "partial"
            
            # Step 4: Prepare prior auth request
            prior_auth_prep = self.prior_auth_agent.prepare_prior_auth_request(
                doc_data,
                {
                    "cpt_codes": code_extraction.get("cpt_codes", []),
                    "icd_codes": code_extraction.get("icd_codes", [])
                },
                doc_data.get("patient", {})
            )
            
            if not prior_auth_prep["success"]:
                result["error"] = f"Prior auth preparation failed: {prior_auth_prep.get('error')}"
                return result
            
            result["steps"]["prior_auth_preparation"] = "success"
            
            # Step 5: Save to database
            prior_auth_data = {
                "file_name": file_info["file_name"],
                "file_path": file_info["file_path"],
                "patient_name": doc_data.get("patient", {}).get("name"),
                "provider_name": doc_data.get("provider", {}).get("name"),
                "cpt_codes": code_extraction.get("cpt_codes", []),
                "icd_codes": code_extraction.get("icd_codes", []),
                "status": "prepared",
                "notes": json.dumps({
                    "document_analysis": doc_data,
                    "code_extraction": code_extraction,
                    "prior_auth_request": prior_auth_prep.get("prior_auth_request", {})
                })
            }
            
            prior_auth_id = self.db.create_prior_auth(prior_auth_data)
            result["prior_auth_id"] = prior_auth_id
            result["steps"]["database_save"] = "success"
            
            # Compile final result
            result["success"] = True
            result["data"] = {
                "document_analysis": doc_data,
                "codes": {
                    "cpt_codes": code_extraction.get("cpt_codes", []),
                    "icd_codes": code_extraction.get("icd_codes", [])
                },
                "prior_auth_request": prior_auth_prep.get("prior_auth_request", {}),
                "formatted_request": self.prior_auth_agent.format_for_submission(prior_auth_prep)
            }
            
        except Exception as e:
            result["error"] = str(e)
            result["success"] = False
        
        return result
    
    def process_response(self, prior_auth_id: int, response_text: str) -> Dict:
        """Process an insurance response for a prior authorization."""
        prior_auth = self.db.get_prior_auth(prior_auth_id)
        if not prior_auth:
            return {"success": False, "error": "Prior auth not found"}
        
        # Parse stored notes
        notes = json.loads(prior_auth.get("notes", "{}"))
        original_request = notes.get("prior_auth_request", {})
        
        # Analyze response
        analysis = self.tracking_agent.analyze_response(
            prior_auth_id,
            response_text,
            original_request
        )
        
        if analysis["success"]:
            # Update database
            update_data = {
                "status": analysis["analysis"].get("status", "unknown"),
                "response_date": analysis["analysis"].get("response_date"),
                "response_status": analysis["analysis"].get("status")
            }
            
            if analysis["analysis"].get("status") == "denied":
                update_data["denial_reason"] = analysis["analysis"].get("denial_details", {}).get("denial_reason", "")
                update_data["appeal_status"] = "eligible" if analysis["analysis"].get("denial_details", {}).get("appeal_eligible") else "not_eligible"
                
                # Get alternative treatments
                alternatives = self.alternative_agent.suggest_alternatives(
                    {
                        "cpt_codes": json.loads(prior_auth.get("cpt_codes", "[]")),
                        "icd_codes": json.loads(prior_auth.get("icd_codes", "[]")),
                        "diagnosis": original_request.get("clinical_justification", {}).get("diagnosis", ""),
                        "treatment_plan": original_request.get("treatment", {})
                    },
                    update_data["denial_reason"],
                    {}
                )
                
                if alternatives["success"]:
                    update_data["alternative_treatments"] = alternatives.get("alternatives", [])
            
            self.db.update_prior_auth(prior_auth_id, update_data)
        
        return analysis
    
    def prepare_appeal(self, prior_auth_id: int) -> Dict:
        """Prepare an appeal for a denied prior authorization."""
        prior_auth = self.db.get_prior_auth(prior_auth_id)
        if not prior_auth:
            return {"success": False, "error": "Prior auth not found"}
        
        if prior_auth.get("status") != "denied":
            return {"success": False, "error": "Prior auth is not denied"}
        
        notes = json.loads(prior_auth.get("notes", "{}"))
        original_request = notes.get("prior_auth_request", {})
        denial_reason = prior_auth.get("denial_reason", "")
        
        appeal = self.tracking_agent.prepare_appeal(
            prior_auth_id,
            denial_reason,
            original_request
        )
        
        return appeal
