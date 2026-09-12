# Architecture

## Component map

| Component | File | Responsibility |
|---|---|---|
| Streamlit UI | `app.py` | Four pages: Upload & Process, View Prior Auths, Track Status, Appeals & Alternatives. Owns session state and drives batching. |
| Batch orchestrator | `core/batch_processor.py` | Instantiates all five agents, runs the per-file pipeline, records batch progress, routes denial follow-ups. |
| Document parser | `core/document_parser.py` | PDF (PyPDF2), DOCX (python-docx), TXT text extraction. Returns `{success, text, error}` dicts, never raises to callers. |
| DocumentAgent | `agents/document_agent.py` | One chat-completion call: raw document text → structured JSON (patient, provider, clinical_info, treatment, insurance). |
| CodeExtractionAgent | `agents/code_extraction_agent.py` | One chat-completion call for CPT/ICD-10 extraction, merged with regex extraction, then format-validated. |
| PriorAuthAgent | `agents/prior_auth_agent.py` | One chat-completion call: prior-step JSON → complete prior-auth request JSON, plus a plain-text `format_for_submission` renderer. |
| TrackingAgent | `agents/tracking_agent.py` | Two entry points, one chat-completion call each: `analyze_response` (payer text → status/denial analysis) and `prepare_appeal`. |
| AlternativeTreatmentAgent | `agents/alternative_agent.py` | One chat-completion call: denied request + denial reason → ranked alternative treatments with coverage-likelihood labels. |
| Persistence | `core/database.py` | SQLite via the standard library; tables `prior_auths` and `batches`; connection opened and closed per operation. |
| Config | `utils/config.py` | `.env`-backed settings; `Config.validate()` hard-fails when `OPENAI_API_KEY` is absent. |
| Validators | `utils/validators.py` | Regex patterns for CPT (`\d{5}` + optional 2-char modifier) and ICD-10 (`[A-Z]\d{2}(\.\d{1,2})?`); extraction and format checks. |

Despite the "agent" naming, each agent class is a thin wrapper over a single synchronous `client.chat.completions.create` call with `response_format={"type": "json_object"}` and a fixed system + user prompt pair. There is no tool use, no function calling, no multi-turn reasoning loop, and no agent-to-agent communication. All coordination lives in ordinary Python control flow in `BatchProcessor` and `app.py`.

## Data flow, end to end

Ingestion (`BatchProcessor._process_single_file`):

1. Streamlit saves each upload to a `tempfile.mkdtemp()` directory (`app.py:process_uploaded_files`).
2. `DocumentParser.parse_file` extracts text; failure short-circuits the file with an error result.
3. `DocumentAgent.analyze_document` produces structured JSON from the full document text (temperature 0.1); failure short-circuits.
4. `CodeExtractionAgent.extract_codes` receives the clinical-info JSON plus the first 2,000 characters of document text. AI-extracted codes are unioned with regex-extracted codes from the full text, then filtered through format validation. This step never short-circuits — on LLM failure it degrades to regex-only results.
5. `PriorAuthAgent.prepare_prior_auth_request` assembles the draft request (temperature 0.2) and self-reports a `completeness_check`.
6. The record is written to `prior_auths` with status `prepared`. The complete intermediate state (document analysis, code extraction, prior-auth request) is serialized into the `notes` column as one JSON blob.

Response processing (`BatchProcessor.process_response`):

7. The user pastes a payer response on the Track Status page. `TrackingAgent.analyze_response` classifies it (approved / denied / pending / additional_info_required) using the stored request summary as context.
8. On `denied`, the denial reason and appeal eligibility are persisted, and `AlternativeTreatmentAgent.suggest_alternatives` is invoked immediately; its output is stored in `alternative_treatments`.
9. Appeals are on-demand: `BatchProcessor.prepare_appeal` re-reads the stored request JSON from `notes` and calls `TrackingAgent.prepare_appeal`. Appeals are only permitted for records whose status is `denied`.

## Orchestration analysis: sequential by construction

