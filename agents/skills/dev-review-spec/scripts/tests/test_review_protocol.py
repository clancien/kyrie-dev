#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Readiness and loop regressions, using isolated specification fixtures."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "review_protocol.py"
spec = importlib.util.spec_from_file_location("review_protocol", SCRIPT)
protocol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(protocol)


class ReviewProtocolTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.doc = self.root / "SPEC.md"
        self.doc.write_text("CAP-1: preserve success; rejection unspecified", encoding="utf-8")
        self.companion = self.root / "acceptance.md"
        self.companion.write_text("Success Given/When/Then", encoding="utf-8")
        self.original = self.root / "SPEC.review.md"
        self.original.write_text("Legacy review: R1 rejection missing", encoding="utf-8")
        self.counter = 0

    def result(self, severity=None):
        value = {"status": "complete", "coverage": "full", "required_lenses": ["adversarial"], "executed_lenses": ["adversarial"], "checks": dict.fromkeys(protocol.CHECKS, True), "pending_decisions": [], "failures": [], "findings": []}
        if severity:
            value["findings"].append({"id": "R1", "severity": severity, "section": "CAP-1", "finding": "Rejection unspecified", "correction": "Define rejection", "evidence": "CAP-1 only specifies success", "consequence": "Incompatible responses", "lenses": ["adversarial"]})
        return value

    def review(self, result=None, latest=None):
        self.counter += 1
        result = self.result() if result is None else result
        source = self.root / f"snapshot-{self.counter}.json"
        incoming = self.root / f"result-{self.counter}.json"
        output = self.root / f"round-{self.counter}.review.md"
        protocol.write(source, protocol.snapshot(self.doc, [self.companion]))
        protocol.write(incoming, result)
        protocol.make_report(incoming, source, output, latest)
        return output.with_suffix(".json")

    def run_path(self, limit=3):
        return Path(protocol.init_run(self.doc, self.original, limit)["run"])

    def record(self, run, review, keys=None, dispositions=None, **extra):
        reconcile = self.root / "reconcile.json"
        protocol.write(reconcile, {"keys": keys or {}, "dispositions": dispositions or {}, **extra})
        return protocol.record(run, review, reconcile)

    def resolved(self):
        return {"D1": {"state": "resolved", "reason": "Rejected branch defined", "evidence": "CAP-1 rejection Given/When/Then and preservation reviewed"}}

    def baseline(self, limit=3):
        run = self.run_path(limit)
        review = self.review(self.result("major"))
        self.record(run, review, {"R1": "CAP-1:missing-rejection"})
        return run

    def test_clean_spec_ready_without_repair(self):
        run = self.run_path()
        state = self.record(run, self.review())
        self.assertEqual((state["status"], state["rounds_used"]), ("ready", 0))

    def test_minor_only_ready_with_observations(self):
        report = protocol.load_review(self.review(self.result("minor")))
        self.assertTrue(report["ready_for_dev"])
        self.assertEqual(report["verdict"], "LISTO CON OBSERVACIONES")

    def test_major_and_blocker_prevent_readiness(self):
        for severity in ("major", "blocker"):
            report = protocol.load_review(self.review(self.result(severity)))
            self.assertFalse(report["ready_for_dev"])
            self.assertEqual(report["verdict"], "NO LISTO")

    def test_false_check_and_decisions_prevent_readiness(self):
        for check in protocol.CHECKS:
            result = self.result()
            result["checks"][check] = False
            self.assertFalse(protocol.load_review(self.review(result))["ready_for_dev"])
        result = self.result()
        result["pending_decisions"] = ["Choose rejection response"]
        self.assertEqual(self.record(self.run_path(), self.review(result))["status"], "needs_user")

    def test_incomplete_has_no_verdict_and_does_not_publish_latest(self):
        latest = self.original
        self.review(latest=latest)
        before = latest.read_bytes()
        result = self.result()
        result.update(status="incomplete", executed_lenses=[], failures=["Lens timed out"])
        report = protocol.load_review(self.review(result, latest))
        self.assertIsNone(report["verdict"])
        self.assertFalse(report["ready_for_dev"])
        self.assertEqual(latest.read_bytes(), before)

    def test_complete_missing_lens_rejected(self):
        result = self.result()
        result["executed_lenses"] = []
        with self.assertRaises(ValueError):
            self.review(result)

    def test_companion_change_invalidates_snapshot(self):
        report = self.review()
        self.companion.write_text("Changed rejection requirement", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Stale snapshot"):
            protocol.load_review(report)

    def test_missing_companion_and_duplicate_inventory_fail(self):
        with self.assertRaises(OSError):
            protocol.snapshot(self.doc, [self.root / "missing.md"])
        with self.assertRaises(ValueError):
            protocol.snapshot(self.doc, [self.doc])

    def test_ready_metadata_cannot_be_forged(self):
        report = self.review(self.result("major"))
        value = protocol.read(report)
        value["ready_for_dev"] = True
        protocol.write(report, value)
        with self.assertRaisesRegex(ValueError, "metadata mismatch"):
            protocol.load_review(report)

    def test_historical_report_immutable(self):
        report = self.review()
        with self.assertRaisesRegex(ValueError, "immutable"):
            protocol.adopt(report, report.with_suffix(".md"))

    def test_output_json_collision_rejected_before_writes(self):
        report = self.review()
        output = self.root / "bad.json"
        with self.assertRaisesRegex(ValueError, "end in .md"):
            protocol.adopt(report, output)
        self.assertFalse(output.exists())
        source = self.root / "snap.json"
        result = self.root / "input.json"
        protocol.write(source, protocol.snapshot(self.doc))
        protocol.write(result, self.result())
        with self.assertRaises(ValueError):
            protocol.make_report(result, source, self.root / "new.md", output)
        self.assertFalse((self.root / "new.md").exists())

    def test_output_cannot_overwrite_contract(self):
        source = self.root / "snap.json"
        result = self.root / "input.json"
        protocol.write(source, protocol.snapshot(self.doc))
        protocol.write(result, self.result())
        with self.assertRaises(ValueError):
            protocol.make_report(result, source, self.doc)
        self.assertIn("CAP-1", self.doc.read_text())

    def test_changed_contract_without_consumed_attempt_rejected(self):
        run = self.baseline()
        self.doc.write_text("CAP-1: success and rejection defined", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "consumed repair attempt"):
            self.record(run, self.review(), dispositions=self.resolved())
        self.assertEqual(protocol.read(run)["rounds_used"], 0)

    def test_repair_then_independent_resolution_ready(self):
        run = self.baseline()
        protocol.begin(run)
        self.doc.write_text("CAP-1: success preserved; rejection response defined", encoding="utf-8")
        state = self.record(run, self.review(), dispositions=self.resolved())
        self.assertEqual((state["status"], state["rounds_used"]), ("ready", 1))
        self.assertEqual(state["defects"][0]["id"], "D1")
        self.assertIn(str(self.doc), state["reviews"][-1]["changed_files"])

    def test_disappearance_does_not_close_defect(self):
        run = self.baseline()
        state = self.record(run, self.review())
        self.assertEqual(state["defects"][0]["state"], "open")
        self.assertNotEqual(state["status"], "ready")

    def test_applied_and_major_deferral_do_not_pass(self):
        run = self.baseline()
        applied = {"D1": {"state": "applied", "reason": "Editor changed wording", "evidence": "Change exists but not verified"}}
        self.assertNotEqual(self.record(run, self.review(), dispositions=applied)["status"], "ready")
        applied["D1"]["state"] = "deferred"
        with self.assertRaisesRegex(ValueError, "cannot be deferred"):
            self.record(run, self.review(), dispositions=applied)

    def test_budget_consumed_before_repair_and_not_reset(self):
        run = self.baseline(limit=1)
        protocol.begin(run)
        self.assertEqual(protocol.read(run)["rounds_used"], 1)
        state = self.record(run, self.review(self.result("major")), {"R1": "CAP-1:missing-rejection"})
        self.assertEqual(state["status"], "budget_exhausted")
        with self.assertRaises(ValueError):
            protocol.begin(run)
        self.assertEqual(protocol.read(run)["max_rounds"], 1)

    def test_repeated_r1_different_cause_gets_new_d(self):
        run = self.baseline()
        state = self.record(run, self.review(self.result("major")), {"R1": "CAP-1:another-defect"})
        self.assertEqual([d["id"] for d in state["defects"]], ["D1", "D2"])

    def test_overlapping_observations_share_defect_preserve_both(self):
        result = self.result("major")
        second = dict(result["findings"][0], id="R2", finding="Same missing branch observed separately")
        result["findings"].append(second)
        state = self.record(self.run_path(), self.review(result), {"R1": "cause", "R2": "cause"})
        self.assertEqual(len(state["defects"]), 1)
        self.assertEqual(len(state["defects"][0]["observations"]), 2)

    def test_rejected_requires_new_evidence_to_reopen(self):
        run = self.baseline()
        rejected = {"D1": {"state": "rejected", "reason": "Covered elsewhere", "evidence": "Companion covers this branch"}}
        self.record(run, self.review(self.result("major")), {"R1": "CAP-1:missing-rejection"}, rejected)
        state = self.record(run, self.review(self.result("major")), {"R1": "CAP-1:missing-rejection"})
        self.assertEqual(state["defects"][0]["state"], "rejected")
        state = self.record(run, self.review(self.result("major")), {"R1": "CAP-1:missing-rejection"}, reopen_rejected={"D1": {"reason": "Different branch now required", "evidence": "New authorized constraint excludes previous handling"}})
        self.assertEqual(state["defects"][0]["state"], "open")

    def test_latest_alias_not_valid_for_ledger(self):
        latest = self.original
        self.review(latest=latest)
        with self.assertRaisesRegex(ValueError, "historical report"):
            self.record(self.run_path(), latest.with_suffix(".json"))

    def test_external_refresh_requires_stop_and_evidence(self):
        run = self.baseline()
        self.doc.write_text("External requirement update", encoding="utf-8")
        report = self.review(self.result("major"))
        reconcile = self.root / "refresh.json"
        protocol.write(reconcile, {"keys": {"R1": "CAP-1:missing-rejection"}})
        with self.assertRaisesRegex(ValueError, "Stop stale run"):
            protocol.record(run, report, reconcile, "External user edit")
        protocol.stop(run, "incomplete_review", "External edit detected")
        state = protocol.record(run, report, reconcile, "External user edit with new requirement")
        self.assertEqual(state["rounds_used"], 0)
        self.assertEqual(state["events"][-1]["event"], "external_refresh")

    def test_cli_emits_json_and_failure_exit(self):
        complete = subprocess.run([sys.executable, str(SCRIPT), "snapshot", str(self.doc), "-o", str(self.root / "cli.json")], capture_output=True, text=True)
        self.assertEqual(complete.returncode, 0)
        self.assertEqual(json.loads(complete.stdout)["document"], str(self.doc))
        failure = subprocess.run([sys.executable, str(SCRIPT), "verify", str(self.root / "missing.json")], capture_output=True, text=True)
        self.assertEqual(failure.returncode, 1)
        self.assertIn("error", json.loads(failure.stdout))

    def test_latest_cannot_overwrite_historical_round(self):
        historical = self.review()
        before = historical.with_suffix(".md").read_bytes()
        with self.assertRaisesRegex(ValueError, "canonical review neighbor"):
            self.review(latest=historical.with_suffix(".md"))
        self.assertEqual(historical.with_suffix(".md").read_bytes(), before)

    def test_legacy_input_archived_before_latest_replaced(self):
        original = self.original.read_bytes()
        run = self.run_path()
        self.review(latest=self.original)
        self.assertEqual((run.parent / "input.review.md").read_bytes(), original)
        self.assertNotEqual(self.original.read_bytes(), original)

    def test_stale_review_blocks_begin_and_consumes_no_budget(self):
        run = self.baseline()
        self.companion.write_text("External update", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Stale snapshot"):
            protocol.begin(run)
        self.assertEqual(protocol.read(run)["rounds_used"], 0)


if __name__ == "__main__":
    unittest.main()
