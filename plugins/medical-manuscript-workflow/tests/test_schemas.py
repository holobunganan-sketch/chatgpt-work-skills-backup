import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


class SchemaContractTests(unittest.TestCase):
    def validate_example(self, schema_name: str, example_name: str) -> None:
        schema = load_json(f"schemas/{schema_name}")
        example = load_json(f"assets/{example_name}")
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(example)

    def test_valid_examples(self) -> None:
        cases = [
            ("project-contract.schema.json", "project-contract.example.json"),
            ("reviewer-ledger.schema.json", "reviewer-ledger.example.json"),
            ("delivery-policy.schema.json", "delivery-policy.default.json"),
        ]
        for schema_name, example_name in cases:
            with self.subTest(schema=schema_name):
                self.validate_example(schema_name, example_name)

    def test_reviewer_comment_required_fields(self) -> None:
        schema = load_json("schemas/reviewer-ledger.schema.json")
        valid = load_json("assets/reviewer-ledger.example.json")
        required_fields = [
            "source_span",
            "verbatim_comment",
            "decision",
            "response",
            "location",
            "implementation",
            "status",
        ]
        for field in required_fields:
            invalid = copy.deepcopy(valid)
            del invalid["reviewers"][0]["comments"][0][field]
            errors = list(Draft202012Validator(schema).iter_errors(invalid))
            paths = [list(error.absolute_path) for error in errors]
            self.assertTrue(
                any(path[:4] == ["reviewers", 0, "comments", 0] for path in paths),
                f"missing {field} was not rejected at the comment path",
            )

    def test_release_report_requires_gate_results(self) -> None:
        schema = load_json("schemas/release-report.schema.json")
        Draft202012Validator.check_schema(schema)
        invalid = {"project_id": "demo", "release_ready": False}
        errors = list(Draft202012Validator(schema).iter_errors(invalid))
        self.assertTrue(any("gates" in error.message for error in errors))


if __name__ == "__main__":
    unittest.main()
