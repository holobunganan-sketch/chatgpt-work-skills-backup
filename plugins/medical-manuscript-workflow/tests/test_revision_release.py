import copy
import json
import unittest
from pathlib import Path

from scripts.validate_revision_release import release_issues


ROOT = Path(__file__).resolve().parents[1]


class RevisionReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = json.loads(
            (ROOT / "assets/reviewer-ledger.example.json").read_text(encoding="utf-8")
        )

    def issue_codes(self, ledger: dict) -> set[str]:
        return {issue["code"] for issue in release_issues(ledger)}

    def test_verified_approved_comment_is_release_ready(self) -> None:
        self.assertEqual([], release_issues(self.ledger))

    def test_pending_and_deferred_decisions_block_release(self) -> None:
        for state in ("pending", "deferred"):
            ledger = copy.deepcopy(self.ledger)
            ledger["reviewers"][0]["comments"][0]["decision"]["state"] = state
            self.assertIn("nonterminal_decision", self.issue_codes(ledger))

    def test_unresolved_conditional_approval_blocks_release(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        decision = ledger["reviewers"][0]["comments"][0]["decision"]
        decision.update(
            {
                "state": "conditional_approved",
                "conditions": ["Confirm the endpoint against the protocol"],
                "conditions_met": False,
            }
        )
        self.assertIn("unresolved_conditions", self.issue_codes(ledger))

    def test_approved_change_requires_verified_implementation_evidence(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        implementation = ledger["reviewers"][0]["comments"][0]["implementation"]
        implementation["status"] = "implemented"
        implementation["evidence"] = []
        codes = self.issue_codes(ledger)
        self.assertIn("implementation_not_verified", codes)
        self.assertIn("missing_implementation_evidence", codes)

    def test_response_and_location_are_required(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        comment = ledger["reviewers"][0]["comments"][0]
        comment["response"] = "  "
        comment["location"] = {"status": "pending", "entries": []}
        codes = self.issue_codes(ledger)
        self.assertIn("missing_response", codes)
        self.assertIn("location_not_verified", codes)

    def test_rejected_comment_can_close_without_manuscript_change(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        comment = ledger["reviewers"][0]["comments"][0]
        comment["decision"].update(
            {
                "state": "rejected",
                "conditions": [],
                "conditions_met": True,
                "rationale": "The requested analysis is outside the prespecified plan.",
            }
        )
        comment["implementation"] = {"status": "not_applicable", "evidence": []}
        comment["response"] = "We respectfully explain why the requested analysis was not added."
        comment["location"] = {"status": "not_applicable", "entries": []}
        comment["status"] = "closed"
        self.assertEqual([], release_issues(ledger))


if __name__ == "__main__":
    unittest.main()
