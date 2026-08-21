#!/usr/bin/env python3
"""Open data-project deliverables in a local review surface."""

import argparse
import csv
import html
import json
import subprocess
import sys
from pathlib import Path


SPREADSHEET_APPS = (
    ("Microsoft Excel", "Microsoft Excel.app"),
    ("Numbers", "Numbers.app"),
    ("LibreOffice", "LibreOffice.app"),
)


def find_spreadsheet_app(application_roots=None):
    roots = application_roots or (Path("/Applications"), Path.home() / "Applications")
    for display_name, bundle_name in SPREADSHEET_APPS:
        if any((root / bundle_name).is_dir() for root in roots):
            return display_name
    return None


def latest_manifest(project):
    manifests = sorted((project / "runs").glob("*.json"))
    if not manifests:
        raise ValueError("no run manifest found; execute run_project.py first")
    return manifests[-1], json.loads(manifests[-1].read_text(encoding="utf-8"))


def declared_outputs(project, config):
    presentation = config.get("presentation", {})
    paths = presentation.get("outputs") or [item["path"] for item in config["outputs"]]
    outputs = [project / path for path in paths]
    missing = [path for path in outputs if not path.is_file()]
    if missing:
        raise ValueError("declared presentation output does not exist: {}".format(missing[0]))
    return outputs


def csv_preview(path, limit=50):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    return rows[: limit + 1], max(0, len(rows) - 1)


def write_html_report(project, manifest_path, manifest, outputs):
    sections = []
    for output in outputs:
        rows, data_row_count = csv_preview(output)
        table_rows = []
        for index, row in enumerate(rows):
            cell = "th" if index == 0 else "td"
            table_rows.append("<tr>{}</tr>".format("".join(
                "<{0}>{1}</{0}>".format(cell, html.escape(value)) for value in row
            )))
        sections.append(
            "<section><h2>{}</h2><p>{} data rows; showing up to 50.</p><table>{}</table></section>".format(
                html.escape(str(output.relative_to(project))), data_row_count, "".join(table_rows)
            )
        )
    checks = "".join(
        "<tr class='{status}'><td>{check_name}</td><td>{status}</td><td>{observed}</td><td>{expected}</td></tr>".format(
            **{key: html.escape(str(value)) for key, value in check.items()}
        )
        for check in manifest["checks"]
    )
    document = """<!doctype html>
<html><head><meta charset="utf-8"><title>Data work review</title>
<style>body{{font:15px system-ui;margin:2rem;max-width:1200px}}table{{border-collapse:collapse;margin-bottom:2rem}}th,td{{border:1px solid #ccc;padding:.4rem;text-align:left}}.pass{{background:#e9f8ee}}.fail{{background:#fdecec}}</style>
</head><body><h1>Data work review</h1><p>Manifest: {}</p>
<h2>Reconciliation checks</h2><table><tr><th>Check</th><th>Status</th><th>Observed</th><th>Expected</th></tr>{}</table>
{}</body></html>
""".format(html.escape(str(manifest_path.relative_to(project))), checks, "".join(sections))
    report = project / "output/review.html"
    report.write_text(document, encoding="utf-8")
    return report


def present(project, dry_run=False, application_roots=None):
    project = project.resolve()
    config = json.loads((project / "project.json").read_text(encoding="utf-8"))
    manifest_path, manifest = latest_manifest(project)
    outputs = declared_outputs(project, config)
    app = find_spreadsheet_app(application_roots)
    if app:
        command = ["open", "-a", app] + [str(path) for path in outputs]
        target = app
    else:
        report = write_html_report(project, manifest_path, manifest, outputs)
        command = ["open", str(report)]
        target = str(report)
    if not dry_run:
        subprocess.run(command, check=True)
    print("review surface: {}".format(target))
    print("command: {}".format(" ".join(command)))
    return command


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        present(args.project, dry_run=args.dry_run)
        return 0
    except Exception as error:
        print("error: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
