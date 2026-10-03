# RepoPilot Architecture Specification

RepoPilot is an open-source AI agent system built around **Gemma 4** for investigating, analyzing, and understanding software codebases.

---

## High-Level Architectural Overview

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

## Architectural Layers

### 1. Repository Management & Exploration Tools (`backend/repository/` & `backend/tools/`)
- **`load_local_repository` & `load_github_repository`**: Ingests local codebases or clones public GitHub repositories into isolated, controlled workspace directories.
- **`list_files`**: Lists repository-relative file paths while enforcing `.gitignore` rules and excluding binary/system directories.
- **`read_file`**: Reads text files safely with automatic length truncation, line offset support, binary file detection, and strict path traversal protection.
- **`search_code`**: Performs deterministic regex and keyword string searching across source files.

### 2. Semantic RAG & Vector Retrieval (`backend/indexing/`)
- **`CodeChunk`**: Chunks source files deterministically by logical code boundaries (classes, functions, header blocks).
- **`InMemoryVectorStore`**: Stores chunk embeddings and computes cosine similarity ranking.
- **`RepositoryIndexer`**: Manages codebase chunking and vector index generation.
- **`RepositoryRetriever` & `search_repository`**: Exposes semantic similarity search as a model-callable tool.

### 3. Structural Code Analysis Engine (`backend/analysis/`)
- **`parse_python_file`**: Statically analyzes Python source text using standard library AST parsing without code execution.
- **`StructuralIndex`**: Maintains an in-memory graph of symbols (`Symbol`), cross-file call sites, imports, and inheritance (`Relationship`). Detects index staleness using cryptographic file fingerprints.
- **Structural Tools**:
  - `find_symbol`: Locates symbol definitions by name.
  - `find_references`: Gathers definitions, AST call sites, and code occurrences.
  - `get_symbol_relationships`: Retrieves incoming and outgoing call/import links.
  - `trace_call_flow`: Recursively traces upstream callers or downstream called functions with cycle detection and depth bounding.
  - `get_file_dependencies`: Analyzes import dependencies and reverse dependency references.

### 4. Agent Execution Loop & Evidence Context (`backend/agent/`)
- **`ToolRegistry`**: Central registry storing model-callable tools with schema generation and argument type validation.
- **`RepoPilotAgent`**: Core agent loop interfacing with Gemma 4, enforcing step limits (`max_iterations`), handling tool execution errors, and orchestrating multi-step investigations.
- **`InvestigationContext` & `EvidenceItem`**: Tracks evidence provenance, distinguishing between retrieved semantic candidate chunks, inspected source files, search matches, and structural AST relations.

---

## Internal Skills vs. Portable Agent Skill Package

RepoPilot maintains a strict architectural distinction between internal Python skills and its portable open-standard Agent Skill:

| Aspect | Internal Skills (`backend/skills/`) | Portable Agent Skill (`skills/repository-investigator/`) |
| :--- | :--- | :--- |
| **Purpose** | Native Python workflows executed by RepoPilot backend (`ArchitectureSkill`, `AuthSkill`, `APIFlowSkill`). | Specification-compliant Agent Skill package enforcing investigation methodology for external AI agents. |
| **Interface** | Python classes inheriting from `BaseSkill` managed by `SkillManager`. | `SKILL.md` markdown file with standard YAML frontmatter and progressive disclosure references in `references/`. |
| **Dependencies** | Requires RepoPilot backend Python code. | Agent/LLM-agnostic; requires no Python runtime dependencies. |
