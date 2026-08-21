import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPOSITORY / "skills/reproducible-data-work/scripts/run_project.py"
PRESENTER_PATH = REPOSITORY / "skills/reproducible-data-work/scripts/present_project.py"
EXAMPLE = REPOSITORY / "examples/customer-reconciliation"

SPEC = importlib.util.spec_from_file_location("run_project", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)

PRESENTER_SPEC = importlib.util.spec_from_file_location("present_project", PRESENTER_PATH)
PRESENTER = importlib.util.module_from_spec(PRESENTER_SPEC)
PRESENTER_SPEC.loader.exec_module(PRESENTER)


class RunnerContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary_directory.name) / "project"
        shutil.copytree(EXAMPLE, self.project)
        for path in (self.project / "runs").glob("*.json"):
            path.unlink()
        for path in (self.project / "output").glob("*.csv"):
            path.unlink()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_repeated_runs_preserve_sources_and_reproduce_output(self):
        source_paths = sorted((self.project / "source").glob("*.csv"))
        before = {path.name: RUNNER.sha256(path) for path in source_paths}

        self.assertEqual(RUNNER.run(self.project), 0)
        first_output = RUNNER.sha256(self.project / "output/reconciled_customers.csv")
        self.assertEqual(RUNNER.run(self.project), 0)
        second_output = RUNNER.sha256(self.project / "output/reconciled_customers.csv")

        after = {path.name: RUNNER.sha256(path) for path in source_paths}
        self.assertEqual(before, after)
        self.assertEqual(first_output, second_output)
        self.assertTrue((self.project / "output/unmatched_transactions.csv").is_file())
        manifests = sorted((self.project / "runs").glob("*.json"))
        self.assertEqual(len(manifests), 2)
        manifest = json.loads(manifests[-1].read_text(encoding="utf-8"))
        self.assertTrue(manifest["source_immutability_verified"])
        self.assertTrue(all(check["status"] == "pass" for check in manifest["checks"]))

    def test_failed_reconciliation_returns_nonzero_and_is_recorded(self):
        transactions = self.project / "source/transactions.csv"
        transactions.write_text(
            transactions.read_text(encoding="utf-8") + "T005,C999,12.00\n",
            encoding="utf-8",
        )

        self.assertEqual(RUNNER.run(self.project), 2)
        manifest_path = next((self.project / "runs").glob("*.json"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        failed = [check for check in manifest["checks"] if check["status"] == "fail"]
        self.assertEqual([check["check_name"] for check in failed], ["unmatched_transaction_rows"])

    def test_rejects_source_outside_source_directory(self):
        config_path = self.project / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["sources"][0]["path"] = "work/001_normalize.sql"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "directly under source"):
            RUNNER.run(self.project)

    def test_presentation_prefers_excel_and_includes_results_and_exceptions(self):
        self.assertEqual(RUNNER.run(self.project), 0)
        applications = Path(self.temporary_directory.name) / "Applications"
        (applications / "Microsoft Excel.app").mkdir(parents=True)

        command = PRESENTER.present(
            self.project, dry_run=True, application_roots=(applications,)
        )

        self.assertEqual(command[:3], ["open", "-a", "Microsoft Excel"])
        self.assertEqual(
            [Path(value).name for value in command[3:]],
            ["reconciled_customers.csv", "unmatched_transactions.csv"],
        )

    def test_presentation_falls_back_to_html_report(self):
        self.assertEqual(RUNNER.run(self.project), 0)
        empty_applications = Path(self.temporary_directory.name) / "NoApplications"
        empty_applications.mkdir()

        command = PRESENTER.present(
            self.project, dry_run=True, application_roots=(empty_applications,)
        )

        report = self.project.resolve() / "output/review.html"
        self.assertEqual(command, ["open", str(report)])
        contents = report.read_text(encoding="utf-8")
        self.assertIn("Reconciliation checks", contents)
        self.assertIn("unmatched_transactions.csv", contents)


if __name__ == "__main__":
    unittest.main()
