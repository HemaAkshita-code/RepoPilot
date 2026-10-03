"""
Unit tests for Person 2 Stage 4 Repository Indexing, Chunking, Embeddings, and Vector Store.
Runs 100% offline with temporary test repositories.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from backend.repository import Repository
from backend.indexing import (
    CodeChunk,
    chunk_file,
    infer_language,
    MockEmbeddingProvider,
    InMemoryVectorStore,
    VectorSearchResult,
    RepositoryIndexer,
    cosine_similarity,
)


class TestChunking(unittest.TestCase):
    def test_infer_language(self):
        self.assertEqual(infer_language("main.py"), "python")
        self.assertEqual(infer_language("index.js"), "javascript")
        self.assertEqual(infer_language("README.md"), "markdown")
        self.assertEqual(infer_language("unknown.xyz"), "text")

    def test_deterministic_chunk_generation(self):
        content = "\n".join([f"Line {i}" for i in range(1, 101)])  # 100 lines
        chunks = chunk_file("src/main.py", content, chunk_size_lines=40, overlap_lines=10)

        self.assertGreaterEqual(len(chunks), 3)
        c1 = chunks[0]
        self.assertEqual(c1.path, "src/main.py")
        self.assertEqual(c1.start_line, 1)
        self.assertEqual(c1.end_line, 40)
        self.assertEqual(c1.chunk_id, "src/main.py:1-40")
        self.assertEqual(c1.language, "python")

        # Check line overlap
        c2 = chunks[1]
        self.assertEqual(c2.start_line, 31)

    def test_empty_content_chunking(self):
        self.assertEqual(chunk_file("empty.py", ""), [])
        self.assertEqual(chunk_file("empty.py", "   \n  "), [])


class TestEmbeddings(unittest.TestCase):
    def test_mock_embedding_provider_deterministic(self):
        provider = MockEmbeddingProvider(dimension=64)
        vec1 = provider.embed_text("function authenticate_user(username, password)")
        vec2 = provider.embed_text("function authenticate_user(username, password)")
        vec_diff = provider.embed_text("database connection pool initialization")

        self.assertEqual(len(vec1), 64)
        self.assertEqual(vec1, vec2)
        self.assertNotEqual(vec1, vec_diff)

    def test_cosine_similarity(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]

        self.assertAlmostEqual(cosine_similarity(v1, v2), 1.0)
        self.assertAlmostEqual(cosine_similarity(v1, v3), 0.0)


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryVectorStore()
        self.c1 = CodeChunk("file1.py:1-10", "file1.py", 1, 10, "def auth(): pass", "python")
        self.c2 = CodeChunk("file2.py:1-10", "file2.py", 1, 10, "def db_connect(): pass", "python")

    def test_add_and_search_vector_store(self):
        self.assertTrue(self.store.is_empty())
        self.store.add_chunks([self.c1, self.c2], [[1.0, 0.0], [0.0, 1.0]])

        self.assertEqual(self.store.count(), 2)

        results = self.store.search([1.0, 0.0], top_k=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk.chunk_id, "file1.py:1-10")
        self.assertAlmostEqual(results[0].score, 1.0)

    def test_index_rebuild_and_clear(self):
        self.store.add_chunks([self.c1], [[1.0, 0.0]])
        self.assertEqual(self.store.count(), 1)

        self.store.clear()
        self.assertTrue(self.store.is_empty())
        self.assertEqual(self.store.count(), 0)


class TestRepositoryIndexer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)

        # Create source files
        (self.root / "README.md").write_text("# Project\nRepo documentation", encoding="utf-8")
        src = self.root / "src"
        src.mkdir(parents=True, exist_ok=True)
        (src / "auth.py").write_text("def login():\n    return True\n" * 20, encoding="utf-8")

        # Create ignored directories and files
        node_dir = self.root / "node_modules"
        node_dir.mkdir(parents=True, exist_ok=True)
        (node_dir / "dep.js").write_text("var x = 1;", encoding="utf-8")

        # Binary file
        bin_dir = self.root / "assets"
        bin_dir.mkdir(parents=True, exist_ok=True)
        (bin_dir / "logo.png").write_bytes(b"\x00\x01\x02\x03PNG")

        self.repo = Repository(root_path=self.root)
        self.indexer = RepositoryIndexer(self.repo)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_repository_indexing_pipeline(self):
        self.assertFalse(self.indexer.is_indexed())
        chunk_count = self.indexer.index_repository()

        self.assertTrue(self.indexer.is_indexed())
        self.assertGreater(chunk_count, 0)

        # Search in vector store
        query_vec = self.indexer.embedding_provider.embed_text("login")
        results = self.indexer.vector_store.search(query_vec, top_k=5)

        self.assertGreater(len(results), 0)
        paths = [r.chunk.path for r in results]
        self.assertIn("src/auth.py", paths)
        self.assertNotIn("node_modules/dep.js", paths)
        self.assertNotIn("assets/logo.png", paths)


if __name__ == "__main__":
    unittest.main()
