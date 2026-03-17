import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_catalog import ProjectCatalog


class ProjectCatalogTests(unittest.TestCase):
    def test_create_and_resolve_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "catalog.json"
            project_root = Path(tmp) / "alpha-app"
            project_root.mkdir(parents=True, exist_ok=True)
            (project_root / ".git").mkdir()
            (project_root / "package.json").write_text("{}", encoding="utf-8")

            with patch.dict(
                os.environ,
                {
                    "PROJECT_CATALOG_PATH": str(catalog_path),
                },
                clear=False,
            ):
                catalog = ProjectCatalog()
                record = catalog.create_or_update_project(
                    root_path=project_root,
                    aliases=["barbearia", "alpha"],
                    priority_score=10,
                )
                match, confidence, candidates = catalog.resolve("barbearia")

            self.assertIsNotNone(match)
            self.assertEqual(match.project_id, record.project_id)
            self.assertEqual(confidence, "high")
            self.assertTrue(candidates)

    def test_scan_detects_git_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_root = root / "beta-service"
            project_root.mkdir(parents=True, exist_ok=True)
            (project_root / ".git").mkdir()
            (project_root / "requirements.txt").write_text("requests\n", encoding="utf-8")

            with patch.dict(
                os.environ,
                {
                    "PROJECT_CATALOG_PATH": str(root / "catalog.json"),
                    "PROJECT_SCAN_ROOTS": str(root),
                    "PROJECT_SCAN_MAX_DEPTH": "2",
                },
                clear=False,
            ):
                catalog = ProjectCatalog()
                discovered = catalog.scan()

            self.assertEqual(len(discovered), 1)
            self.assertEqual(discovered[0].name, "beta-service")

    def test_update_and_remove_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "catalog.json"
            project_root = Path(tmp) / "gamma-app"
            project_root.mkdir(parents=True, exist_ok=True)
            (project_root / ".git").mkdir()

            with patch.dict(
                os.environ,
                {
                    "PROJECT_CATALOG_PATH": str(catalog_path),
                },
                clear=False,
            ):
                catalog = ProjectCatalog()
                record = catalog.create_or_update_project(root_path=project_root, aliases=["gamma"])
                catalog.rename_project(record.project_id, "Gamma Renamed")
                catalog.set_aliases(record.project_id, ["gamma", "cliente-x"])
                catalog.set_priority(record.project_id, 7)
                updated = catalog.get_project(record.project_id)
                removed = catalog.remove_project(record.project_id)

            self.assertIsNotNone(updated)
            self.assertEqual(updated.name, "Gamma Renamed")
            self.assertIn("cliente-x", updated.aliases)
            self.assertEqual(updated.priority_score, 7)
            self.assertIsNotNone(removed)
            self.assertIsNone(catalog.get_project(record.project_id))

    def test_resolve_handles_jarvez_name_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog_path = Path(tmp) / "catalog.json"
            project_root = Path(tmp) / "Jarvez2.0"
            project_root.mkdir(parents=True, exist_ok=True)
            (project_root / ".git").mkdir()
            (project_root / "package.json").write_text("{}", encoding="utf-8")

            with patch.dict(
                os.environ,
                {
                    "PROJECT_CATALOG_PATH": str(catalog_path),
                },
                clear=False,
            ):
                catalog = ProjectCatalog()
                record = catalog.create_or_update_project(root_path=project_root, aliases=["jarvez", "jarviz"])
                match_jarvis, confidence_jarvis, _ = catalog.resolve("Jarvis 2.0")
                match_jarviz, confidence_jarviz, _ = catalog.resolve("Jarviz2.0")

            self.assertIsNotNone(match_jarvis)
            self.assertEqual(match_jarvis.project_id, record.project_id)
            self.assertEqual(confidence_jarvis, "high")
            self.assertIsNotNone(match_jarviz)
            self.assertEqual(match_jarviz.project_id, record.project_id)
            self.assertEqual(confidence_jarviz, "high")


if __name__ == "__main__":
    unittest.main()
