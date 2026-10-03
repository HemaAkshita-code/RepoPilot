"""
Unit tests for Stage 6 Call Flow Traversal Engine (Person 1 Stage 6).
Tests downstream tracing, upstream tracing, depth bounding, cycle detection, and unresolved calls.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from backend.analysis.index import StructuralIndex
from backend.analysis.relationships import trace_call_flow
from backend.repository import Repository


class TestCallFlowEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Call Chain: step_a -> step_b -> step_c -> step_a (cycle)
        app_py = self.root / "app.py"
        app_py.write_text(
            "def step_c():\n"
            "    return step_a()\n\n"
            "def step_b():\n"
            "    return step_c()\n\n"
            "def step_a():\n"
            "    return step_b()\n",
            encoding="utf-8",
        )

        # Call Chain: route_handler -> service_call -> db_call -> external_lib_call
        flow_py = self.root / "flow.py"
        flow_py.write_text(
            "def db_call():\n"
            "    return external_unresolved_function()\n\n"
            "def service_call():\n"
            "    return db_call()\n\n"
            "def route_handler():\n"
            "    return service_call()\n",
            encoding="utf-8",
        )

        self.repo = Repository(root_path=self.root)
        self.index = StructuralIndex(self.repo)
        self.index.build_index()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_downstream_call_flow(self):
        trace = trace_call_flow(self.index, "route_handler", direction="downstream", max_depth=3)

        self.assertEqual(trace.direction, "downstream")
        self.assertEqual(trace.max_depth, 3)
        self.assertTrue(len(trace.nodes) > 1)

        node_names = [n["name"] for n in trace.nodes]
        self.assertIn("route_handler", node_names)
        self.assertIn("service_call", node_names)
        self.assertIn("db_call", node_names)

        # External function should be captured in unresolved_calls
        self.assertIn("external_unresolved_function", trace.unresolved_calls)

    def test_upstream_call_flow(self):
        trace = trace_call_flow(self.index, "db_call", direction="upstream", max_depth=3)

        self.assertEqual(trace.direction, "upstream")
        node_names = [n["name"] for n in trace.nodes]
        self.assertIn("db_call", node_names)
        self.assertIn("service_call", node_names)
        self.assertIn("route_handler", node_names)

    def test_cycle_detection(self):
        trace = trace_call_flow(self.index, "step_a", direction="downstream", max_depth=5)

        self.assertTrue(trace.cycles_detected)
        self.assertTrue(len(trace.nodes) <= 3)  # Visited nodes deduplicated

    def test_depth_bounding(self):
        trace_shallow = trace_call_flow(self.index, "route_handler", direction="downstream", max_depth=1)
        self.assertEqual(trace_shallow.max_depth, 1)

        node_names = [n["name"] for n in trace_shallow.nodes]
        self.assertIn("route_handler", node_names)
        self.assertNotIn("db_call", node_names)


if __name__ == "__main__":
    unittest.main()
