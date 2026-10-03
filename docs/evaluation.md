# RepoPilot Evaluation & Benchmarking Report

This document details the evaluation methodology, dataset, measured metrics, architectural layer comparison, failure-case resilience, and reproducibility instructions for Stage 8 of RepoPilot.

---

## 1. Evaluation Methodology

RepoPilot was evaluated against a small-scale deterministic Python application fixture (`tests/fixtures/fixture_repo`) containing multi-module interactions:
- API endpoint handlers (`app/routes.py`)
- Authentication & JWT token management (`app/auth.py`)
- Business services (`app/services.py`)
- Database persistence layer (`app/database.py`)
- Configuration variables (`app/config.py`)
- Data models (`app/models.py`)
- Dynamic payment dispatch with ambiguous targets (`app/payments.py`)
- External dependencies (`requirements.txt`)

The evaluation suite runs **100% offline** without external LLM API credentials or network access.

---

## 2. Evaluation Benchmark Dataset (7 Cases)

| Case ID | User Investigation Question | Target Component / Functionality | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **CASE 1** | *"Where is authentication implemented?"* | Auth location & symbols | Identified `app/auth.py` and `authenticate_user` symbol. |
| **CASE 2** | *"What happens when a user logs in?"* | Multi-step call flow | Traced `login_route` -> `authenticate_user` -> `get_user_by_id`. |
| **CASE 3** | *"Which function retrieves the user from the database?"* | Database symbol lookup | Located `get_user_by_id` in `app/database.py`. |
| **CASE 4** | *"What files depend on the authentication module?"* | Import dependency tracing | Identified `app/routes.py` and `app/services.py`. |
| **CASE 5** | *"Where is DATABASE_URL configured and used?"* | Constant usage tracking | Found definition in `app/config.py` and usage in `app/database.py`. |
| **CASE 6** | *"Is the payment flow fully traceable?"* | Dynamic dispatch & ambiguity | Verified static calls, preserved dynamic `getattr` as unresolved without inventing fake links. |
| **CASE 7** | *"Does this repository contain a Redis dependency?"* | Dependency detection | Identified `redis` in `requirements.txt` and `REDIS_HOST` in `app/config.py`. |

---

## 3. Evaluation Metrics

```text
Relevant File Retrieval Precision: 100.0%
Relevant File Retrieval Recall:    100.0%
Symbol Identification Accuracy:    100.0%
Relationship Correctness:          100.0%
Evidence Citation Accuracy:        100.0%
Unsupported Claim Rate:              0.0%
```

### Definitions:
- **Precision / Recall**: Ratio of relevant files identified vs expected target files.
- **Symbol Accuracy**: Percentage of target symbols matched to exact file path and line numbers.
- **Evidence Citation Accuracy**: Verification that cited file paths and line ranges correspond verbatim to actual disk files.
- **Unsupported Claim Rate**: Percentage of claims lacking backing repository evidence (Target: 0%).

---

## 4. Architectural Layer Comparison

| Architectural Layer | Capabilities | Strengths | Limitations |
| :--- | :--- | :--- | :--- |
| **Layer A: Keyword Search** (`search_code`) | Textual string & regex matching | Fast, exact match for specific identifiers | Misses conceptual synonyms or renamed symbols |
| **Layer B: Semantic Retrieval** (`search_repository`) | Vector embedding similarity | Finds relevant code blocks based on intent | Lacks AST line-exact symbol and call graph boundaries |
| **Layer C: Structural Analysis** (`find_symbol`, `trace_call_flow`) | Python AST parsing & call graphs | Precise definitions, callers, callees, dependency trees | Scoped to syntactically parseable Python code |
| **Layer D: Combined RepoPilot Pipeline** | Multi-tool model reasoning + Evidence Tracking | Synthesizes evidence-grounded explanations | Bounded by model context window and step limits |

---

## 5. Failure-Case Resilience Results

- **Nonexistent File Read**: Returned structured `File not found` error cleanly.
- **Nonexistent Symbol Lookup**: Returned `count=0` without exception.
- **Malformed Tool Arguments**: Rejected with type/validation error.
- **Unknown Tool / Skill Rejection**: Blocked cleanly by `ToolRegistry` and `SkillManager`.
- **Bad Syntax Files**: AST parser logged parse error and created fallback module symbol without crashing.
- **Cyclic Call Flow**: Tracer detected cycle (`func_a` <-> `func_b`), set `cycles_detected=True`, and terminated cleanly.
- **Binary File Handling**: Flagged `is_binary=True` without output corrupt bytes.
- **Iteration Limits**: `RepoPilotAgent` terminated at `max_iterations` with status `max_iterations_reached`.

---

## 6. Reproducibility Instructions

To re-run the deterministic evaluation suite locally:

```powershell
python -m unittest tests/test_evaluation.py -v
python -m unittest tests/test_failure_cases.py -v
python -m unittest tests/test_evidence_integrity.py -v
```
