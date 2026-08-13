import copy
import json
import tempfile
import unittest
from pathlib import Path

from docx import Document

from scripts.build_reviewer_responses import build_responses


ROOT = Path(__file__).resolve().parents[1]


class ReviewerResponseBuilderTests(unittest.TestCase):
    def ledger_with_two_reviewers(self) -> dict:
        ledger = json.loads(
            (ROOT / "assets/reviewer-ledger.example.json").read_text(encoding="utf-8")
        )
        reviewer_one = ledger["reviewers"][0]
        second_comment = copy.deepcopy(reviewer_one["comments"][0])
        second_comment["comment_id"] = "R1-C2"
        second_comment["order"] = 2
        second_comment["response"] = "We added a second clarification and removed the redundant sentence as described here."
        reviewer_one["comments"].append(second_comment)

        reviewer_two = copy.deepcopy(reviewer_one)
        reviewer_two["reviewer_id"] = "R2"
        reviewer_two["sequence"] = 2
        reviewer_two["source_name"] = "Reviewer 2"
        reviewer_two["comments"] = [copy.deepcopy(reviewer_two["comments"][0])]
        reviewer_two["comments"][0]["comment_id"] = "R2-C1"
        reviewer_two["comments"][0]["order"] = 1
        ledger["reviewers"].append(reviewer_two)
        return ledger

    def test_one_docx_per_reviewer_with_repeated_heading_sequence(self) -> None:
        ledger = self.ledger_with_two_reviewers()
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            paths = build_responses(ledger, output_dir)
            self.assertEqual(
                ["Response_to_Reviewer_1.docx", "Response_to_Reviewer_2.docx"],
                [path.name for path in paths],
            )
            for reviewer_index, path in enumerate(paths):
                document = Document(path)
                paragraph_text = [paragraph.text for paragraph in document.paragraphs]
                headings = [
                    text
                    for text in paragraph_text
                    if text in {"Reviewer Comment", "Response", "Location of Revision"}
                ]
                expected_count = len(ledger["reviewers"][reviewer_index]["comments"])
                self.assertEqual(
                    ["Reviewer Comment", "Response", "Location of Revision"] * expected_count,
                    headings,
                )
                full_text = "\n".join(paragraph_text)
                for comment in ledger["reviewers"][reviewer_index]["comments"]:
                    self.assertIn(comment["verbatim_comment"], full_text)
                    self.assertIn(comment["response"], full_text)
                    self.assertNotIn(comment["comment_id"], full_text)


if __name__ == "__main__":
    unittest.main()
