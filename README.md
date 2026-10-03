# RepoPilot

An open-source AI agent for investigating and understanding unfamiliar GitHub repositories.

RepoPilot is designed to assist developers in navigating, exploring, and analyzing codebases. The system uses **Gemma 4** as its primary open-weight reasoning model.

---

## Current Stage

**Stage 4 — Repository Indexing, Vector Retrieval & RAG Agent Integration**

Stage 4 upgrades RepoPilot with semantic retrieval capabilities:
- **Repository Indexing & Chunking (Person 2):** `RepositoryIndexer`, deterministic line-bounded chunking (`chunk_file`), metadata tracking (`path:start_line-end_line`), and safe file filtering.
- **Embeddings & Vector Store (Person 2):** `MockEmbeddingProvider` (deterministic offline feature hashing), `GoogleGenAIEmbeddingProvider`, and `InMemoryVectorStore` (cosine similarity search).
- **Retrieval & RAG Context (Person 1):** `RepositoryRetriever`, `search_repository` model-facing tool, `InvestigationContext`, and evidence classification (distinguishing `retrieved_chunk` from `inspected_file`).
- **Test Coverage:** Complete offline test suite (76 tests across `tests/test_indexing.py`, `tests/test_retrieval.py`, `tests/test_agent.py`, `tests/test_registry.py`, `tests/test_repository.py`, `tests/test_tools.py`, `tests/test_gemma.py`).

### ⚠️ Scope & Unimplemented Features
The following features are **NOT** implemented in Stage 4 and represent future roadmap milestones:
- LangGraph framework integration
- Agent Skills
- User interface / frontend
- Multimodal repository investigation

---

## Stage 4 Architecture & Capabilities

```text
                         RepoPilot
                            │
              ┌─────────────┴─────────────┐
              │                           │
        Repository Layer             Agent Core
             Stage 2                  Stage 3/4
              │                           │
              │                           ▼
              │                        Gemma 4
              │                           │
              │                  ┌────────┴────────┐
              │                  │                 │
              │             Tool calls       Retrieval
              │                  │                 │
              │                  ▼                 ▼
              │           Tool Registry       Retriever
              │                  │                 │
              │                  ▼                 ▼
              │          Existing Tools       Vector Store
              │                                    ▲
              │                                    │
              └──────────────► Indexer ─────► Embeddings
                                   │
                                   ▼
                                Chunks
                                   │
                                   ▼
                             Repository Files
```

### Key Components

1. **Repository Indexer (`RepositoryIndexer`)**:
   - Safely walks repository text files using Stage 2 security & ignore rules.
   - Splits text into line-bounded `CodeChunk` objects (e.g. `src/auth.py:1-40`).
   - Ignores binary files, `.git`, `node_modules`, `__pycache__`, `.venv`, and oversized files.

2. **Vector Store (`InMemoryVectorStore`)**:
   - In-memory vector store performing top-$k$ cosine similarity search over chunk embeddings.
   - Preserves source path, line ranges, content, and similarity scores.

3. **Retriever & Search Tool (`search_repository`)**:
   - Exposes `search_repository(query, top_k)` as an explicit tool in `ToolRegistry`.
   - Injects repository context internally without allowing the model to specify `repo_root`.

4. **Evidence Classification (`InvestigationContext`)**:
   - Distinguishes between **Retrieved Chunks** (RAG vector search) and **Directly Inspected Files** (`read_file` tool call).
   - Generates grounded source location citations (e.g. `src/auth.py:1-40`).

---

## Project Architecture

Below is the project layout for **Stage 4**:

```text
RepoPilot/
├── backend/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   ├── context.py
│   │   ├── models.py
│   │   ├── prompts.py
│   │   ├── registry.py
│   │   └── retrieval.py
│   ├── indexing/
│   │   ├── __init__.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── indexer.py
│   │   └── store.py
│   ├── repository/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── github.py
│   │   ├── local.py
│   │   ├── models.py
│   │   └── workspace.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── exceptions.py
│   │   ├── list_files.py
│   │   ├── read_file.py
│   │   ├── search_code.py
│   │   └── security.py
│   ├── config.py
│   ├── gemma.py
│   └── main.py
│
├── tests/
│   ├── test_agent.py
│   ├── test_gemma.py
│   ├── test_indexing.py
│   ├── test_registry.py
│   ├── test_repository.py
│   ├── test_retrieval.py
│   └── test_tools.py
│
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Windows / PowerShell Setup

Follow these steps to set up RepoPilot locally on Windows using PowerShell:

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/your-username/RepoPilot.git
   cd RepoPilot
   ```

2. **Create a virtual environment:**
   ```powershell
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

4. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Configure environment variables:**
   Copy `.env.example` to create `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
   Edit `.env` to insert your API key and confirmed model identifier.

---

## Environment Variables

RepoPilot uses environment variables for configuration:

| Variable | Description | Security / Notes |
| --- | --- | --- |
| `GEMMA_API_KEY` | API Key for accessing Gemma 4 model endpoints | **Secret.** Never commit or share publicly. |
| `GEMMA_MODEL` | Official model identifier string for Gemma 4 | Must use the identifier verified by Person 1. |

---

## Running the Application

To run the Stage 4 RAG agent investigation demo:

```powershell
python backend/main.py
```

---

## Running Tests

To run the complete Stage 4 test suite (100% offline):

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

To run individual test modules:
```powershell
python -m unittest tests/test_indexing.py
python -m unittest tests/test_retrieval.py
python -m unittest tests/test_agent.py
python -m unittest tests/test_registry.py
python -m unittest tests/test_repository.py
python -m unittest tests/test_tools.py
```

---

## Security Guidelines

- **Never commit `.env`** to version control.
- **Never expose `GEMMA_API_KEY`** in documentation, commits, or client-side code.
- **Never hardcode API keys** directly into Python files.
- Models cannot control `repo_root` or bypass Stage 2 filesystem security boundaries.

---

## Roadmap

- **Stage 1:** Foundation + Gemma 4 Connectivity
- **Stage 2:** GitHub repository ingestion + repository exploration tools
- **Stage 3:** Agent tool calling + autonomous investigation loop
- **Stage 4 (Current):** Repository indexing + retrieval/RAG
- **Stage 5:** Agent Skill implementation
- **Stage 6:** Frontend + multimodal capabilities + final integration

---

## Open Source & Licensing

RepoPilot is an open-source project released under the [MIT License](LICENSE).
