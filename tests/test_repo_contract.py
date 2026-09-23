from __future__ import annotations

import unittest
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTestCase(unittest.TestCase):
    def test_removed_standalone_deficit_feature_does_not_return(self) -> None:
        forbidden_word = "ca" "mp"
        removed_paths = [
            ROOT
            / "skills"
            / "diet-tracker"
            / "scripts"
            / ("cut_" + forbidden_word + ".py"),
            ROOT
            / "skills"
            / "diet-tracker"
            / "modules"
            / ("cut-" + forbidden_word + ".md"),
            ROOT
            / "skills"
            / "diet-tracker"
            / "references"
            / ("cut-" + forbidden_word + ".template.json"),
            ROOT / "data" / "diet" / (forbidden_word + "s") / ".gitkeep",
        ]
        self.assertTrue(all(not path.exists() for path in removed_paths))

        documentation = [
            ROOT / "AGENTS.md",
            ROOT / "README.md",
            ROOT / "README.zh-CN.md",
            ROOT / "SETUP.md",
            *sorted((ROOT / "skills" / "diet-tracker").rglob("*.md")),
            *sorted((ROOT / "tests").glob("test_*.py")),
        ]
        chinese_term = "\u8425\u671f"
        for path in documentation:
            text = path.read_text(encoding="utf-8").casefold()
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn(forbidden_word, text)
                self.assertNotIn(chinese_term, text)

    def test_runtime_data_and_credentials_are_ignored_and_untracked(self) -> None:
        for relative_path in (
            "data/diet/2099-01-01.json",
            "data/training/2099-01-01.json",
            "data/training-plans/private.json",
            ".env",
        ):
            result = subprocess.run(
                ["git", "check-ignore", "-q", relative_path],
                cwd=ROOT,
                check=False,
            )
            with self.subTest(relative_path=relative_path):
                self.assertEqual(result.returncode, 0)

        tracked = subprocess.run(
            ["git", "ls-files", "data"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        self.assertTrue(tracked)
        self.assertTrue(all(Path(path).name == ".gitkeep" for path in tracked))
    def test_phase_boundaries_and_runtime_entrypoints_are_explicit(self) -> None:
        setup = (ROOT / "SETUP.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        profile_skill = (
            ROOT / "skills" / "user-profile-management" / "SKILL.md"
        ).read_text(encoding="utf-8")
        profile_module = (
            ROOT
            / "skills"
            / "user-profile-management"
            / "modules"
            / "profile-management.md"
        ).read_text(encoding="utf-8")
        config = (
            ROOT / "coach-agent-profile" / "config.reference.yaml"
        ).read_text(encoding="utf-8")

        for text in (setup, agents, readme, readme_zh, profile_skill, profile_module):
            with self.subTest(text_source="phase documentation"):
                self.assertNotIn("Chinese-speaking", text)
                self.assertNotIn("language-configurable", text)

        for phrase in (
            "Phase 0 — Agent Profile Installation",
            "Phase 0.5 — Profile Handoff & Gateway Setup",
            "Phase 1 — User Onboarding & Fitness Profile Creation",
            "existing host Agent",
            "does **not** read `SETUP.md`",
            "data/user/profile.json",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, setup)

        for phrase in (
            "Phase 0 — Agent Profile Installation",
            "Phase 0.5 — Profile Handoff & Gateway Setup",
            "Phase 1 — User Onboarding & Fitness Profile Creation",
            "must **not read `SETUP.md`**",
            "active profile's `SOUL.md` must already exist",
            "Do not ask the language-selection question again",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, agents)

        for text in (readme, readme_zh):
            with self.subTest(text_source="README"):
                self.assertIn("Phase 0", text)
                self.assertIn("Phase 0.5", text)
                self.assertIn("Phase 1", text)
                self.assertIn("SETUP.md", text)
                self.assertIn("AGENTS.md", text)

        self.assertTrue(profile_module.startswith("# Phase 1 — User Onboarding & Fitness Profile Creation"))
        self.assertIn("does not install or configure an Agent Profile", profile_module)
        self.assertIn("read `SETUP.md`", profile_module)
        self.assertIn("do not ask the language-selection question again", profile_module)
        self.assertNotIn("SOUL.example.md", profile_module)
        self.assertNotIn("coach-agent-profile/", profile_module)
        self.assertIn("Phase 0 — Agent Profile Installation", profile_skill)
        self.assertIn("does not", profile_skill)
        self.assertIn("reads `SETUP.md`", profile_skill)
        self.assertIn("selects the runtime communication language", profile_skill)
        self.assertIn("AGENTS.md and the active profile's SOUL.md", config)

    def test_soul_examples_are_phase_zero_only_and_read_only(self) -> None:
        english = (
            ROOT / "coach-agent-profile" / "SOUL.example.md"
        ).read_text(encoding="utf-8")
        chinese = (
            ROOT / "coach-agent-profile" / "SOUL.zh-CN.example.md"
        ).read_text(encoding="utf-8")

        for text in (english, chinese):
            with self.subTest(text_source="Soul example"):
                self.assertTrue(
                    "read-only" in text.casefold() or "只读" in text
                )
                self.assertIn("Phase 0", text)
                self.assertIn("SOUL.md", text)
                self.assertIn("Phase 1", text)
                self.assertIn("not" if text is english else "不会", text)


if __name__ == "__main__":
    unittest.main()
