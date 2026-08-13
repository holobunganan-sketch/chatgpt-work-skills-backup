import copy
import json
import unittest
from pathlib import Path

from scripts.validate_reviewer_coverage import coverage_issues


ROOT = Path(__file__).resolve().parents[1]


class ReviewerCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = json.loads(
            (ROOT / "assets/reviewer-ledger.example.json").read_text(encoding="utf-8")
        )

    def test_valid_contiguous_span(self) -> None:
        self.assertEqual([], coverage_issues(self.ledger))

    def test_overlapping_context_spans_are_allowed(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        reviewer = ledger["reviewers"][0]
        second = copy.deepcopy(reviewer["comments"][0])
        second["comment_id"] = "R1-C2"
        second["order"] = 2
        second["source_span"] = {"start": 7, "end": 28}
        second["verbatim_comment"] = reviewer["source_text"][7:28]
        reviewer["comments"].append(second)
        self.assertEqual([], coverage_issues(ledger))

    def test_non_action_segment_can_complete_coverage(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        reviewer = ledger["reviewers"][0]
        reviewer["comments"][0]["source_span"] = {"start": 7, "end": 28}
        reviewer["comments"][0]["verbatim_comment"] = reviewer["source_text"][7:28]
        reviewer["non_action_segments"] = [
            {
                "segment_id": "R1-N1",
                "source_span": {"start": 0, "end": 7},
                "verbatim_text": reviewer["source_text"][0:7],
                "reason": "Introductory wording",
            }
        ]
        self.assertEqual([], coverage_issues(ledger))

    def test_uncovered_characters_are_reported(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["reviewers"][0]["comments"][0]["source_span"] = {"start": 1, "end": 28}
        ledger["reviewers"][0]["comments"][0]["verbatim_comment"] = "lease clarify the endpoint."
        issues = coverage_issues(ledger)
        self.assertTrue(any(issue["code"] == "uncovered_source" for issue in issues))
        self.assertEqual({"start": 0, "end": 1}, next(i["span"] for i in issues if i["code"] == "uncovered_source"))

    def test_out_of_range_and_reversed_spans_are_reported(self) -> None:
        for span in ({"start": 0, "end": 99}, {"start": 10, "end": 10}):
            ledger = copy.deepcopy(self.ledger)
            ledger["reviewers"][0]["comments"][0]["source_span"] = span
            issues = coverage_issues(ledger)
            self.assertTrue(any(issue["code"] == "invalid_span" for issue in issues))

    def test_mismatched_verbatim_excerpt_is_reported(self) -> None:
        ledger = copy.deepcopy(self.ledger)
        ledger["reviewers"][0]["comments"][0]["verbatim_comment"] = "Edited reviewer text"
        issues = coverage_issues(ledger)
        self.assertTrue(any(issue["code"] == "verbatim_mismatch" for issue in issues))


if __name__ == "__main__":
    unittest.main()
