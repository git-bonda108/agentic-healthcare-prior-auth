"""Document parsing utilities for medical documents."""
import os
from typing import Optional, Dict
import PyPDF2
from docx import Document
from pathlib import Path

class DocumentParser:
    """Parse various document formats to extract text."""
    
    @staticmethod
    def parse_file(file_path: str) -> Dict[str, any]:
        """Parse a file and extract text content."""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == ".pdf":
                text = DocumentParser._parse_pdf(file_path)
            elif file_ext in [".docx", ".doc"]:
                text = DocumentParser._parse_docx(file_path)
            elif file_ext == ".txt":
                text = DocumentParser._parse_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            return {
                "text": text,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": os.path.getsize(file_path),
                "success": True
            }
        except Exception as e:
            return {
                "text": "",
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "error": str(e),
                "success": False
            }
    
    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    
    @staticmethod
    def _parse_docx(file_path: str) -> str:
        """Extract text from DOCX file."""
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    
    @staticmethod
    def _parse_txt(file_path: str) -> str:
        """Extract text from TXT file."""
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read().strip()
