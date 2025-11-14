"""Setup script for Prior Authorization Automation."""
import os
from pathlib import Path

def setup_project():
    """Set up the project directories and files."""
    # Create data directory
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write("""OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
BATCH_SIZE=5
DATABASE_PATH=./data/prior_auths.db
""")
        print("✅ Created .env file. Please add your OPENAI_API_KEY.")
    else:
        print("✅ .env file already exists.")
    
    print("✅ Project setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file and add your OPENAI_API_KEY")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the app: python -m streamlit run app.py")

if __name__ == "__main__":
    setup_project()
