import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "deepseek_prompt_tool.py"


def run_tool(*args):
    return subprocess.run([sys.executable, str(TOOL), *args], cwd=ROOT, text=True, capture_output=True)


class DeepSeekPromptToolTests(unittest.TestCase):
    def write_spec(self, data):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False)
        json.dump(data, f, ensure_ascii=False)
        f.close()
        self.addCleanup(lambda: Path(f.name).unlink(missing_ok=True))
        return f.name

    def base_spec(self):
        return {
            "title": "医学文献结论整理",
            "task_type": "medical",
            "objective": "依据给定文献提取研究设计与关键结论",
            "deliverable": "中文结构化摘要",
            "audience": "医学事务团队",
            "risk": "medium",
            "complexity": "moderate",
            "agentic": False,
            "long_context": True,
            "constraints": ["所有数字必须来自提供材料", "无法确认的信息标记为材料未提供"],
            "quality_checks": ["核对样本量、终点和效应值"],
            "output": {"language": "zh-CN", "format": "自然段+必要项目符号", "length": "1200字以内"},
            "sources": [{"id": "S1", "name": "研究论文", "authority": "primary", "cache_scope": "stable", "content": "示例材料正文"}],
            "cache": {"stable_context": ["医学事务内部写作规范"], "dynamic_context": ["本轮提问"]}
        }

    def test_validate_spec_accepts_valid_input(self):
        path = self.write_spec(self.base_spec())
        r = run_tool("validate-spec", path)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        self.assertIn("VALID", r.stdout)

    def test_route_selects_nonthink_for_routine_low_risk(self):
        spec = self.base_spec(); spec.update({"task_type": "writing", "risk": "low", "complexity": "routine", "agentic": False, "long_context": False})
        r = run_tool("route", self.write_spec(spec))
        self.assertEqual(r.returncode, 0)
        self.assertIn('"mode": "nonthink"', r.stdout)

    def test_route_selects_max_for_complex_agent(self):
        spec = self.base_spec(); spec.update({"task_type": "agent", "risk": "high", "complexity": "complex", "agentic": True})
        r = run_tool("route", self.write_spec(spec))
        self.assertEqual(r.returncode, 0)
        self.assertIn('"reasoning_effort": "max"', r.stdout)

    def test_compile_contains_source_authority_and_stop_condition(self):
        spec = self.base_spec(); spec.update({"agentic": True, "task_type": "agent", "stop_condition": "交付物通过全部质量检查后停止"})
        r = run_tool("compile", self.write_spec(spec), "--profile", "agent")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("SOURCE AUTHORITY", r.stdout)
        self.assertIn("STOP CONDITION", r.stdout)
        self.assertIn("交付物通过全部质量检查后停止", r.stdout)

    def test_compile_places_reusable_prefix_before_current_task(self):
        r = run_tool("compile", self.write_spec(self.base_spec()), "--profile", "medical")
        self.assertEqual(r.returncode, 0)
        self.assertLess(r.stdout.index("STABLE PREFIX"), r.stdout.index("CURRENT TASK"))
        self.assertLess(r.stdout.index("医学事务内部写作规范"), r.stdout.index("本轮提问"))

    def test_lint_rejects_prompt_without_quality_gate(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".md", encoding="utf-8", delete=False)
        f.write("# CURRENT TASK\nDo something\n# OUTPUT\nText")
        f.close(); self.addCleanup(lambda: Path(f.name).unlink(missing_ok=True))
        r = run_tool("lint", f.name)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("QUALITY GATE", r.stdout)

    def test_cache_plan_reports_prefix_order(self):
        r = run_tool("cache-plan", self.write_spec(self.base_spec()))
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["strategy"], "stable-prefix-first")
        self.assertGreaterEqual(data["stable_items"], 2)

    def test_adapter_for_official_deepseek_max(self):
        spec = self.base_spec(); spec.update({"task_type": "agent", "risk": "high", "complexity": "complex", "agentic": True, "provider": "deepseek-official"})
        r = run_tool("adapter", self.write_spec(spec))
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["model"], "deepseek-v4-flash")
        self.assertEqual(data["reasoning_effort"], "max")
        self.assertEqual(data["thinking"]["type"], "enabled")

    def test_doctor_passes_package_integrity(self):
        r = run_tool("doctor")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("PACKAGE OK", r.stdout)


if __name__ == "__main__":
    unittest.main()
