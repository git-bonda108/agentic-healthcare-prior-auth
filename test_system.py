"""Test script to verify system components."""
import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")
    try:
        from utils.config import Config
        from core.document_parser import DocumentParser
        from core.database import PriorAuthDatabase
        from utils.validators import CodeValidator
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_document_parsing():
    """Test document parsing with sample file."""
    print("\nTesting document parsing...")
    try:
        from core.document_parser import DocumentParser
        parser = DocumentParser()
        sample_file = "sample_data/sample_medical_note_1.txt"
        
        if not os.path.exists(sample_file):
            print(f"⚠️  Sample file not found: {sample_file}")
            return False
        
        result = parser.parse_file(sample_file)
        if result["success"]:
            print(f"✅ Document parsed successfully ({len(result['text'])} characters)")
            return True
        else:
            print(f"❌ Parsing failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Parsing test error: {e}")
        return False

def test_code_extraction():
    """Test code extraction with sample text."""
    print("\nTesting code extraction...")
    try:
        from utils.validators import CodeValidator
        
        sample_text = """
        Patient requires cardiac catheterization (CPT: 93458) and coronary angiography (CPT: 93459).
        Diagnosis: Chest pain (ICD-10: R06.02) and coronary artery disease (ICD-10: I25.9).
        """
        
        validator = CodeValidator()
        cpt_codes = validator.extract_cpt_codes(sample_text)
        icd_codes = validator.extract_icd_codes(sample_text)
        
        print(f"✅ Extracted CPT codes: {cpt_codes}")
        print(f"✅ Extracted ICD codes: {icd_codes}")
        
        if cpt_codes and icd_codes:
            return True
        else:
            print("⚠️  No codes extracted")
            return False
    except Exception as e:
        print(f"❌ Code extraction test error: {e}")
        return False

def test_database():
    """Test database initialization."""
    print("\nTesting database...")
    try:
        from core.database import PriorAuthDatabase
        
        test_db_path = "./data/test_prior_auths.db"
        db = PriorAuthDatabase(test_db_path)
        print("✅ Database initialized successfully")
        
        # Clean up test database
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        return True
    except Exception as e:
        print(f"❌ Database test error: {e}")
        return False

def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    try:
        from utils.config import Config
        
        print(f"  Model: {Config.OPENAI_MODEL}")
        print(f"  Batch Size: {Config.DEFAULT_BATCH_SIZE}")
        print(f"  Database Path: {Config.DATABASE_PATH}")
        
        # Check if API key is set (don't validate, just check if env var exists)
        if Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != "your_openai_api_key_here":
            print("✅ OpenAI API key is configured")
            api_key_set = True
        else:
            print("⚠️  OpenAI API key not set (required for full functionality)")
            api_key_set = False
        
        return True, api_key_set
    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False, False

def main():
    """Run all tests."""
    print("=" * 50)
    print("SYSTEM TEST - Prior Authorization Automation")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Document Parsing", test_document_parsing()))
    results.append(("Code Extraction", test_code_extraction()))
    results.append(("Database", test_database()))
    config_ok, api_key_set = test_config()
    results.append(("Configuration", config_ok))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✅ All tests passed!")
        if not api_key_set:
            print("\n⚠️  NOTE: Add your OpenAI API key to .env file to enable AI features")
        print("\n🚀 System is ready! Run: python -m streamlit run app.py")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
