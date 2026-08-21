# Work Frontier

## Outcome

Equip AI agents with a system of principles and operating procedures for structured data workflows (inspect, clean, transform, reconcile, export) that guarantees complete reproducibility, auditability, and safety.

The agent enforces a strict architectural contract:
  immutable inputs + transformation code + execution manifest = reproducible derived state

The user experiences complete confidence: raw files are never touched, every mutation is an explicit numbered step, outputs have cryptographic provenance, and every run produces human-verifiable reconciliation checks and audit manifests.

## Goal invariants

- **Architectural Lineage (Source + Work + Manifest = Output):**
  - `source/`: Immutable raw inputs, cryptographically fingerprinted (SHA-256).
  - `work/`: Ordered, discrete, readable transformation steps (e.g. `001_import.sql`, `002_normalize.sql`, `003_reconcile.sql`).
  - `runs/`: Timestamped execution manifests recording input hashes, executed steps, parameters, engine version, output hashes, and data sanity/reconciliation checks.
  - `output/`: Clean derived state generated exclusively by running the steps against the inputs.
- **Source Immutability:** Raw inputs are strictly read-only and never modified in place.
- **Zero Black-Box Mutation:** Every transformation step must be an explicit, human-readable, independent script or query that can be inspected and re-run outside the agent.
- **First-Class Quality & Reconciliation Checks:** Every run must evaluate domain-specific data assertions (e.g., duplicate counts, unmatched join keys, balance totals, null rates) and capture them in the run manifest.
- **Environment & Engine Adaptability:** The agent selects and uses whatever appropriate engine is available on the machine (DuckDB, SQLite, Python, etc.) and explicitly logs the engine and parameters in the run manifest.
- **User Review Experience:** The agent presents concise, high-signal reconciliation summaries, diffs, and health metrics directly to the user so they can review outcomes without manual data digging.
- **Visible Completion:** A data task is not complete when files merely exist.
  The agent opens the primary results and exceptions in an available local
  spreadsheet application (Excel, Numbers, or LibreOffice), falling back to a
  generated HTML review report when no spreadsheet application is available.
- **Intent Completion:** Requests may name only the mechanical operation. The
  agent still infers and performs the correctness, exception-reporting,
  provenance, and visible-review work needed for a trustworthy result.
- **Fast Semantic Correction:** When a request leaves data semantics ambiguous,
  the agent chooses one reasonable interpretation, names consequential
  assumptions concisely, and presents the result immediately. The stack does
  not attempt to eliminate ambiguity through an expanding glossary or a bundle
  of speculative outputs.

## Evaluation regime

- **Epoch:** `epoch-1-visible-completion`
- **Active criterion:** Verification of end-to-end data lifecycle scenarios (inspect -> clean -> transform -> reconcile -> export) ensuring:
  1. Input immutability (SHA-256 unchanged).
  2. Complete step lineage in `work/`.
  3. Valid execution manifest in `runs/` with accurate hashes and sanity checks.
  4. Reproducibility: re-executing `work/` on `source/` produces bit-for-bit identical `output/`.
  5. Clear user-facing reconciliation and summary reporting.
  6. Results and exceptions are opened in an available spreadsheet application,
     with a browser-opened HTML report as the no-spreadsheet fallback.
- **Anchors:** Byte-identical source immutability, independent step re-executability, manifest schema validity, and reconciliation check accuracy.
- **Dependent evidence:** `tests/test_runner.py` exercises replay, source
  immutability, manifest recording, failed reconciliation, and source-path
  containment against `examples/customer-reconciliation/`.

## Prediction errors

<!-- None logged yet. -->
