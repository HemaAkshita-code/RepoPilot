"""
Unit and Integration tests for Stage 5 Agent Skills (Person 1 & Person 2).
Runs 100% offline using a deterministic fixture repository and temporary directories.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from backend.repository import Repository
from backend.agent import RepoPilotAgent, ToolRegistry, InvestigationContext, AgentResponse
from backend.skills import (
    BaseSkill,
    Finding,
    SkillResult,
    SkillMetadata,
    SkillManager,
    ArchitectureSkill,
    FeatureTraceSkill,
    APIFlowSkill,
    AuthSkill,
    get_default_skill_manager,
)


class TestSkillFramework(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Build a deterministic fixture repository structure
        (self.root / "README.md").write_text("# Test Repo\nDocumentation overview.", encoding="utf-8")
        (self.root / "pyproject.toml").write_text("[tool.poetry]\nname = 'fixture-app'\n", encoding="utf-8")

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
            "    # Authentication middleware token check\n"
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
        self.manager = get_default_skill_manager()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_skill_registration_and_lookup(self):
        skills = self.manager.list_skills()
        self.assertIn("understand_architecture", skills)
        self.assertIn("trace_feature", skills)
        self.assertIn("investigate_api_flow", skills)
        self.assertIn("investigate_auth", skills)
        self.assertEqual(len(skills), 4)

        skill = self.manager.get_skill("understand_architecture")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "understand_architecture")

        metadata = self.manager.get_skill_metadata("understand_architecture")
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["name"], "understand_architecture")

    def test_unknown_skill_rejection(self):
        res = self.manager.execute_skill("non_existent_skill", {}, self.registry)
        self.assertEqual(res.status, "failed")
        self.assertIn("Unknown skill", res.error)

    def test_skill_input_validation(self):
        # Missing required argument feature_query for trace_feature
        res = self.manager.execute_skill("trace_feature", {}, self.registry)
        self.assertEqual(res.status, "failed")
        self.assertIn("missing required argument 'feature_query'", res.error)

        # Invalid argument type for max_depth
        res_type = self.manager.execute_skill("trace_feature", {"feature_query": "user", "max_depth": "five"}, self.registry)
        self.assertEqual(res_type.status, "failed")
        self.assertIn("invalid type or value", res_type.error)

        # Unexpected argument
        res_unexp = self.manager.execute_skill("understand_architecture", {"unexpected_key": "val"}, self.registry)
        self.assertEqual(res_unexp.status, "failed")
        self.assertIn("received unexpected argument 'unexpected_key'", res_unexp.error)

    def test_rejection_of_model_supplied_repo_root(self):
        res = self.manager.execute_skill("understand_architecture", {"repo_root": "/etc"}, self.registry)
        self.assertEqual(res.status, "failed")
        self.assertIn("Security violation", res.error)

    def test_tool_registry_skill_integration(self):
        # Register skills into ToolRegistry
        self.registry.register_built_in_skills()
        tools = self.registry.list_tools()

        # Atomic tools + 4 Skills
        self.assertIn("understand_architecture", tools)
        self.assertIn("trace_feature", tools)
        self.assertIn("investigate_api_flow", tools)
        self.assertIn("investigate_auth", tools)
        self.assertEqual(len(tools), 8)

        # Validate arguments via ToolRegistry
        err = self.registry.validate_args("trace_feature", {})
        self.assertIsNotNone(err)
        self.assertIn("missing required argument 'feature_query'", err)

        # Execute skill via ToolRegistry
        tool_res = self.registry.execute("understand_architecture", {})
        self.assertTrue(tool_res.success)
        self.assertIn("skill_name", tool_res.result)
        self.assertEqual(tool_res.result["skill_name"], "understand_architecture")

    def test_evidence_propagation_and_context_integration(self):
        context = InvestigationContext()
        res = self.manager.execute_skill("understand_architecture", {}, self.registry, context=context)

        self.assertEqual(res.status, "completed")
        self.assertTrue(len(res.evidence) > 0)
        # Verify evidence recorded into InvestigationContext
        self.assertTrue(len(context.inspected_files) > 0 or len(context.retrieved_chunks) > 0)


class TestBuiltInSkills(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Build fixture files
        (self.root / "README.md").write_text("# App Documentation\nOverview of the service.", encoding="utf-8")
        (self.root / "pyproject.toml").write_text("[tool.poetry]\nname = 'app'\n", encoding="utf-8")

        backend = self.root / "backend"
        backend.mkdir()
        (backend / "main.py").write_text("from backend.auth import login\n\ndef main():\n    login('user', 'pass')\n", encoding="utf-8")
        (backend / "auth.py").write_text("def login(username, password):\n    # Authentication function\n    return True\n", encoding="utf-8")
        (backend / "routes.py").write_text("@app.get('/api/v1/status')\ndef status():\n    return {'status': 'ok'}\n", encoding="utf-8")

        self.repo = Repository(root_path=self.root)
        self.registry = ToolRegistry(self.repo)
        self.context = InvestigationContext()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_architecture_skill(self):
        skill = ArchitectureSkill()
        res = skill.execute(self.registry, context=self.context)

        self.assertEqual(res.status, "completed")
        self.assertEqual(res.skill_name, "understand_architecture")
        self.assertIn("Repository architecture investigation completed", res.summary)

        # Check findings distinguish observed vs inference
        finding_types = [f["finding_type"] for f in res.findings]
        self.assertIn("observed", finding_types)
        self.assertIn("inference", finding_types)
        self.assertIn("README.md", res.evidence or [loc.split(':')[0] for loc in res.evidence])

    def test_feature_trace_skill(self):
        skill = FeatureTraceSkill()
        res = skill.execute(self.registry, context=self.context, feature_query="login")

        self.assertEqual(res.status, "completed")
        self.assertEqual(res.skill_name, "trace_feature")
        self.assertIn("login", res.summary)

        # Evidence should cite auth.py or main.py
        locs = " ".join(res.evidence)
        self.assertTrue("backend/auth.py" in locs or "backend/main.py" in locs)

    def test_api_flow_skill(self):
        skill = APIFlowSkill()
        res = skill.execute(self.registry, context=self.context, endpoint_query="/api/v1/status")

        self.assertEqual(res.status, "completed")
        self.assertEqual(res.skill_name, "investigate_api_flow")
        self.assertIn("/api/v1/status", res.summary)
        self.assertTrue(len(res.findings) > 0)

    def test_auth_skill(self):
        skill = AuthSkill()
        res = skill.execute(self.registry, context=self.context, auth_query="login")

        self.assertEqual(res.status, "completed")
        self.assertEqual(res.skill_name, "investigate_auth")
        self.assertIn("Authentication investigation completed", res.summary)

        # Verify findings include evidence from backend/auth.py or backend/main.py
        locs = " ".join(res.evidence)
        self.assertTrue("backend/auth.py" in locs or "backend/main.py" in locs)


class TestAgentSkillIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        (self.root / "README.md").write_text("# Fixture App\nMain architecture.", encoding="utf-8")
        src = self.root / "src"
        src.mkdir()
        (src / "app.py").write_text("def run():\n    print('Starting app')\n", encoding="utf-8")

        self.repo = Repository(root_path=self.root)
        self.registry = ToolRegistry(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_end_to_end_skill_invocation(self):
        mock_gemma = MagicMock()
        mock_gemma.generate_with_tools.side_effect = [
            # Turn 1: Model invokes understand_architecture skill
            {
                "text": "I will analyze the repository architecture.",
                "function_calls": [{"name": "understand_architecture", "args": {}}],
            },
            # Turn 2: Model returns grounded final answer based on skill result
            {
                "text": "The repository is structured with a root README.md and a main package in src/app.py.",
                "function_calls": [],
            },
        ]

        agent = RepoPilotAgent(
            registry=self.registry,
            gemma_client=mock_gemma,
            enable_skills=True,
        )

        resp = agent.run("What is the architecture of this repository?")

        self.assertIsInstance(resp, AgentResponse)
        self.assertEqual(resp.status, "completed")
        self.assertEqual(resp.steps_count, 2)
        self.assertIn("src/app.py", resp.evidence or resp.final_answer)
        self.assertIn("README.md", resp.evidence or resp.final_answer)


if __name__ == "__main__":
    unittest.main()
