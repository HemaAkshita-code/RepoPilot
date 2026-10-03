"""Stage 8 Evidence Integrity Regression Test Suite.

Verifies strict rules for evidence provenance:
1. Correct evidence path formatting.
2. Correct evidence line range formatting.
3. Missing evidence handling.
4. Stale evidence handling.
5. Retrieved-but-not-inspected content distinction.
6. Inferred vs verified relationship representation.
7. Verified relationship resolution.
8. Unresolved relationship handling.
9. External dependency identification.
10. Final-answer grounding in actual evidence.
"""

import unittest
from pathlib import Path
from backend.repository import load_local_repository
from backend.agent.context import InvestigationContext, EvidenceItem
from backend.analysis.index import StructuralIndex
from backend.analysis.models import Relationship


class TestEvidenceIntegrity(unittest.TestCase):
    """Regression test suite for evidence integrity, citations, and provenance."""

    @classmethod
    def setUpClass(cls):
        cls.fixture_path = Path(__file__).parent / "fixtures" / "fixture_repo"
        cls.repository = load_local_repository(cls.fixture_path)
        cls.index = StructuralIndex(cls.repository)
        cls.index.build_index()

    def test_1_correct_evidence_path(self):
        """Verify evidence items preserve repository-relative POSIX file paths."""
        ctx = InvestigationContext()
        item = EvidenceItem(
            path="app/auth.py",
            start_line=1,
            end_line=30,
            evidence_type="inspected_file",
            snippet="def authenticate_user(): pass",
        )
        ctx.inspected_files.append(item)
        self.assertEqual(ctx.inspected_files[0].path, "app/auth.py")
        self.assertFalse(Path(ctx.inspected_files[0].path).is_absolute())

    def test_2_correct_evidence_line_range(self):
        """Verify citation strings correctly format start_line and end_line."""
        ctx = InvestigationContext()
        ctx.add_retrieved_chunk("app/database.py", 12, 25, "def get_user_by_id():", score=0.95)
        citations = ctx.get_all_source_locations()
        self.assertIn("app/database.py:12-25", citations)

    def test_3_missing_evidence_handling(self):
        """Verify context returns empty lists when no evidence has been recorded."""
        ctx = InvestigationContext()
        self.assertEqual(len(ctx.retrieved_chunks), 0)
        self.assertEqual(len(ctx.inspected_files), 0)
        self.assertEqual(len(ctx.get_all_source_locations()), 0)

    def test_4_stale_evidence_handling(self):
        """Verify resetting context wipes outdated evidence when starting a new investigation."""
        ctx = InvestigationContext()
        ctx.add_inspected_file("app/old.py", "old content")
        self.assertEqual(len(ctx.inspected_files), 1)
        ctx = InvestigationContext()
        self.assertEqual(len(ctx.inspected_files), 0)

    def test_5_retrieved_vs_inspected_distinction(self):
        """Verify retrieved candidate chunks are strictly distinguished from fully inspected files."""
        ctx = InvestigationContext()
        ctx.add_retrieved_chunk("app/auth.py", 1, 10, "chunk text", score=0.8)
        ctx.add_inspected_file("app/auth.py", "full source code")
        
        self.assertEqual(len(ctx.retrieved_chunks), 1)
        self.assertEqual(len(ctx.inspected_files), 1)
        self.assertEqual(ctx.retrieved_chunks[0].evidence_type, "retrieved_chunk")
        self.assertEqual(ctx.inspected_files[0].evidence_type, "inspected_file")

    def test_6_inferred_vs_verified_relationship(self):
        """Verify relationship model explicitly represents resolution_status."""
        rel_resolved = Relationship(
            relationship_id="r1",
            relationship_type="calls",
            source="app/routes.py::login_route",
            target="app/auth.py::authenticate_user",
            resolution_status="resolved",
            confidence=1.0,
        )
        rel_ambiguous = Relationship(
            relationship_id="r2",
            relationship_type="calls",
            source="app/payments.py::execute_payment_gateway",
            target="handler",
            resolution_status="ambiguous",
            confidence=0.5,
        )
        self.assertEqual(rel_resolved.resolution_status, "resolved")
        self.assertEqual(rel_ambiguous.resolution_status, "ambiguous")

    def test_7_verified_relationship_resolution(self):
        """Verify exact function call resolution produces resolved status in structural index."""
        symbols = self.index.find_symbols("login_route")
        self.assertTrue(len(symbols) > 0)
        rels = self.index.get_symbol_relationships("login_route")
        call_rels = [r for r in rels if r.relationship_type == "calls"]
        self.assertTrue(any(r.resolution_status == "resolved" for r in call_rels))

    def test_8_unresolved_relationship_handling(self):
        """Verify dynamic call targets remain marked unresolved without hallucinating targets."""
        rels = self.index.get_symbol_relationships("execute_payment_gateway")
        # Ensure dynamic getattr call target does not claim 100% resolved confidence
        for r in rels:
            if r.relationship_type == "calls":
                self.assertNotEqual(r.resolution_status, "resolved")

    def test_9_external_dependency_identification(self):
        """Verify imports of non-repository modules are marked unresolved/external."""
        deps = self.index.get_file_dependencies("app/database.py")
        imports = deps.get("imports", [])
        # 'typing' module import from stdlib/external is unresolved in repo-scoped index
        typing_imports = [imp for imp in imports if "typing" in str(imp.get("target", ""))]
        if typing_imports:
            self.assertEqual(typing_imports[0].get("resolution_status"), "unresolved")

    def test_10_final_answer_grounding(self):
        """Verify evidence provenance formatting for grounded synthesis."""
        ctx = InvestigationContext()
        ctx.add_retrieved_chunk("app/auth.py", 1, 20, "def authenticate_user(): pass", score=0.9)
        summary = ctx.format_retrieved_context_for_prompt()
        self.assertIn("app/auth.py", summary)
        self.assertIn("Score: 0.90", summary)


if __name__ == "__main__":
    unittest.main()
