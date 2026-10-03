# Investigation Methodology

This reference details the systematic strategies for exploring, searching, and scoping unfamiliar software repositories.

---

## 1. Scope Selection & Initial Exploration

Before searching or reading code, establish the structural scope of the repository:

- **Root Configuration Inspection:** Locate project definition files (`pyproject.toml`, `setup.py`, `package.json`, `Cargo.toml`, `go.mod`, `CMakeLists.txt`, `pom.xml`). These files reveal project dependencies, entry points, build targets, and sub-packages.
- **Directory Layout Mapping:** Identify primary source directories (`src/`, `lib/`, `backend/`, `app/`, `api/`), infrastructure/config folders (`config/`, `deploy/`, `docker/`), and test suites (`tests/`, `spec/`).
- **Documentation Review:** Read `README.md`, `ARCHITECTURE.md`, or API specs when available to form initial architectural hypotheses.

---

## 2. Search Strategy Matrix

Select search techniques based on query characteristics:

| Query Type | Primary Search Mechanism | Purpose | Action |
| --- | --- | --- | --- |
| **Exact Symbol / Function Name** | Keyword Search (`search_code`) | Locate exact declaration or invocation sites | Search for exact string literal e.g. `authenticate_user`. |
| **Route / Endpoint Path** | Keyword Search (`search_code`) | Locate URL route handlers | Search for path string or decorator e.g. `/api/v1/login` or `@app.post`. |
| **Configuration Key** | Keyword Search (`search_code`) | Locate config usage | Search for environment variable or key e.g. `DATABASE_URL`. |
| **High-Level Concept / Feature** | Semantic Retrieval (`search_repository`) | Discover relevant modules when naming is unknown | Run vector query e.g. "JWT token validation middleware". |
| **Unfamiliar Subsystem** | Structural Analysis / File List | Map subsystem boundary | List directory files and inspect module entry points. |

---

## 3. Disambiguating Multiple Symbol Definitions

When multiple files define functions or classes with identical names (e.g. `handle_request` or `User`):
1. **Do not arbitrarily pick one.**
2. Inspect import statements in calling files to identify which module is imported.
3. Compare class or namespace prefixes.
4. Report all matching candidates if static resolution remains ambiguous.

---

## 4. Stopping Conditions

Conclude an investigation turn when:
- The exact answer to the user's question has been verified against source code.
- Source citations covering the relevant line ranges have been recorded.
- Remaining uninspected candidate files are redundant or irrelevant to the core inquiry.
