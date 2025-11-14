# System Architecture

## Overview

The Prior Authorization Automation system uses an agentic AI architecture with specialized agents for each workflow step, ensuring high accuracy and autonomous decision-making.

## Architecture Components

### 1. Frontend Layer (Streamlit)
- **File Upload Interface**: Handles multiple file formats (PDF, DOCX, TXT)
- **Batch Processing UI**: Visual progress tracking and confirmation
- **Status Dashboard**: Real-time tracking of prior authorizations
- **Response Processing**: Interface for insurance response input

### 2. Agentic AI Layer

#### Document Agent (`document_agent.py`)
- **Purpose**: Analyze medical documents and extract structured information
- **Capabilities**:
  - Patient information extraction
  - Provider information extraction
  - Clinical history and findings
  - Treatment plans
  - Insurance information
- **Model**: GPT-4o with JSON response format
- **Temperature**: 0.1 (high accuracy)

#### Code Extraction Agent (`code_extraction_agent.py`)
- **Purpose**: Extract and validate CPT and ICD-10 codes
- **Capabilities**:
  - AI-powered code extraction
  - Regex-based fallback extraction
  - Code validation
  - Code descriptions
  - Confidence scoring
- **Dual Approach**: Combines AI extraction with regex validation

#### Prior Auth Agent (`prior_auth_agent.py`)
- **Purpose**: Prepare comprehensive prior authorization requests
- **Capabilities**:
  - Clinical justification
  - Medical necessity documentation
  - Complete request formatting
  - Submission readiness check
- **Output**: Structured JSON + formatted text document

#### Tracking Agent (`tracking_agent.py`)
- **Purpose**: Analyze insurance responses and manage appeals
- **Capabilities**:
  - Response status determination
  - Denial reason extraction
  - Appeal eligibility assessment
  - Appeal document preparation
- **Intelligence**: Determines next steps automatically

#### Alternative Treatment Agent (`alternative_agent.py`)
- **Purpose**: Suggest covered alternative treatments
- **Capabilities**:
  - Alternative treatment identification
  - Coverage likelihood assessment
  - Clinical appropriateness evaluation
  - Cost comparison
- **Output**: Ranked alternatives with recommendations

### 3. Core Processing Layer

#### Batch Processor (`batch_processor.py`)
- **Functionality**:
  - Distributes workload across batches
  - Manages processing pipeline
  - Handles errors gracefully
  - Tracks progress
- **Features**:
  - Configurable batch size
  - User confirmation checkpoints
  - Error recovery
  - Progress tracking

#### Document Parser (`document_parser.py`)
- **Supported Formats**: PDF, DOCX, TXT
- **Functionality**:
  - Text extraction
  - Format detection
  - Error handling
  - File validation

#### Database (`database.py`)
- **Storage**: SQLite database
- **Tables**:
  - `prior_auths`: Complete prior authorization records
  - `batches`: Batch processing tracking
- **Features**:
  - Full CRUD operations
  - Status tracking
  - JSON storage for complex data

### 4. Utility Layer

#### Configuration (`config.py`)
- **Purpose**: Centralized configuration management
- **Features**:
  - Environment variable loading
  - Validation
  - Default values
  - API key management

#### Validators (`validators.py`)
- **Purpose**: Code validation and extraction
- **Features**:
  - CPT code validation (5 digits + optional modifier)
  - ICD-10 validation (Letter + digits)
  - Regex-based extraction
  - Format validation

## Data Flow

```
1. File Upload
   ↓
2. Document Parsing (PDF/DOCX/TXT → Text)
   ↓
3. Document Agent (Text → Structured Data)
   ↓
4. Code Extraction Agent (Text + Clinical Data → CPT/ICD Codes)
   ↓
5. Prior Auth Agent (All Data → Prior Auth Request)
   ↓
6. Database Storage (Request → SQLite)
   ↓
7. [Optional] Response Processing
   ↓
8. Tracking Agent (Response → Status Update)
   ↓
9. [If Denied] Alternative Agent (Denial → Alternatives)
   ↓
10. [If Denied] Appeal Preparation
```

## Batch Processing Flow

```
1. User uploads N files
   ↓
2. Files divided into batches (size: configurable)
   ↓
3. For each batch:
   a. Process all files in batch
   b. Display results
   c. Wait for user review (optional)
   d. Continue to next batch
   ↓
4. Final summary and completion
```

## Error Handling

- **Document Parsing Errors**: Graceful fallback, error reporting
- **API Errors**: Retry logic, error messages
- **Code Extraction Errors**: Regex fallback
- **Database Errors**: Transaction rollback, error logging
- **Batch Processing Errors**: Continue with remaining files

## Security Considerations

- API keys stored in environment variables
- No sensitive data in logs
- File upload size limits
- Input validation on all user inputs
- SQL injection prevention (parameterized queries)

## Scalability

- **Batch Processing**: Distributes load
- **Database**: SQLite (can be upgraded to PostgreSQL)
- **Caching**: Session state for performance
- **Async Ready**: Architecture supports async operations

## Accuracy Measures

1. **Dual Extraction**: AI + Regex for codes
2. **Validation**: All codes validated before use
3. **Low Temperature**: 0.1-0.3 for consistency
4. **Structured Output**: JSON format for reliability
5. **Error Recovery**: Multiple fallback mechanisms
6. **User Review**: Confirmation checkpoints

## Future Enhancements

- Integration with insurance APIs
- Real-time submission
- Multi-language support
- Advanced analytics dashboard
- Machine learning for code prediction
- Integration with EMR systems
