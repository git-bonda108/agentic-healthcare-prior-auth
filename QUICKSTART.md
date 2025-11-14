# Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- OpenAI API key (get one at https://platform.openai.com/api-keys)

## Installation (5 minutes)

1. **Navigate to project directory:**
   ```bash
   cd "/Users/macbook/Documents/AGENTIC HEALTHCARE "
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up project:**
   ```bash
   python setup.py
   ```

4. **Configure API key:**
   - Open `.env` file
   - Replace `your_openai_api_key_here` with your actual OpenAI API key
   - Save the file

5. **Run the application:**
   ```bash
   python -m streamlit run app.py
   ```

The app will open automatically in your browser at `http://localhost:8501`

## First Use (10 minutes)

1. **Upload a test document:**
   - Go to "Upload & Process" page
   - Click "Choose files"
   - Upload a medical document (PDF, DOCX, or TXT)
   - See TESTING.md for sample document format

2. **Process the document:**
   - Set batch size (default: 5)
   - Click "🚀 Process Files"
   - Wait for processing to complete

3. **Review results:**
   - Expand the batch results
   - Check extracted CPT and ICD codes
   - Review the generated prior authorization request

4. **View in database:**
   - Go to "View Prior Auths" page
   - See your processed prior authorization
   - Filter by status or search

## Key Features to Try

### Batch Processing
- Upload multiple files at once
- System processes them in batches
- Review results after each batch
- Confirm before proceeding

### Response Tracking
- Go to "Track Status" page
- Enter a Prior Auth ID
- Paste an insurance response
- System analyzes and updates status

### Alternative Treatments
- For denied requests, go to "Appeals & Alternatives"
- View suggested alternative treatments
- See coverage likelihood and clinical appropriateness

## Troubleshooting

**"OPENAI_API_KEY is required" error:**
- Make sure `.env` file exists and has your API key
- Check that the key is correct (starts with `sk-`)

**No codes extracted:**
- Check document format
- Ensure codes are in standard format
- See TESTING.md for sample document

**File upload fails:**
- Check file size (max 50MB)
- Ensure file format is supported (PDF, DOCX, TXT)
- Try a different file

## Next Steps

- Read the full README.md for detailed documentation
- Check TESTING.md for sample documents and test cases
- Customize batch size and other settings in `.env`
- Integrate with your existing systems using the database API
