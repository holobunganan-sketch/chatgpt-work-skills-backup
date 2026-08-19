import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "mimo_prompt_tool.py"
FIX = ROOT / "tests" / "fixtures"


def run_tool(*args):
    return subprocess.run(
        [sys.executable, str(TOOL), *map(str, args)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class CompileTests(unittest.TestCase):
    def test_compile_contains_contract_sections(self):
        r = run_tool("compile", "--input", FIX / "basic_task.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        for section in ["# TASK", "# CONTEXT", "# SOURCES", "# WORKFLOW", "# CONSTRAINTS", "# OUTPUT", "# QUALITY GATE"]:
            self.assertIn(section, r.stdout)

    def test_medical_profile_adds_evidence_rules(self):
        r = run_tool("compile", "--input", FIX / "medical_task.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("事实 / 推断", r.stdout)
        self.assertIn("来源优先级", r.stdout)
        self.assertIn("材料未提供", r.stdout)

    def test_long_context_profile_adds_source_map_and_chunk_rules(self):
        r = run_tool("compile", "--input", FIX / "long_context_task.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SOURCE MAP", r.stdout)
        self.assertIn("来源编号", r.stdout)
        self.assertIn("上下文位置", r.stdout)

    def test_compile_can_write_output_file(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "prompt.md"
            r = run_tool("compile", "--input", FIX / "basic_task.json", "--output", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(out.exists())
            self.assertIn("# TASK", out.read_text(encoding="utf-8"))


class LintTests(unittest.TestCase):
    def test_lint_good_prompt_passes(self):
        compiled = run_tool("compile", "--input", FIX / "basic_task.json")
        self.assertEqual(compiled.returncode, 0, compiled.stderr)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "good.md"
            p.write_text(compiled.stdout, encoding="utf-8")
            r = run_tool("lint", "--prompt", p)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("PASS", r.stdout)

    def test_lint_detects_missing_sections_and_weak_constraints(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.md"
            p.write_text("帮我认真分析一下，尽量详细，注意不要犯错。", encoding="utf-8")
            r = run_tool("lint", "--prompt", p)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("missing_section", r.stdout)
            self.assertIn("weak_constraint_language", r.stdout)


class CachePlanTests(unittest.TestCase):
    def test_cache_plan_recommends_stable_prefix(self):
        r = run_tool("cache-plan", "--input", FIX / "basic_task.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["prefix_order"][0], "system_identity")
        self.assertIn("current_task", data["variable_suffix"])
        self.assertIn("current_materials", data["variable_suffix"])


class ValidateSpecTests(unittest.TestCase):
    def test_validate_spec_rejects_missing_required_field(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "bad.json"
            f.write_text(json.dumps({"goal": "x"}, ensure_ascii=False), encoding="utf-8")
            r = run_tool("validate-spec", "--input", f)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("task_type", r.stdout)
            self.assertIn("deliverable", r.stdout)


if __name__ == "__main__":
    unittest.main()
