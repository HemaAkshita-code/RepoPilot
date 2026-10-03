# RepoPilot

An open-source AI agent for investigating and understanding unfamiliar GitHub repositories.

RepoPilot is designed to assist developers in navigating, exploring, and analyzing codebases. The system uses **Gemma 4** as its primary open-weight reasoning model.

---

### Current Stage

**Stage 5 — Reusable Agent Skills & Investigation Workflows**

Stage 5 equips RepoPilot with a reusable Agent Skill abstraction layer:
- **Skill Engine & Lifecycle (Person 1):** `BaseSkill`, `SkillResult`, `Finding`, `SkillMetadata`, `SkillManager`, input validation, bounded execution, security enforcement, and `ToolRegistry` binding.
- **Built-in Investigation Skills (Person 2):**
  1. `ArchitectureSkill` (`understand_architecture`): Investigates high-level layout, entry points, configuration, and major subsystems.
  2. `FeatureTraceSkill` (`trace_feature`): Traces a feature, concept, or data model across repository components using semantic RAG + code search + file inspection.
  3. `APIFlowSkill` (`investigate_api_flow`): Maps API request progression across routes, controllers, services, and data access layers.
  4. `AuthSkill` (`investigate_auth`): Analyzes authentication endpoints, security middleware, token handling, and authorization boundaries.
- **Evidence Provenance & Context Integration:** All skills preserve evidence provenance within `InvestigationContext`, distinguishing observed facts from inferences.
- **Test Coverage:** Complete offline test suite (87 tests across `tests/test_skills.py`, `tests/test_indexing.py`, `tests/test_retrieval.py`, `tests/test_agent.py`, `tests/test_registry.py`, `tests/test_repository.py`, `tests/test_tools.py`, `tests/test_gemma.py`).

### ⚠️ Scope & Unimplemented Features
The following features are **NOT** implemented in Stage 5 and represent future roadmap milestones:
- LangGraph / external agent framework integration (built natively)
- Frontend UI / web interface
- Autonomous repository code modification (RepoPilot is read-only)
- Pull-request analysis / issue tracker integration

---

## Stage 5 Architecture & Capabilities

```text
                         RepoPilot
                            │
                            ▼
                         Gemma 4
                            │
                  ┌─────────┴─────────┐
                  │                   │
             Atomic Tools        Agent Skills
                  │                   │
                  │            ┌──────┴──────┐
                  │            │             │
                  │       Architecture   Feature Trace
                  │            Skill          Skill
                  │            │             │
                  │            └──────┬──────┘
                  │                   │
                  └──────────┬────────┘
                             ▼
                       Tool Registry
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         list_files      read_file      search_code
                                            │
                                            │
                                   search_repository
                                            │
                                            ▼
                                   Stage 4 Retrieval
                                            │
                                  ┌─────────┴─────────┐
                                  ▼                   ▼
                              Vector Store       Investigation
                                                     Context
                                                        │
                                                        ▼
                                                     Evidence
                                                        │
                                                        ▼
                                                  Final Answer
```

### Key Differences: Tools vs. Skills

| Dimension | Atomic Tool | Agent Skill |
| --- | --- | --- |
| **Abstraction Level** | Low-level repository operation (`read_file`, `search_code`). | High-level investigation workflow (`understand_architecture`, `trace_feature`). |
| **Execution** | Atomic, single step. | Bounded sequence combining multiple tools & retrieval calls. |
| **Output** | Raw text / match arrays. | Structured `SkillResult` with `findings` (facts vs inferences) and cited `evidence`. |
| **Evidence** | Directly populates `InvestigationContext`. | Propagates line citations into `InvestigationContext` and `AgentState`. |

---

## Project Architecture

Below is the project layout for **Stage 5**:

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
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── api_flow.py
│   │   ├── architecture.py
│   │   ├── auth.py
│   │   ├── base.py
│   │   ├── feature_trace.py
│   │   ├── manager.py
│   │   └── models.py
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
│   ├── test_skills.py
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

To run the Stage 5 agent investigation demo:

```powershell
python backend/main.py
```

---

## Running Tests

To run the complete Stage 5 test suite (100% offline):

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

To run individual test modules:
```powershell
python -m unittest tests/test_skills.py
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
- Skills cannot execute arbitrary code (`eval`, `exec`, `subprocess`) or modify repository files.

---

## Roadmap

- **Stage 1:** Foundation + Gemma 4 Connectivity
- **Stage 2:** GitHub repository ingestion + repository exploration tools
- **Stage 3:** Agent tool calling + autonomous investigation loop
- **Stage 4:** Repository indexing + retrieval/RAG
- **Stage 5 (Current):** Reusable Agent Skills & investigation workflows
- **Stage 6:** Frontend + multimodal capabilities + final integrationon control.
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