- **Everything is sequential and synchronous.** Files within a batch run one at a time in a `for` loop; batches run one after another in `app.py`. Each pipeline step blocks on one OpenAI HTTP call. Nothing is parallel, and there is no async code anywhere in the repository.
- **Why this shape fits:** the pipeline has hard data dependencies (codes need clinical info; the request needs codes), volumes are interactive-scale (batches of 1–20), and Streamlit's rerun model favors simple synchronous flows. The obvious future optimization — processing the files of a batch concurrently, since files are independent — is not implemented.
- **The denial branch is the only conditional routing.** `process_response` fans into alternatives only when the tracking analysis returns `denied`; appeal preparation is a separate user-triggered path. This is an if-statement, not a planner decision, which makes the system's behavior fully predictable and auditable — an intentional trade-off away from autonomy.
- **Batch "confirmation" is display-only.** `BatchProcessor.process_batch` accepts a `confirmation_callback` that can stop the run, but the callback wired up in `app.py` always returns `True`; the UI shows per-batch results and continues automatically. The stop mechanism exists in the orchestrator but no UI control exercises it.

## State and context engineering

- **Session state:** Streamlit `session_state` holds the database handle, processor, uploaded files, and processing status. It is per-browser-session and lost on restart.
- **Durable state:** SQLite. `prior_auths` is the system of record (identifiers, codes as JSON strings, status lifecycle `pending → prepared → submitted → approved/denied`, denial reason, appeal status, alternatives). `batches` records batch progress. Connections are short-lived (open/execute/commit/close per call), which keeps the code simple at the cost of throughput — acceptable for a single-user local app.
- **Context assembly is explicit and bounded.** Each prompt embeds exactly the JSON produced by earlier steps; nothing accumulates across files or sessions, so context length is bounded by one document plus its derived JSON. Two deliberate bounds are visible in code: the code-extraction prompt truncates raw document text to 2,000 characters (relying on the structured clinical-info JSON plus full-text regex for the remainder), and every LLM call demands `json_object` output so downstream code can parse deterministically.
- **The `notes` column is the memory between phases.** Ingestion-time analysis is replayed to the tracking and appeal steps by deserializing this blob, so response analysis works even in a fresh session — persistence, not conversation history, is the memory mechanism.

## Design decisions and trade-offs visible in the code

1. **Dual extraction (LLM + regex) with validation as arbiter.** `CodeExtractionAgent` unions both sources and keeps only format-valid codes; on LLM failure it silently degrades to regex-only. This buys availability and recall at a precision cost: the CPT regex `\b\d{5}[A-Z0-9]{0,2}\b` matches any 5-digit number in the document (dates, IDs, ZIP codes), and format validation cannot reject a well-formed but clinically wrong code.
2. **Errors as return values, not exceptions.** Every agent and the parser return `{success: bool, error: str, ...}` dicts. The orchestrator decides which failures are fatal per file (parsing, document analysis, request preparation) and which degrade (code extraction). One file's failure never aborts the batch; failures are counted and displayed.
3. **Low temperature, structured output.** 0.1 for extraction/analysis steps, 0.2–0.3 for generative steps (request drafting, alternatives), all with JSON mode. Consistency is preferred over creativity everywhere accuracy matters.
4. **Self-reported completeness instead of programmatic validation.** The prior-auth draft's `completeness_check.ready_for_submission` comes from the model's own JSON, not from code that checks required fields. It is surfaced in the UI but nothing gates on it.
5. **SQLite with JSON columns rather than a normalized schema.** Codes and alternatives are stored as JSON strings inside text columns. Right-sized for a prototype; querying by code or reporting across records would require schema work (see HARDENING).
6. **Config constants ahead of implementation.** `MAX_RETRIES`, `TIMEOUT_SECONDS`, `MAX_FILE_SIZE_MB`, and `ALLOWED_EXTENSIONS` are declared in `utils/config.py` but not referenced by processing code; there is no retry or timeout handling around OpenAI calls, and upload constraints are enforced only by the hard-coded `type=` list in `app.py` and Streamlit's own upload limits.

## Known UI limitation

On the Appeals & Alternatives page, the "Prepare Appeal" button is rendered inside the click handler of "Load Prior Auth" (`app.py:appeals_page`). Because Streamlit re-runs the script on every interaction and the outer button's state does not persist, the nested button's action is unreachable in practice. Appeal preparation logic itself (`BatchProcessor.prepare_appeal`) is functional and covered by the live test path.
