"""Exercise the real gates in disposable Git repositories; no dependencies."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

MODULE = importlib.util.spec_from_file_location("factory_control", Path(__file__).with_name("control.py"))
control = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(control)


class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.factory = self.root / "factory"
        self.factory.mkdir()
        self.original_root = control.ROOT
        control.ROOT = self.factory
        self.addCleanup(setattr, control, "ROOT", self.original_root)
        self.git("init", "-b", "main")
        self.git("config", "user.email", "factory-test@example.invalid")
        self.git("config", "user.name", "Factory test")
        (self.root / "application.txt").write_text("initial\n")
        (self.factory / "backlog.md").write_text("# Backlog\n\n- [ ] First feature\n- [ ] Second feature\n")
        self.board = {"version": 1, "updated_at": None, "jobs": []}
        control.save_board(self.board)
        self.git("add", ".")
        self.git("commit", "-m", "initial")
        self.job_id = "001-first-feature"

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def run_event(self, command, **kwargs):
        args = argparse.Namespace(command=command, job=self.job_id, **kwargs)
        candidate = copy.deepcopy(self.board)
        control.transition(candidate, args)
        control.save_board(candidate)
        self.board = candidate
        return self.board["jobs"][0]

    @property
    def job(self):
        return self.board["jobs"][0]

    @property
    def folder(self):
        return self.factory / "jobs" / self.job_id

    def start(self, backlog=False):
        self.run_event("new", request="First feature", backlog_line=3 if backlog else None)
        (self.folder / "spec.md").write_text("# Spec\nAC1: application says implemented.\nCheck: read application.txt\n")
        self.run_event("spec")
        self.git("switch", "-c", "factory/" + self.job_id)
        self.run_event("agent", agent_id="builder-original", reason=None)
        self.build()

    def build(self):
        (self.root / "application.txt").write_text("implemented\n" + str(self.job["round"]))
        (self.folder / "build.md").write_text("AC1 verified by reading application.txt.\n")
        self.git("add", "application.txt", str(self.folder / "build.md"), str(self.folder / "spec.md"))
        self.git("commit", "-m", "implement")
        self.run_event("built")

    def review(self, name, verdict="PASS", commit=None):
        path = self.folder / f"round-{self.job['round']}" / f"review-{name}.md"
        path.write_text(f"VERDICT: {verdict}\nCOMMIT: {commit or self.job['commit']}\nInspected acceptance criterion AC1.\n")
        return path

    def reviews(self, verdict="PASS"):
        for name in control.REVIEWERS:
            self.review(name, verdict if name == "security" else "PASS")
        self.run_event("collect")

    def decision(self, verdict):
        (self.folder / "decision.md").write_text(f"{verdict}\nCOMMIT: {self.job['commit']}\nAcceptance evidence examined.\n")
        self.run_event("decide")

    def test_wait_for_all_then_correction_uses_original_builder(self):
        self.start()
        self.review("security", "CHANGES")
        self.review("ux")
        self.review("ui")
        self.run_event("collect")
        self.assertEqual(self.job["stage"], "review")
        self.assertEqual(self.job["reviews"]["code"], "pending")
        with self.assertRaisesRegex(ValueError, "Expected build"):
            self.run_event("built")
        self.review("code")
        self.run_event("collect")
        self.assertEqual(self.job["stage"], "build")
        self.build()
        self.assertEqual(self.job["round"], 2)
        self.assertEqual(self.job["builder_id"], "builder-original")
        self.assertEqual(self.job["rounds"][0]["reviews"]["security"], "CHANGES")

    def test_round_limit_and_manual_rework_preserve_history(self):
        self.start()
        self.reviews("CHANGES")
        self.build()
        self.reviews("CHANGES")
        self.assertEqual(self.job["stage"], "needs-human")
        with self.assertRaises(ValueError):
            self.run_event("built")
        old_commit = self.job["commit"]
        self.run_event("rework", note="Fix the remaining issue")
        self.build()
        self.assertEqual(self.job["round"], 3)
        self.assertEqual(self.job["cycle_start"], 3)
        self.assertEqual(self.job["rounds"][1]["commit"], old_commit)
        self.assertTrue((self.folder / "round-1/review-security.md").exists())
        self.assertEqual(len(self.job["feedback"]), 1)

    def test_invalid_and_wrong_commit_reviews_do_not_advance(self):
        self.start()
        for name in control.REVIEWERS:
            self.review(name)
        path = self.review("security", commit="0" * 40)
        with self.assertRaisesRegex(ValueError, "Wrong commit"):
            self.run_event("collect")
        path.write_text("VERDICT: PASS\n")
        with self.assertRaisesRegex(ValueError, "Invalid verdict"):
            self.run_event("collect")
        self.assertEqual(control.read_board()["jobs"][0]["stage"], "review")

    def test_changed_source_and_changed_spec_reject_reviews(self):
        self.start()
        self.review("security")
        (self.root / "application.txt").write_text("changed after review started")
        with self.assertRaisesRegex(ValueError, "Uncommitted application"):
            self.run_event("collect")
        self.git("restore", "application.txt")
        (self.folder / "spec.md").write_text("different acceptance criteria")
        with self.assertRaisesRegex(ValueError, "Spec changed"):
            self.run_event("collect")

    def test_factory_source_is_also_frozen(self):
        self.start()
        (self.factory / "dashboard.html").write_text("unreviewed UI")
        with self.assertRaisesRegex(ValueError, "Untracked application"):
            self.run_event("collect")

    def test_four_pass_requires_decision_and_real_merge(self):
        self.start()
        self.reviews()
        with self.assertRaisesRegex(ValueError, "Missing merge authorization"):
            self.run_event("merged")
        self.decision("APPROVE")
        with self.assertRaisesRegex(ValueError, "Finish on main"):
            self.run_event("merged")
        self.git("switch", "main")
        with self.assertRaises(ValueError):
            self.run_event("merged")
        self.git("merge", "--ff-only", "factory/" + self.job_id)
        self.run_event("merged")
        self.assertEqual(self.job["stage"], "done")

    def test_decision_rechecks_reports(self):
        self.start()
        self.reviews()
        self.review("security", "CHANGES")
        with self.assertRaisesRegex(ValueError, "still be PASS"):
            self.decision("APPROVE")

    def test_human_override_retains_failed_reviews(self):
        self.start()
        self.reviews("CHANGES")
        self.build()
        self.reviews("CHANGES")
        self.run_event("human-approve")
        self.git("switch", "main")
        self.git("merge", "--ff-only", "factory/" + self.job_id)
        self.run_event("merged")
        self.assertEqual(self.job["stage"], "done")
        self.assertEqual(self.job["reviews"]["security"], "CHANGES")
        self.assertIsNone(self.job["decision"])

    def test_escalation_and_archived_decision(self):
        self.start()
        self.reviews()
        self.decision("ESCALATE")
        self.assertEqual(self.job["reason"], "approver-escalated")
        self.run_event("rework", note="Resolve uncertainty")
        self.assertTrue(self.job["feedback"][0]["decision_text"].startswith("ESCALATE\n"))

    def test_backlog_reservation_and_single_job(self):
        with self.assertRaisesRegex(ValueError, "first unchecked"):
            self.run_event("new", request="Second feature", backlog_line=4)
        self.start(backlog=True)
        self.assertEqual(self.job["backlog"]["line"], 3)
        with self.assertRaisesRegex(ValueError, "Finish the existing"):
            control.transition(self.board, argparse.Namespace(command="new", job="002-next", request="Next", backlog_line=None))

    def test_backlog_mark_does_not_block_frozen_snapshot(self):
        self.start(backlog=True)
        path = self.factory / "backlog.md"
        path.write_text(path.read_text().replace("- [ ] First", "- [x] First"))
        self.reviews()
        self.assertEqual(self.job["stage"], "approve")

    def test_builder_recovery_requires_explanation(self):
        self.start()
        with self.assertRaisesRegex(ValueError, "Explain why"):
            self.run_event("agent", agent_id="replacement", reason=None)
        self.run_event("agent", agent_id="replacement", reason="Original session unavailable")
        self.assertEqual(len(self.job["builder_history"]), 2)

    def test_atomic_save_keeps_valid_json(self):
        self.start()
        self.assertEqual(json.loads((self.factory / "board.json").read_text()), self.board)
        self.assertEqual(list(self.factory.glob(".board-*")), [])

    def test_resume_new_after_folder_created_before_board_save(self):
        args = argparse.Namespace(command="new", job=self.job_id, request="First feature", backlog_line=None)
        control.transition(copy.deepcopy(self.board), args)
        self.assertTrue(self.folder.exists())
        self.run_event("new", request="First feature", backlog_line=None)
        self.assertEqual(self.job["stage"], "spec")

    def test_resume_built_after_folder_created_before_board_save(self):
        self.start()
        self.reviews("CHANGES")
        (self.root / "application.txt").write_text("fixed")
        self.git("add", "application.txt")
        self.git("commit", "-m", "fix")
        args = argparse.Namespace(command="built", job=self.job_id)
        control.transition(copy.deepcopy(self.board), args)
        self.assertTrue((self.folder / "round-2").exists())
        self.run_event("built")
        self.assertEqual(self.job["round"], 2)

    def test_orphaned_artifacts_are_never_overwritten(self):
        self.folder.mkdir(parents=True)
        (self.folder / "spec.md").write_text("existing evidence")
        with self.assertRaisesRegex(ValueError, "contains artifacts"):
            self.run_event("new", request="First feature", backlog_line=None)
        self.assertEqual((self.folder / "spec.md").read_text(), "existing evidence")


if __name__ == "__main__":
    unittest.main()
