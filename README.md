# RepoPilot

An open-source AI agent system for investigating and understanding unfamiliar software repositories.

RepoPilot assists developers in navigating, exploring, and analyzing codebases using **Gemma 4** as its primary open-weight reasoning model.

---

## Current Status

**Stage 8 — Hardening, Deterministic Evaluation & Release Readiness (Final Stage)**

RepoPilot is fully implemented, evaluated, and hardened across 8 development stages:
- **Deterministic Fixture Repository (`tests/fixtures/fixture_repo`):** Multi-module Python codebase for offline benchmark evaluation.
- **Offline Benchmark Evaluation Dataset (`tests/test_evaluation.py`):** 7 core investigation benchmark cases measuring file retrieval precision, symbol identification accuracy, relationship correctness, and citation accuracy.
- **Failure-Case & Resilience Suite (`tests/test_failure_cases.py`):** Safe handling of missing files, bad syntax, cyclic calls, binary files, stale indexes, and agent iteration bounds.
- **Evidence Integrity Suite (`tests/test_evidence_integrity.py`):** Strict evidence provenance, non-fabrication of source facts, and explicit resolution status tracking (`resolved`, `unresolved`, `ambiguous`).
- **Portable Agent Skill Package (`skills/repository-investigator/`):** Specification-compliant Agent Skill package enforcing investigation methodology for external AI agents.
- **Documentation Suite (`docs/`):** Detailed architectural specs ([docs/architecture.md](docs/architecture.md)), evaluation results ([docs/evaluation.md](docs/evaluation.md)), and security model ([docs/security.md](docs/security.md)).

---

## High-Level Architecture

```text
                         USER
                           │
                           ▼
                    ┌──────────────┐
                    │   Gemma 4    │
                    │ Agent Reason │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Tool Registry│
                    └──────┬───────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
    Repository       Semantic RAG      Structural
      Tools                             Analysis
          │                │                 │
          └────────────────┼─────────────────┘
                           ▼
                 ┌────────────────────┐
                 │ Investigation      │
                 │ Context            │
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │ Evidence & Findings│
                 └─────────┬──────────┘
                           │
                           ▼
                 ┌────────────────────┐
                 │ Evidence-backed    │
                 │ Final Answer       │
                 └────────────────────┘


             Portable Agent Skill
             ────────────────────
             repository-investigator
                         │
                         ▼
             Investigation methodology
                         │
                         ▼
             Compatible AI agents
```

---

## Project Structure

```text
RepoPilot/
├── backend/
│   ├── agent/                 # Agent loop, Tool Registry, Context & Evidence tracking
│   ├── analysis/              # Static Python AST analysis & Call Flow engine
│   ├── indexing/              # Chunking, Vector Store & Semantic Retrieval RAG
│   ├── repository/            # Local repo loader & public GitHub cloner
│   ├── skills/                # Internal RepoPilot Python skill infrastructure
│   ├── tools/                 # Safe file reading, listing & searching tools
│   ├── config.py              # Environment configuration & settings
│   ├── gemma.py               # Gemma 4 LLM client integration
│   └── main.py                # Demonstration CLI entry point
│
├── docs/                      # Technical Documentation
│   ├── architecture.md        # Architectural breakdown & layer specification
│   ├── evaluation.md          # Evaluation methodology & benchmark metrics
│   └── security.md            # Security controls & boundary enforcement
│
├── skills/
│   └── repository-investigator/  # Portable Agent Skill package (Agent Skills standard)
│       ├── SKILL.md
│       └── references/
│
├── tests/                     # 100% Offline Test Suite
│   ├── fixtures/fixture_repo/ # Deterministic evaluation codebase
│   ├── test_evaluation.py     # Stage 8 deterministic evaluation dataset
│   ├── test_failure_cases.py  # Stage 8 failure-case resilience suite
│   ├── test_evidence_integrity.py # Stage 8 evidence integrity suite
│   ├── test_agent.py          # Stage 3 agent loop tests
│   ├── test_analysis.py       # Stage 6 AST analyzer tests
│   ├── test_indexing.py       # Stage 4 chunking & vector store tests
│   ├── test_repository.py     # Stage 2 repository workspace tests
│   ├── test_skills.py         # Stage 5 internal skills tests
│   └── test_tools.py          # Stage 2 safe file tools tests
│
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

---

## Setup Instructions

### 1. Clone the repository
```powershell
git clone https://github.com/your-username/RepoPilot.git
cd RepoPilot
```

### 2. Create and activate virtual environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables (Optional for live LLM mode)
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Edit `.env` to set your `GEMMA_API_KEY` and `GEMMA_MODEL`.

---

## Running the Demo CLI

Execute an investigation against the deterministic fixture repository:

```powershell
python backend/main.py
```

The CLI works **100% offline** if `GEMMA_API_KEY` is omitted, demonstrating tool execution, evidence collection, and grounded final synthesis.

---

## Running Tests & Evaluation Suite

Run the full offline test suite (all 145+ tests):

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

To run individual evaluation suites:
```powershell
python -m unittest tests/test_evaluation.py -v
python -m unittest tests/test_failure_cases.py -v
python -m unittest tests/test_evidence_integrity.py -v
```

---

## Security Policy

- RepoPilot is strictly **read-only**; code is never executed (`eval`, `exec`, `subprocess` forbidden).
- Filesystem boundary enforcement (`resolve_safe_path`) prevents path traversal attacks outside the target repository.
- Secrets (`GEMMA_API_KEY`) are excluded via `.gitignore` and redacted from logs.
- Detailed security documentation is available in [docs/security.md](docs/security.md).

---

## License

RepoPilot is released under the [MIT License](LICENSE).
