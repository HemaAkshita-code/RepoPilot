# RepoPilot

An open-source AI agent for investigating and understanding unfamiliar GitHub repositories.

RepoPilot is designed to assist developers in navigating, exploring, and analyzing codebases. The eventual system will use **Gemma 4** as its primary open-weight reasoning model.

---

## Current Stage

**Stage 2 — Repository Acquisition & Investigation Tools**

Stage 2 completes the core codebase acquisition and investigation tool layer:
- **Repository Acquisition (Person 2):** `Repository` abstraction, `load_local_repository`, `load_github_repository`, strict GitHub URL validation, and controlled workspace isolation (`WorkspaceManager`).
- **Investigation Tools (Person 1):** `list_files()`, `read_file(path)`, and `search_code(query)`.
- **Test Suites:** Offline unit tests for repository management (`tests/test_repository.py`) and investigation tools (`tests/test_tools.py`).

### ⚠️ Scope & Unimplemented Features
The following features are **NOT** implemented in Stage 2 and represent future roadmap milestones:
- Autonomous agent loop
- Gemma tool calling loop
- Repository indexing & vector databases
- Retrieval-Augmented Generation (RAG)
- Embeddings
- LangGraph framework integration
- Agent Skills
- User interface / frontend
- Multimodal repository investigation

---

## Repository Acquisition & Investigation Tools (Stage 2)

### Repository Acquisition Layer
- **`load_local_repository(path)`**: Validates local directory existence, permissions, and normalizes root path.
- **`load_github_repository(url)`**: Safely clones public HTTPS GitHub repositories into a controlled workspace outside the project source tree.
- **`WorkspaceManager`**: Isolates cloned repositories into temporary directories to prevent workspace contamination.

### Repository Investigation Tools
All tools operate relative to a controlled repository root (`repo_root`), which can be passed as a `Repository` object, `Path`, or `str`.

1. **`list_files(repo_root)`**:
   - Recursively discovers all repository-relative file paths.
   - Deterministically ordered (alphabetical).
   - Excludes `.git`, `node_modules`, `__pycache__`, `.venv`, and common cache/build directories.

2. **`read_file(path, repo_root)`**:
   - Safely reads repository-relative files.
   - **Security:** Prevents path traversal (`../../secret.txt`), rejects absolute paths, and blocks symlinks pointing outside the repository root.
   - **Binary Handling:** Detects binary content (`\x00` bytes) and avoids dumping binary data into output.
   - **Size Limits:** Enforces content size limits (`max_bytes`) and clearly reports truncation status.

3. **`search_code(query, repo_root)`**:
   - Recursively searches text files for a query string (case-insensitive by default).
   - Excludes binary files and ignored directories.
   - Returns structured matches with relative path, line number, and trimmed line snippet.

---

## Project Architecture

Below is the project layout for **Stage 2**:

```text
RepoPilot/
├── backend/
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
│   ├── test_gemma.py
│   ├── test_repository.py
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

RepoPilot uses environment variables for configuration. These are loaded from `.env` in development:

| Variable | Description | Security / Notes |
| --- | --- | --- |
| `GEMMA_API_KEY` | API Key for accessing Gemma 4 model endpoints | **Secret.** Never commit or share publicly. |
| `GEMMA_MODEL` | Official model identifier string for Gemma 4 | Must use the identifier verified by Person 1. |

- `.env` contains local secrets and is strictly ignored by Git.
- `.env.example` contains non-sensitive placeholders for documentation purposes.

---

## Running Tests

To run the complete Stage 2 test suite (offline):

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

To run individual test files:
```powershell
python -m unittest tests/test_repository.py
python -m unittest tests/test_tools.py
```

---

## Security Guidelines

To maintain security and prevent credential leakage:
- **Never commit `.env`** to version control.
- **Never expose `GEMMA_API_KEY`** in documentation, commits, or client-side code.
- **Never hardcode API keys** directly into Python files.
- Always treat user-supplied paths and URLs as untrusted input.
- Enforce strict repository-root boundaries for file operations.

---

## Roadmap

RepoPilot will be developed in structured stages:

- **Stage 1:** Foundation + Gemma 4 Connectivity
- **Stage 2 (Current):** GitHub repository ingestion + repository exploration tools
- **Stage 3:** Agent tool calling + autonomous investigation loop
- **Stage 4:** Repository indexing + retrieval/RAG
- **Stage 5:** Agent Skill implementation
- **Stage 6:** Frontend + multimodal capabilities + final integration

---

## Open Source & Licensing

RepoPilot is an open-source project released under the [MIT License](LICENSE).
