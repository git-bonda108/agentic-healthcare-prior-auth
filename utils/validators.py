"""Validation utilities for prior authorization data."""
import re
from typing import List, Dict, Optional

class CodeValidator:
    """Validates CPT and ICD codes."""
    
    # CPT code pattern: 5 digits, sometimes with modifier (2 alphanumeric)
    CPT_PATTERN = re.compile(r'\b\d{5}[A-Z0-9]{0,2}\b')
    
    # ICD-10 pattern: Letter followed by digits, with possible decimal
    ICD10_PATTERN = re.compile(r'\b[A-Z]\d{2}(?:\.\d{1,2})?\b')
    
    @staticmethod
    def extract_cpt_codes(text: str) -> List[str]:
        """Extract CPT codes from text."""
        matches = CodeValidator.CPT_PATTERN.findall(text)
        return list(set(matches))  # Remove duplicates
    
    @staticmethod
    def extract_icd_codes(text: str) -> List[str]:
        """Extract ICD-10 codes from text."""
        matches = CodeValidator.ICD10_PATTERN.findall(text)
        return list(set(matches))  # Remove duplicates
    
    @staticmethod
    def validate_cpt_code(code: str) -> bool:
        """Validate CPT code format."""
        return bool(CodeValidator.CPT_PATTERN.match(code))
    
    @staticmethod
    def validate_icd_code(code: str) -> bool:
        """Validate ICD-10 code format."""
        return bool(CodeValidator.ICD10_PATTERN.match(code))
    
    @staticmethod
    def validate_extracted_codes(codes: Dict[str, List[str]]) -> Dict[str, any]:
        """Validate extracted codes and return validation results."""
        results = {
            "cpt_codes": [],
            "icd_codes": [],
            "valid": True,
            "errors": []
        }
        
        for code in codes.get("cpt_codes", []):
            if CodeValidator.validate_cpt_code(code):
                results["cpt_codes"].append(code)
            else:
                results["errors"].append(f"Invalid CPT code format: {code}")
                results["valid"] = False
        
        for code in codes.get("icd_codes", []):
            if CodeValidator.validate_icd_code(code):
                results["icd_codes"].append(code)
            else:
                results["errors"].append(f"Invalid ICD code format: {code}")
                results["valid"] = False
        
        return results
