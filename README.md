# Agentic AI for Prior Authorization Automation

## Overview
An autonomous AI agent system that automates the entire prior authorization workflow for healthcare providers, reducing manual work and improving accuracy.

## Features
- **Document Processing**: Reads doctor's notes, medical reports, and clinical documentation
- **Code Extraction**: Automatically extracts CPT and ICD-10 codes from medical documents
- **Prior Auth Preparation**: Prepares complete prior authorization requests
- **Submission Tracking**: Tracks submissions, responses, and appeals
- **Alternative Suggestions**: Suggests covered alternative treatments if denied
- **Batch Processing**: Processes multiple requests in batches with user confirmation
- **Streamlit UI**: User-friendly web interface with file upload capability

## Architecture
- **Agentic OpenAI SDK**: Uses OpenAI's agentic framework for autonomous decision-making
- **Multi-Agent System**: Specialized agents for each workflow step
- **Batch Processing**: Distributed workload with confirmation checkpoints
- **High Accuracy**: Multiple validation layers and error handling

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up the project:
```bash
python setup.py
```

3. Configure environment variables:
   - Edit `.env` file and add your `OPENAI_API_KEY`
   - Optionally adjust `BATCH_SIZE` and other settings

4. Run the application:
```bash
python -m streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## Usage

### Basic Workflow

1. **Upload Documents**
   - Navigate to "Upload & Process" page
   - Upload medical documents (PDF, DOCX, TXT)
   - Multiple files can be uploaded for batch processing

2. **Configure Batch Processing**
   - Set batch size in sidebar (default: 5)
   - Click "Process Files" to start

3. **Review and Confirm**
   - Review results after each batch
   - Confirm before proceeding to next batch
   - System pauses for your confirmation

4. **Track Status**
   - View all prior authorizations in "View Prior Auths"
   - Filter by status (pending, approved, denied)
   - Search by patient name or file name

5. **Process Responses**
   - Use "Track Status" page to update with insurance responses
   - System automatically analyzes responses
   - Denials trigger alternative treatment suggestions

6. **Appeals & Alternatives**
   - View alternative treatments for denied requests
   - Generate appeal documents
   - Review coverage likelihood and clinical appropriateness

### Features

- **Automatic Code Extraction**: CPT and ICD-10 codes extracted from documents
- **AI-Powered Analysis**: Advanced document understanding using GPT-4
- **Batch Processing**: Process multiple files efficiently with confirmation checkpoints
- **Response Tracking**: Automatically analyze insurance responses
- **Alternative Suggestions**: Get covered treatment alternatives for denials
- **Appeal Generation**: Automatically prepare appeal documents

## Project Structure
```
├── app.py                 # Streamlit frontend
├── agents/                # Agentic AI agents
│   ├── document_agent.py
│   ├── code_extraction_agent.py
│   ├── prior_auth_agent.py
│   ├── tracking_agent.py
│   └── alternative_agent.py
├── core/                  # Core functionality
│   ├── batch_processor.py
│   ├── document_parser.py
│   └── database.py
├── utils/                 # Utilities
│   ├── config.py
│   └── validators.py
└── data/                  # Data storage
    └── prior_auths.db
```
