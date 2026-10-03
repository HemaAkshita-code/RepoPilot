"""
Unit tests for Stage 7 Portable Agent Skill Package (Person 1 & Person 2 Stage 7).
Validates skills/repository-investigator/SKILL.md against official Agent Skills specification rules.
Runs 100% offline.
"""

import re
import unittest
from pathlib import Path


class TestAgentSkillPackage(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(__file__).parent.parent
        self.skill_dir = self.project_root / "skills" / "repository-investigator"
        self.skill_md = self.skill_dir / "SKILL.md"

    def test_skill_directory_and_file_exist(self):
        self.assertTrue(self.skill_dir.exists(), "Skill directory skills/repository-investigator must exist.")
        self.assertTrue(self.skill_dir.is_dir(), "skills/repository-investigator must be a directory.")
        self.assertTrue(self.skill_md.exists(), "SKILL.md must exist inside skills/repository-investigator.")

    def test_yaml_frontmatter_validity(self):
        content = self.skill_md.read_text(encoding="utf-8")

        # Check frontmatter delimiters
        self.assertTrue(content.startswith("---"), "SKILL.md must begin with '---' YAML frontmatter delimiter.")

        parts = content.split("---", 2)
        self.assertGreaterEqual(len(parts), 3, "SKILL.md must contain valid '---' enclosed YAML frontmatter.")

        frontmatter_text = parts[1]

        # Extract name
        name_match = re.search(r"^name:\s*(.+)$", frontmatter_text, re.MULTILINE)
        self.assertIsNotNone(name_match, "Frontmatter must contain a 'name' field.")
        name = name_match.group(1).strip().strip("'\"")

        # Extract description
        desc_match = re.search(r"^description:\s*(.+)$", frontmatter_text, re.MULTILINE)
        self.assertIsNotNone(desc_match, "Frontmatter must contain a 'description' field.")
        description = desc_match.group(1).strip().strip("'\"")

        # Validate name rules: 1-64 chars, lowercase a-z0-9-, no leading/trailing/consecutive hyphens, matches parent dir
        parent_dir_name = self.skill_dir.name
        self.assertEqual(name, parent_dir_name, "Skill name must exactly match parent directory name.")
        self.assertTrue(1 <= len(name) <= 64, f"Skill name length must be between 1 and 64 characters (got {len(name)}).")
        self.assertTrue(re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name), f"Skill name '{name}' contains invalid characters or hyphens.")

        # Validate description rules: non-empty, <= 1024 chars
        self.assertTrue(len(description) > 0, "Description must be non-empty.")
        self.assertLessEqual(len(description), 1024, f"Description must be <= 1024 characters (got {len(description)}).")

    def test_relative_links_resolution(self):
        content = self.skill_md.read_text(encoding="utf-8")

        # Find relative markdown links like [Text](./references/filename.md)
        relative_links = re.findall(r"\]\(\./([^)]+)\)", content)
        self.assertTrue(len(relative_links) > 0, "SKILL.md should contain relative links to references.")

        for rel_link in relative_links:
            target_path = self.skill_dir / rel_link
            self.assertTrue(
                target_path.exists(),
                f"Referenced link './{rel_link}' in SKILL.md does not exist at {target_path}.",
            )

    def test_skill_implementation_independence(self):
        """Verify skill contains no RepoPilot Python implementation coupling."""
        content = self.skill_md.read_text(encoding="utf-8")

        # Ensure no internal Python modules or class imports are referenced in skill instructions
        forbidden_terms = [
            "backend.agent",
            "backend.analysis",
            "ToolRegistry",
            "BaseSkill",
            "SkillManager",
            "InvestigationContext",
            "import backend",
            "from backend",
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, content, f"Portable SKILL.md must not reference internal RepoPilot code '{term}'.")

    def test_no_absolute_filesystem_paths(self):
        content = self.skill_md.read_text(encoding="utf-8")

        # Match Windows (C:\...) or POSIX (/home/..., /Users/...) absolute paths
        abs_windows = re.findall(r"[A-Za-z]:\\[^\s\)]+", content)
        abs_posix = re.findall(r"\s/(?:Users|home|tmp|etc|var)/[^\s\)]+", content)

        self.assertEqual(len(abs_windows), 0, f"SKILL.md contains absolute Windows paths: {abs_windows}")
        self.assertEqual(len(abs_posix), 0, f"SKILL.md contains absolute POSIX paths: {abs_posix}")

    def test_skill_conciseness(self):
        lines = self.skill_md.read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lines), 500, f"SKILL.md should remain concise (< 500 lines, got {len(lines)}).")


if __name__ == "__main__":
    unittest.main()
