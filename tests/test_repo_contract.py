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


if __name__ == "__main__":
    unittest.main()
