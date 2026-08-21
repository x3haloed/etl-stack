# etl-stack

A toolkit for reproducible, auditable AI-assisted data transformation.

The stack teaches agents to treat structured-data outputs as derived artifacts:

```text
immutable source files + explicit SQL steps + execution manifest = reproducible output
```

## First runnable journey

Run the bundled customer-reconciliation example:

```bash
python3 skills/reproducible-data-work/scripts/run_project.py \
  examples/customer-reconciliation
python3 skills/reproducible-data-work/scripts/present_project.py \
  examples/customer-reconciliation
```

The runner verifies source immutability, executes every numbered SQL file in
order, exports deterministic CSV output, evaluates reconciliation checks, and
writes a timestamped JSON manifest under the example's `runs/` directory. The
presenter then opens both the reconciled result and its exceptions in Excel,
Numbers, or LibreOffice, with an HTML report as the fallback.

See [the core skill](skills/reproducible-data-work/SKILL.md) for the operating
procedure and review contract.
