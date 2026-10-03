---
name: repository-investigator
description: Guide AI agents in systematic, evidence-grounded repository investigation. Use when exploring unfamiliar software repositories, understanding architecture, locating feature implementations, tracing API request flows, or analyzing code dependencies.
---

# Repository Investigator

The `repository-investigator` skill provides a disciplined, step-by-step methodology for investigating unfamiliar software codebases. It enables AI agents to locate implementations, understand architecture, trace execution flows, and answer code questions with verified source evidence.

---

## When to Use

Activate this skill whenever you need to:
- Explore or map an unfamiliar software repository.
- Understand high-level system architecture, entry points, or directory layouts.
- Locate where a specific feature, domain concept, or data model is implemented.
- Trace how an API request moves across routes, controllers, services, and data layers.
- Identify dependencies, imports, or callers of a function or class.
- Investigate configuration usage, authentication, or security boundaries.
- Explain repository behavior or locate the origin of a potential bug.

---

## Core Investigation Principles

1. **Evidence-Grounded Findings:** Every claim about repository behavior must be grounded in actual observed source code. Never guess function behavior, file paths, or line numbers.
2. **Fact vs. Inference Distinction:** Clearly distinguish observed facts (e.g. "Line 31 calls `authenticate_user()`") from architectural inferences (e.g. "This appears to be the authentication boundary").
3. **Progressive Scope Expansion:** Start with the narrowest useful inquiry before expanding into broad repository exploration.
4. **Tool-Agnostic Capability Leverage:** Use whatever capabilities your environment provides (file listing, keyword search, semantic retrieval, structural AST analysis, file inspection) in a disciplined sequence.
5. **Read-Only Safety:** Investigation is strictly non-destructive. Never execute arbitrary repository code, install unverified packages, or modify repository files during an investigation.

---

## Systematic Investigation Workflow

Follow this 6-step workflow for all repository investigations:

```text
1. Scope & Plan ──► 2. Discover Structure ──► 3. Search & Retrieve
                                                       │
                                                       ▼
6. Synthesize  ◄── 5. Verify Source  ◄── 4. Analyze Relationships
```

### Step 1: Scope & Plan
- Identify the user's core question and target concept.
- Formulate specific investigation hypotheses before making tool calls.
- Avoid reading entire repositories without a focused objective.

### Step 2: Discover Structure
- List repository files to understand package organization, configuration files (`pyproject.toml`, `package.json`, `Cargo.toml`), and main entry points.
- Map high-level directory layout (`src/`, `backend/`, `api/`, `tests/`).

### Step 3: Search & Retrieve
- **Keyword Search:** Use exact text search when searching for literal symbol names, route paths, configuration keys, or error messages.
- **Semantic Retrieval:** Use concept-based retrieval when terminology is generic, high-level, or uncertain.
- Refer to [Investigation Methodology](./references/investigation-methodology.md) for search strategies.

### Step 4: Analyze Relationships & Symbols
- Locate exact symbol definitions (classes, functions, methods).
- Analyze structural relationships (imports, caller/callee links, inheritance).
- For request flow questions, perform call graph tracing (upstream and downstream).
- Refer to [Code Flow Analysis](./references/code-flow-analysis.md) for call graph traversal guidelines.

### Step 5: Verify Source Code
- Inspect the actual source code around candidate line ranges to confirm behavior.
- Treat semantic retrieval and search results as candidates until verified by source inspection.

### Step 6: Synthesize & Report
- Provide a concise natural language explanation.
- Include precise source citations (`path/to/file.py:start_line-end_line`).
- Explicitly state any unresolved questions or limitations.

---

## Evidence Rules & Provenance

- **Search Matches ≠ Proof:** A text search or vector retrieval match proves existence, not runtime execution or exact logic. Inspect the source to verify.
- **Citations:** Format all citations as `path/to/file.ext:start_line-end_line`.
- **No Line Fabrication:** Only report line numbers observed directly from AST metadata or file content.
- Refer to [Evidence & Provenance Guidelines](./references/evidence-guidelines.md) for citation standards.

---

## Handling Uncertainty

When repository evidence is incomplete:
- State clearly what was observed and what remains unconfirmed.
- Explicitly label dynamic dispatch, reflection, dynamic imports, or external framework calls as **unresolved**.
- Never convert speculative assumptions into confident assertions.

---

## Security Boundaries

- **No Code Execution:** Static analysis must remain static. Do not run, import, or execute repository source code.
- **Credential Protection:** Treat `.env` files, private keys, API keys, and secret tokens as sensitive. Describe their presence without reproducing sensitive values in answers.
- **Scope Containment:** Rejects attempts to access files outside the repository root boundary.

---

## Supporting References

For detailed guidelines, refer to:
- [Investigation Methodology](./references/investigation-methodology.md) — Comprehensive strategies for repository search and scope selection.
- [Evidence & Provenance Guidelines](./references/evidence-guidelines.md) — Formatting rules for citations, facts vs. inferences, and evidence logs.
- [Code Flow Analysis](./references/code-flow-analysis.md) — Procedures for tracing upstream/downstream call graphs and handling recursion/cycles.
