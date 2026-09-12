# Hardening

Current security posture of this codebase, an honest PHI/compliance assessment, and a staged ladder to production. This is a prototype; the gaps below are expected for that stage and are listed so they can be closed deliberately.

## Current posture

**Authentication and authorization.** None. The Streamlit app has no login, no roles, and no per-user data separation; anyone who can reach port 8501 can upload documents, read every stored record, and process responses. The dev container additionally launches Streamlit with `--server.enableCORS false --server.enableXsrfProtection false`, which is acceptable only behind Codespaces' own authentication.

**Secrets handling.** Good for a prototype: the OpenAI key is read from the environment / `.env` (`utils/config.py`), `.env` is gitignored, `setup.py` writes only a placeholder, and no credentials exist in the repository at HEAD. The app fails fast when the key is missing.

**Error handling.** Consistent error-as-value pattern (`{success, error}`) keeps single failures from crashing batches, but raw exception strings — which can include upstream API details — are rendered directly in the UI, and there are no retries or timeouts around network calls despite `MAX_RETRIES`/`TIMEOUT_SECONDS` being declared in config.

**Data at rest.** Uploads are written to a world-default `tempfile.mkdtemp()` directory and never deleted by the app. Extracted patient names, provider names, codes, denial reasons, and the full document-analysis JSON are stored unencrypted in a local SQLite file (`./data/prior_auths.db`, gitignored). There is no deletion or retention mechanism in the application.

**Injection surfaces.** SQL values are parameterized throughout. One caveat: `PriorAuthDatabase.update_prior_auth` interpolates dictionary *keys* into the `SET` clause; keys currently come only from internal call sites, but the method itself does not whitelist columns. Document content is untrusted input that flows into LLM prompts (prompt-injection surface: a document could attempt to steer the drafting model) and LLM/database output is rendered via Streamlit widgets; the only `unsafe_allow_html=True` usages render fixed CSS and a status string derived from a controlled status set.

**Observability.** None. No logging module usage, no audit trail of who processed what, no metrics. `print` statements exist only in the test scripts.

## PHI and compliance posture — what the code does and does not do

This system is designed around medical documents, so it must be assessed as if inputs were Protected Health Information, even though the bundled `sample_data/` is entirely synthetic (fictional patients).

What the code does today:
- **Sends full document text to OpenAI's API** (`DocumentAgent`, and excerpts plus derived clinical JSON in the other four agents). If real PHI were uploaded, PHI would leave the machine to a third-party processor. Nothing in the code establishes or checks for a Business Associate Agreement, a HIPAA-eligible endpoint, or zero-retention API terms.
- **Persists PHI-shaped fields in plaintext** (patient name, provider, diagnosis text, full analysis JSON) in local SQLite, and leaves uploaded files in a temp directory indefinitely.
- **Has no access control, no audit logging, no encryption at rest or key management, no de-identification, no retention/deletion workflow, and no consent tracking.** None of the HIPAA Security Rule technical safeguards (access control, audit controls, integrity, transmission security beyond TLS to the API) are implemented in application code.
- **Makes no minimum-necessary reduction**: the entire note is sent, not the minimal fields needed per step.

Plain conclusion: **this codebase is not HIPAA-ready and must not be used with real patient data in its current form.** It is suitable for demonstrations with synthetic data only. The clinical outputs (codes, medical-necessity language, alternative treatments) are model-generated and unvalidated; in any real deployment they would require review by qualified coding/clinical staff before submission — the current UI presents them as drafts but enforces no review step.

## Staged ladder to production

### Stage 1 — Identity, keys, and data boundaries
- Put the app behind authentication (reverse proxy with SSO/OIDC, or Streamlit's supported auth patterns); add role separation (uploader vs. reviewer) if more than one persona exists. Re-enable XSRF protection outside Codespaces.
- Move the OpenAI key to a secret manager; scope one key per environment; add rotation.
- Contract a HIPAA-eligible LLM endpoint under a BAA with zero data retention before any real document is processed; alternatively add a de-identification pass (e.g., redact names/DOB/IDs) before text leaves the process, re-associating identifiers locally.
- Delete uploaded temp files after processing; encrypt the database (or move to a managed Postgres with encryption at rest); whitelist columns in `update_prior_auth`.

### Stage 2 — Reliability and observability
- Wire the already-declared `MAX_RETRIES`/`TIMEOUT_SECONDS` into the OpenAI client (the SDK supports `timeout` and `max_retries` natively); add backoff for rate limits.
- Validate every agent's JSON against Pydantic schemas (already a dependency) and fail closed on malformed output instead of `.get()` defaults.
- Structured logging with an audit trail: who uploaded, what was processed, which model/version, token counts, and every status transition. Exclude PHI from logs.
- Metrics and alerting: per-stage latency, failure rates, cost per document. Implement the evaluation gates from [EVALUATION.md](EVALUATION.md) in CI before changing prompts or models.

### Stage 3 — Deployment
- Containerize the app (the dev container is a starting point, minus its security-disabling flags); run behind TLS; pin dependency versions (`requirements.txt` currently uses open-ended `>=` ranges) and add vulnerability scanning.
- Replace SQLite with a server database for concurrency and backups; add migrations.
- Add a human-review gate in the workflow: a request cannot reach `submitted` status without a reviewer action, replacing the model's self-reported `ready_for_submission`.

### Stage 4 — Compliance
- HIPAA Security Rule risk analysis; document administrative/technical safeguards; BAAs with every processor in the data path (LLM provider, hosting, backups).
- Retention and deletion policy implemented in code (purge documents and derived records on schedule or request).
- Access reviews and audit-log retention; incident-response runbook covering model-output errors (wrong codes submitted) as well as data exposure.
- Validation study of coding accuracy against certified-coder ground truth before any payer-facing use; ongoing monitoring for model drift after `OPENAI_MODEL` changes.

## Secrets removed from HEAD — rotate these credentials and purge history

None. No credentials, key files, or populated `.env` files were present at HEAD; `.gitignore` already excludes `.env`, databases, and local data.
