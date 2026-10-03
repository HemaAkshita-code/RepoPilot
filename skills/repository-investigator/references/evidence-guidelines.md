# Evidence & Provenance Guidelines

This reference defines rules for recording, classifying, and formatting evidence gathered during repository investigations.

---

## 1. Classification of Evidence

To maintain rigorous grounding, classify all investigation findings into three explicit tiers:

### Tier 1: Directly Inspected Fact (Verified)
- **Definition:** Information extracted directly from reading source file text or AST structural analysis.
- **Example:** "`authenticate_user()` is defined in `backend/auth.py:42-58` and accepts `(username, password)` arguments."
- **Requirement:** Must include exact file path and 1-indexed line range.

### Tier 2: Observed Relationship / Candidate (Discovered)
- **Definition:** Information discovered via search results or semantic retrieval that indicates a candidate location.
- **Example:** "Keyword search found 3 occurrences of `token` in `backend/middleware/auth.py`."
- **Requirement:** Treat as unconfirmed until verified by source reading.

### Tier 3: Architectural Inference (Deduction)
- **Definition:** Deduction or hypothesis formed by combining observed facts with software design patterns.
- **Example:** "`backend/auth.py` appears to serve as the primary security boundary for API routes."
- **Requirement:** Must be explicitly labeled as an inference, deduction, or hypothesis. Never state an inference as a verified fact.

---

## 2. Citation Format Standard

All file citations in final answers and investigation logs must adhere to the standard format:

- **Single Line Citation:** `relative/path/to/file.ext:42`
- **Line Range Citation:** `relative/path/to/file.ext:42-58`
- **Whole File Citation:** `relative/path/to/file.ext` (use only when referencing whole file assets like `pyproject.toml`).

---

## 3. Evidence Rules

1. **No Line Fabrication:** Never invent or estimate line numbers. If exact line numbers are unavailable, cite the relative file path.
2. **Path Normalization:** Always use POSIX relative paths with forward slashes (`/`), even on Windows environments (`backend/api/routes.py`).
3. **No Phantom Files:** Never cite files or functions that have not been observed in tool output.
4. **Provenance Tracking:** Retain the path and line range for every cited code snippet.
