from pathlib import Path
import re
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "manuscript-workflow-orchestrator"


class OrchestratorContractTests(unittest.TestCase):
    def test_orchestrator_declares_required_routes_and_gates(self) -> None:
        skill_path = SKILL_ROOT / "SKILL.md"
        self.assertTrue(skill_path.exists(), "orchestrator SKILL.md must exist")
        text = skill_path.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^name: manuscript-workflow-orchestrator$")
        self.assertRegex(text, r"(?m)^description: Use when ")
        required = [
            "新建论文",
            "普通修订",
            "审稿返修",
            "Discussion 专项",
            "投稿交付",
            "只读审计",
            "Reviewer 原文覆盖率必须为 100%",
            "未获批准不得修改",
            "Clean",
            "Highlighted",
            "Zotero",
            "Submission_Package",
        ]
        for token in required:
            self.assertIn(token, text)

    def test_orchestrator_references_are_complete(self) -> None:
        expected = {
            "ROUTING.md",
            "PROJECT_CONTRACT.md",
            "REVIEWER_REVISION.md",
            "DELIVERY_BOUNDARY.md",
            "QUALITY_GATES.md",
        }
        references = SKILL_ROOT / "references"
        self.assertTrue(references.is_dir(), "references directory must exist")
        self.assertEqual(expected, {path.name for path in references.glob("*.md")})


if __name__ == "__main__":
    unittest.main()
