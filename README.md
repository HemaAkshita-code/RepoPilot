# RepoPilot

An open-source AI agent for investigating and understanding unfamiliar GitHub repositories.

RepoPilot is designed to assist developers in navigating, exploring, and analyzing codebases. The eventual system will use **Gemma 4** as its primary open-weight reasoning model.

---

## Current Stage

**Stage 1 — Foundation + Gemma 4 Connectivity**

Stage 1 establishes the initial technical foundation:
- Project directory structure
- Python environment setup
- Configuration management
- Basic Gemma 4 model connectivity
- Testing framework configuration
- Open-source repository infrastructure

### ⚠️ Scope & Unimplemented Features
The following features are **NOT** implemented in Stage 1 and represent future roadmap milestones:
- GitHub repository ingestion
- Repository exploration tools
- Autonomous agent loop
- Tool calling
- Code search
- Repository mapping
- Retrieval-Augmented Generation (RAG)
- Embeddings
- Vector database integration
- LangGraph framework integration
- Agent Skills
- User interface / frontend
- Multimodal repository investigation

---

## Project Architecture

Below is the intended project layout for **Stage 1**:

```text
RepoPilot/
├── backend/
│   ├── config.py
│   ├── gemma.py
│   └── main.py
│
├── tests/
│   └── test_gemma.py
│
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

> **Note:** Backend implementation files (`backend/`), test suites (`tests/`), and dependency manifests (`requirements.txt`) are managed separately by the backend team (Person 1).

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

   > **Important:** The exact `GEMMA_MODEL` identifier string will be provided and verified by Person 1 (Backend Lead).

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

## Running the Application

To run the Stage 1 CLI application, execute the entry point script (once implemented by Person 1):

```powershell
python backend/main.py
```

*(This is the expected command structure for Stage 1 execution).*

---

## Running Tests

To run unit and connectivity tests for Stage 1:

```powershell
pytest
```

---

## Expected Output Flow

Stage 1 validates basic end-to-end connectivity with Gemma 4:

```text
User prompt
    ↓
RepoPilot
    ↓
Gemma 4
    ↓
Model response
```

*Illustrative Example Output:*
```text
[RepoPilot Stage 1] Initializing Gemma 4 connectivity...
[Prompt]: Hello, RepoPilot!
[Response]: Hello! I am RepoPilot powered by Gemma 4. Ready to investigate repositories.
```

---

## Security Guidelines

To maintain security and prevent credential leakage:
- **Never commit `.env`** to version control.
- **Never expose `GEMMA_API_KEY`** in documentation, commits, or client-side code.
- **Never hardcode API keys** directly into Python files.
- Always use `.env` for local execution and `.env.example` as a placeholder reference.
- Inspect `git status` and `git diff` prior to every commit to verify secrets are excluded.

---

## Roadmap

RepoPilot will be developed in structured stages:

- **Stage 1 (Current):** Foundation + Gemma 4 Connectivity
- **Stage 2:** GitHub repository ingestion + repository exploration tools
- **Stage 3:** Agent tool calling + autonomous investigation loop
- **Stage 4:** Repository indexing + retrieval/RAG
- **Stage 5:** Agent Skill implementation
- **Stage 6:** Frontend + multimodal capabilities + final integration

---

## Open Source & Licensing

RepoPilot is an open-source project released under the [MIT License](LICENSE).
