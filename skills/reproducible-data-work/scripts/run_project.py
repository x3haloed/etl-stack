#!/usr/bin/env python3
"""Run a SQL-first data project and emit a provenance manifest."""

import csv
import datetime as dt
import hashlib
import json
import sqlite3
import sys
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def relative_hashes(root, paths):
    return {str(path.relative_to(root)): sha256(path) for path in paths}


def quote_identifier(value):
    return '"' + value.replace('"', '""') + '"'


def load_csv(connection, path, table):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        try:
            columns = next(reader)
        except StopIteration:
            raise ValueError("source CSV is empty: {}".format(path))
        if not columns or any(not column for column in columns):
            raise ValueError("source CSV has blank column names: {}".format(path))
        if len(columns) != len(set(columns)):
            raise ValueError("source CSV has duplicate column names: {}".format(path))
        column_sql = ", ".join(quote_identifier(column) + " TEXT" for column in columns)
        connection.execute("CREATE TABLE {} ({})".format(quote_identifier(table), column_sql))
        placeholders = ", ".join("?" for _ in columns)
        insert_sql = "INSERT INTO {} VALUES ({})".format(quote_identifier(table), placeholders)
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(columns):
                raise ValueError(
                    "source CSV row {} has {} fields; expected {}: {}".format(
                        row_number, len(row), len(columns), path
                    )
                )
            connection.execute(insert_sql, row)


def export_query(connection, query, path):
    cursor = connection.execute(query)
    columns = [description[0] for description in cursor.description]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(cursor)


def load_config(project):
    config_path = project / "project.json"
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    for key in ("sources", "outputs", "checks_query"):
        if key not in config:
            raise ValueError("project.json is missing required key: {}".format(key))
    return config, config_path


def run(project):
    project = project.resolve()
    config, config_path = load_config(project)
    source_paths = [project / item["path"] for item in config["sources"]]
    for path in source_paths:
        if not path.is_file() or path.parent != project / "source":
            raise ValueError("declared source must be a file directly under source/: {}".format(path))

    steps = sorted((project / "work").glob("[0-9][0-9][0-9]_*.sql"))
    if not steps:
        raise ValueError("no numbered SQL steps found under work/")

    before = relative_hashes(project, source_paths)
    step_hashes = relative_hashes(project, steps)
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        for item, path in zip(config["sources"], source_paths):
            load_csv(connection, path, item["table"])
        for step in steps:
            connection.executescript(step.read_text(encoding="utf-8"))

        output_paths = []
        for item in config["outputs"]:
            output_path = project / item["path"]
            if output_path.parent != project / "output":
                raise ValueError("declared output must be directly under output/: {}".format(output_path))
            export_query(connection, item["query"], output_path)
            output_paths.append(output_path)

        checks = [dict(row) for row in connection.execute(config["checks_query"])]
    finally:
        connection.close()

    required_check_columns = {"check_name", "status", "observed", "expected"}
    for check in checks:
        if set(check) != required_check_columns:
            raise ValueError("checks query must return exactly: {}".format(sorted(required_check_columns)))

    after = relative_hashes(project, source_paths)
    if before != after:
        raise RuntimeError("source files changed during execution")

    now = dt.datetime.now(dt.timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%S.%fZ")
    manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "started_at_utc": now.isoformat().replace("+00:00", "Z"),
        "project_config": {
            "path": str(config_path.relative_to(project)),
            "sha256": sha256(config_path),
        },
        "engine": {"name": "sqlite", "version": sqlite3.sqlite_version},
        "inputs": before,
        "steps": [
            {"path": str(step.relative_to(project)), "sha256": step_hashes[str(step.relative_to(project))]}
            for step in steps
        ],
        "outputs": relative_hashes(project, output_paths),
        "checks": checks,
        "source_immutability_verified": True,
    }
    runs = project / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    manifest_path = runs / (run_id + ".json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("manifest: {}".format(manifest_path))
    for path, digest in manifest["outputs"].items():
        print("output: {} {}".format(path, digest))
    for check in checks:
        print("check: {status} {check_name} observed={observed} expected={expected}".format(**check))

    return 0 if checks and all(check["status"] == "pass" for check in checks) else 2


def main():
    if len(sys.argv) != 2:
        print("usage: run_project.py PROJECT_DIRECTORY", file=sys.stderr)
        return 64
    try:
        return run(Path(sys.argv[1]))
    except Exception as error:
        print("error: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
