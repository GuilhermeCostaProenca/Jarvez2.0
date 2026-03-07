import tempfile
import unittest
from pathlib import Path

from code_knowledge import CodeKnowledgeIndex


class CodeKnowledgeIndexTests(unittest.TestCase):
    def test_indexes_multiple_projects_without_mixing_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_a = root / "project-a"
            project_b = root / "project-b"
            project_a.mkdir()
            project_b.mkdir()
            (project_a / "auth.ts").write_text("export const authMode = 'jwt';\n", encoding="utf-8")
            (project_b / "payments.ts").write_text("export const paymentProvider = 'stripe';\n", encoding="utf-8")

            index = CodeKnowledgeIndex(root / "code.db")
            index.index_project("a", project_a, project_name="Project A", aliases=["alpha"])
            index.index_project("b", project_b, project_name="Project B", aliases=["beta"])

            auth_results = index.search("authMode", project_id="a")
            payment_results = index.search("paymentProvider", project_id="b")
            global_results = index.search("stripe")

        self.assertEqual(len(auth_results), 1)
        self.assertEqual(auth_results[0]["project_id"], "a")
        self.assertEqual(len(payment_results), 1)
        self.assertEqual(payment_results[0]["project_id"], "b")
        self.assertTrue(any(item["project_id"] == "b" for item in global_results))


if __name__ == "__main__":
    unittest.main()
