# Evaluation

An honest account of what testing exists in this repository, what the code demonstrably handles, and what a real evaluation harness for this system should look like.

## What exists today

Two script-style test files at the repository root. Neither uses a test framework (no pytest/unittest), and there is no CI configuration in the repository.

### `test_system.py` — offline smoke test

Run: `python test_system.py`. No OpenAI API key required (it reports key presence but does not call the API).

Covers:
- **Imports** — all core modules load.
- **Document parsing** — `sample_data/sample_medical_note_1.txt` parses to non-empty text.
- **Regex code extraction** — a hard-coded snippet yields CPT `93458`, `93459` and ICD-10 `R06.02`, `I25.9` via `CodeValidator`.
- **Database** — SQLite schema initializes at a temp path, then the temp file is cleaned up.
- **Configuration** — settings load; warns (does not fail) when the API key is a placeholder.

Exits non-zero if any check fails.

### `test_agents.py` — live integration test

Run: `python test_agents.py`. Requires a valid `OPENAI_API_KEY`; makes real chat-completion calls and writes a record to the configured database.

Covers each of the five agent classes in dependency order (document analysis → code extraction → prior-auth preparation → tracking against a mock approval response → alternatives against a mock denial), then runs `BatchProcessor._process_single_file` end to end on a sample note.

Two caveats visible in the code:
- **It always exits 0.** `main()` returns `True` even when tests fail (it prints a warning and "launching anyway"), so this script cannot gate anything.
- **Success criteria are loose.** Checks assert that calls returned `success: True` and produced non-empty structures — not that the extracted codes match the known codes in the sample documents.

### Ground truth that exists but is unused

`sample_data/` contains seven synthetic doctor's notes, and `sample_data/README.md` documents the expected CPT and ICD-10 codes for each (e.g. `sample_medical_note_2.txt` → CPT `27447`, ICD-10 `M17.11`). No test compares extraction output against these expectations — this is a ready-made golden dataset that is currently only used manually.

## Edge cases the code visibly handles

Enumerated from the source, not from intent:

| Edge case | Where | Behavior |
|---|---|---|
| Unsupported file extension | `core/document_parser.py` | Caught, returned as `{success: False, error}` |
| Parse failure (corrupt PDF/DOCX, encoding) | `core/document_parser.py` | Same error-dict pattern; file is skipped with reason |
| LLM call failure in any agent | all `agents/*.py` | try/except returns `success: False` with the error string |
| LLM failure during code extraction | `agents/code_extraction_agent.py` | Degrades to regex-only extraction instead of failing the file |
| Malformed/duplicate codes | `agents/code_extraction_agent.py` + `utils/validators.py` | Union of AI+regex codes is de-duplicated and format-validated |
| One file failing mid-batch | `core/batch_processor.py` | Failure counted, remaining files continue; batch-level try/except marks batch `error` |
| Missing API key | `utils/config.py` + `app.py` | `Config.validate()` raises; UI shows a configuration error and stops |
| Unknown prior-auth ID | `core/batch_processor.py`, `app.py` | "Prior auth not found" result/message |
| Appeal on a non-denied record | `core/batch_processor.py` | Refused with an explanatory error |
| No files uploaded | `app.py` | Guard with error message |

## Edge cases *not* handled (declared but unwired, or absent)

- **No retries and no timeouts** around OpenAI calls. `Config.MAX_RETRIES` and `Config.TIMEOUT_SECONDS` exist but are referenced nowhere; a hung or rate-limited call surfaces as a single failure.
- **No file-size enforcement** in application code; `Config.MAX_FILE_SIZE_MB` is unused (Streamlit's own upload limit is the only bound).
- **No output-schema validation.** Pydantic is in `requirements.txt` but unused; agent JSON is consumed with `.get()` chains, so a missing key degrades to `"N/A"` silently rather than being flagged.
- **No accuracy checks** on extraction — a format-valid but wrong code passes every layer.

## Proposed: an evaluation harness this system should have

Nothing below exists yet; this is the design a production effort should implement first.

**Golden dataset.** Start from the seven `sample_data/` notes and their documented codes; grow to 50–100 de-identified or synthetic notes stratified by specialty, note length, and code density (including notes with *no* explicit codes, where inference is required, and adversarial notes containing 5-digit non-codes like ZIP codes and dates). Store per-note expectations as JSON: `{file, expected_cpt: [], expected_icd: [], patient_name, provider_name, primary_diagnosis}`.

**Metrics.**
- Code extraction: precision, recall, and F1 for CPT and ICD-10 separately (the union-with-regex design should be measured for its false-positive cost).
- Field extraction: exact-match rate for patient name, provider name, NPI.
- Response classification (`TrackingAgent`): accuracy on a labeled set of approval/denial/info-request letters, including denial-reason extraction match.
- Request drafting: completeness checked *programmatically* against a required-field list, replacing the model's self-reported `ready_for_submission`.
- Operational: per-document latency and token cost per pipeline stage.

**Gates.** Run as pytest so exit codes are meaningful (unlike `test_agents.py` today). Regression gate in CI on every change to prompts, model choice (`OPENAI_MODEL`), or extraction logic: fail if CPT F1 or ICD F1 drops more than an agreed delta from the recorded baseline, or if any golden note that previously extracted its primary code stops doing so. Because model outputs vary, run each note 3 times and gate on the median.

**Determinism handling.** Pin the model version in CI, keep temperatures at their current low values, and record raw model outputs as artifacts so failures are diagnosable.

**Unit layer.** The pure-Python pieces deserve conventional unit tests independent of any LLM: `CodeValidator` regexes (both false negatives and the known 5-digit false-positive class), `DocumentParser` per format, and `PriorAuthDatabase` CRUD including the JSON-column round-trip.
