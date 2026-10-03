"""
Integration tests and deterministic evaluation for Stage 6 Structural Analysis (Person 1 & Person 2).
Tests Agent end-to-end structural investigation, InvestigationContext integration, and structural evaluation suite.
Runs 100% offline using mocked Gemma responses.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from backend.agent import AgentResponse, InvestigationContext, RepoPilotAgent, ToolRegistry
from backend.repository import Repository


class TestStructuralAgentIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Create realistic multi-directory fixture repository
        (self.root / "README.md").write_text("# Service Architecture\nOverview", encoding="utf-8")
        (self.root / "pyproject.toml").write_text("[tool.poetry]\nname = 'service'\n", encoding="utf-8")

        api_dir = self.root / "backend" / "api"
        api_dir.mkdir(parents=True, exist_ok=True)
        (api_dir / "routes.py").write_text(
            "from backend.services.user_service import get_user\n"
            "from backend.auth.middleware import auth_required\n\n"
            "@router.get('/api/v1/users')\n"
            "@auth_required\n"
            "def handle_get_user(user_id: str):\n"
            "    return get_user(user_id)\n",
            encoding="utf-8",
        )

        service_dir = self.root / "backend" / "services"
        service_dir.mkdir(parents=True, exist_ok=True)
        (service_dir / "user_service.py").write_text(
            "from backend.database.repository import UserRepository\n\n"
            "def get_user(user_id: str):\n"
            "    repo = UserRepository()\n"
            "    return repo.find_by_id(user_id)\n",
            encoding="utf-8",
        )

        auth_dir = self.root / "backend" / "auth"
        auth_dir.mkdir(parents=True, exist_ok=True)
        (auth_dir / "middleware.py").write_text(
            "def auth_required(func):\n"
            "    def wrapper(*args, **kwargs):\n"
            "        return func(*args, **kwargs)\n"
            "    return wrapper\n",
            encoding="utf-8",
        )

        db_dir = self.root / "backend" / "database"
        db_dir.mkdir(parents=True, exist_ok=True)
        (db_dir / "repository.py").write_text(
            "class UserRepository:\n"
            "    def find_by_id(self, user_id: str):\n"
            "        return {'id': user_id, 'name': 'Alice'}\n",
            encoding="utf-8",
        )

        self.repo = Repository(root_path=self.root)
        self.registry = ToolRegistry(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_structural_tool_invocation(self):
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.side_effect = [
            # Turn 1: Model calls find_symbol
            {
                "text": "I will find the definition of handle_get_user.",
                "function_calls": [{"name": "find_symbol", "args": {"symbol_name": "handle_get_user"}}],
            },
            # Turn 2: Model traces call flow
            {
                "text": "Now I will trace the call flow from handle_get_user downstream.",
                "function_calls": [{"name": "trace_call_flow", "args": {"symbol": "handle_get_user", "direction": "downstream", "depth": 3}}],
            },
            # Turn 3: Final grounded answer
            {
                "text": "handle_get_user is defined in backend/api/routes.py:6-7 and calls get_user in backend/services/user_service.py:3-5.",
                "function_calls": [],
            },
        ]

        agent = RepoPilotAgent(
            registry=self.registry,
            gemma_client=mock_gemma,
            enable_structural_analysis=True,
        )

        resp = agent.run("How does handle_get_user process requests?")

        self.assertIsInstance(resp, AgentResponse)
        self.assertEqual(resp.status, "completed")
        self.assertEqual(resp.steps_count, 3)
        self.assertIn("backend/api/routes.py", resp.evidence or resp.final_answer)

    def test_investigation_context_structural_evidence(self):
        context = InvestigationContext()
        context.add_structural_evidence("backend/api/routes.py", start_line=6, end_line=7, snippet="def handle_get_user")

        locs = context.get_all_source_locations()
        self.assertIn("backend/api/routes.py:6-7", locs)
        self.assertEqual(context.structural_evidence[0].evidence_type, "structural_analysis")


class TestStructuralEvaluationSuite(unittest.TestCase):
    """
    Deterministic structural evaluation suite measuring symbol, call flow, and dependency discovery.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        (self.root / "auth.py").write_text(
            "def verify_token(token):\n"
            "    return True\n\n"
            "def authenticate_user(user, token):\n"
            "    return verify_token(token)\n",
            encoding="utf-8",
        )

        (self.root / "routes.py").write_text(
            "import auth\n\n"
            "def login():\n"
            "    return auth.authenticate_user('admin', 'token')\n",
            encoding="utf-8",
        )

        self.repo = Repository(root_path=self.root)
        self.registry = ToolRegistry(self.repo)
        self.registry.register_structural_tools()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_eval_question_1_where_is_authentication_implemented(self):
        sym_res = self.registry.execute("find_symbol", {"symbol_name": "authenticate_user"})
        self.assertTrue(sym_res.success)
        self.assertEqual(sym_res.result["symbols"][0]["file_path"], "auth.py")

    def test_eval_question_2_what_calls_authenticate_user(self):
        ref_res = self.registry.execute("find_references", {"symbol_name": "authenticate_user"})
        self.assertTrue(ref_res.success)
        ref_files = [r.get("evidence", {}).get("file_path") for r in ref_res.result["ast_references"]]
        self.assertIn("routes.py", ref_files)

    def test_eval_question_3_what_does_login_call(self):
        flow_res = self.registry.execute("trace_call_flow", {"symbol": "login", "direction": "downstream", "depth": 2})
        self.assertTrue(flow_res.success)
        nodes = [n["name"] for n in flow_res.result["nodes"]]
        self.assertIn("login", nodes)
        self.assertIn("authenticate_user", nodes)

    def test_eval_question_4_which_modules_does_login_route_import(self):
        dep_res = self.registry.execute("get_file_dependencies", {"file_path": "routes.py"})
        self.assertTrue(dep_res.success)
        targets = [i["target"] for i in dep_res.result["imports"]]
        self.assertTrue(any("auth" in t for t in targets))


if __name__ == "__main__":
    unittest.main()
