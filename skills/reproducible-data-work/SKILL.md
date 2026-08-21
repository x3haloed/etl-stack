---
name: reproducible-data-work
description: Use when inspecting, cleaning, joining, reconciling, correcting, or exporting CSV and other structured data where the original inputs, transformation lineage, correctness checks, or repeatability matter.
compatibility: Requires Python 3 with its standard-library sqlite3 module for the bundled runner.
---

# Reproducible Data Work

Treat the output as disposable derived state. The durable evidence is the
immutable source material, explicit transformation code, and run manifest that
explains exactly how the output was produced.

## Establish the workspace

Use this layout for each data task:

```text
project/
  project.json       # source, output, and check declarations
  source/            # user-provided inputs; never edit in place
  work/              # ordered SQL transformations
  output/            # regenerated deliverables
  runs/               # immutable execution manifests
```

Copy source material into `source/` when necessary, then leave those bytes
untouched. Never "clean up" a source workbook or CSV in place. If the task
requires a corrected file, produce it under `output/`.

Infer the complete data-work outcome from a short request. "Merge these files"
does not mean merely execute a join: preserve the inputs, prevent accidental row
multiplication, reconcile coverage and control totals, expose unmatched or
invalid records, produce reviewable deliverables, and place those deliverables
in front of the user. Do not make the user enumerate these safeguards.

## Inspect before transforming

Profile the inputs and state the data grain, candidate keys, important nulls,
and join assumptions. Hashing proves that bytes did not change; it does not
prove that the interpretation is correct.

Prefer SQL for relational transformations. Put each meaningful mutation in a
numbered file such as `001_normalize.sql` or `002_reconcile.sql`. A step should
have one legible purpose and be independently inspectable. Use explicit casts,
join conditions, and column lists. Avoid transformations hidden in shell
history, notebook state, or one-off interactive edits.

The bundled SQLite runner loads declared CSV sources as text. Make type
conversion explicit in SQL so readers can see the interpretation applied to
source values.

## Make correctness executable

Create a final `checks` table with exactly these columns:

- `check_name`: stable, human-readable identifier
- `status`: `pass` or `fail`
- `observed`: value actually measured
- `expected`: criterion or comparison value

Checks should target the ways this specific task could be wrong: duplicate
business keys, unmatched joins, row multiplication, dropped records, invalid
values, and control totals. Do not substitute generic row counts for
domain-relevant reconciliation.

Material exceptions must also be a declared deliverable, not merely a count in
the manifest. Produce a reviewable exception output even when the user did not
explicitly request one. An empty exception output with headers is useful
evidence that the condition was checked.

Declare deliverable queries and the checks query in `project.json`. Keep output
queries deterministic by using an explicit `ORDER BY`.

## Run and review

Run:

```bash
python3 /path/to/this-skill/scripts/run_project.py /path/to/project
```

The runner snapshots source SHA-256 hashes, loads declared CSVs into a fresh
SQLite database, executes ordered SQL steps, exports outputs, evaluates checks,
rehashes sources and outputs, and writes a manifest. It exits unsuccessfully if
a source changes during execution or a check does not pass.

Review the manifest and report to the user:

- deliverables created and their hashes;
- each reconciliation check and its observed value;
- material assumptions or unresolved anomalies;
- confirmation that the source hashes remained unchanged.

Then make the work visible:

```bash
python3 /path/to/this-skill/scripts/present_project.py /path/to/project
```

Presentation is part of completion, not an optional convenience. The presenter
opens the declared results and exceptions in Microsoft Excel when available,
then Numbers, then LibreOffice. When none is installed, it builds an HTML review
report containing checks and output previews and opens that report in the
default browser. Do not claim the workflow is complete until the presentation
command succeeds and the review surface is open.

Re-run the same project and compare output hashes when reproducibility is
important. Matching hashes establish byte-level replay for those inputs,
steps, configuration, and engine version.

## Respect engine boundaries

Use another available engine when SQLite cannot express the work safely or
efficiently, but preserve the same contract: fresh derived state, ordered
readable transformations, source and output hashes, engine/version capture,
and executable reconciliation checks. Record deviations in the manifest rather
than silently weakening the audit trail.
