# RepoPilot Security & Boundary Model

This document outlines the security controls, boundary enforcement mechanisms, secret protection practices, and known security limits of RepoPilot.

---

## 1. Filesystem Security & Workspace Isolation

RepoPilot strictly enforces filesystem boundaries for all tools (`read_file`, `list_files`, `search_code`, `get_file_dependencies`):

- **Path Boundary Resolution (`resolve_safe_path`)**: All user- or model-supplied paths are resolved against the active `Repository.root_path`.
- **Directory Traversal Protection**: Any path containing `..` or attempting to dereference outside the repository root raises a `SecurityBoundaryError`.
- **Symlink Escape Protection**: Symlinks pointing outside the repository workspace boundary are rejected or ignored.
- **Model Isolation**: Models cannot pass arbitrary `repo_root` arguments to override the repository boundary established by the application.

---

## 2. Execution Policy (Read-Only Safety)

RepoPilot operates as a non-destructive, read-only repository investigator:

- **No Code Execution**: RepoPilot **never** invokes `eval()`, `exec()`, or Python `import` on repository code.
- **No Arbitrary Subprocess Spawning**: Model arguments cannot execute shell commands or operating system executables.
- **AST Static Analysis**: Python code structure is analyzed purely via standard library AST parsing (`ast.parse`).

---

## 3. Tool Registry & Model Input Validation

- **Registry Boundary**: The model can only execute tools explicitly registered in the `ToolRegistry`. Unregistered tool names return an immediate error.
- **Argument Type Validation**: Tool arguments are validated against predefined type schemas before execution.
- **Sanitized Outputs**: Error messages from failed tool calls return structured JSON errors to the model rather than exposing system stack traces.

---

## 4. Secret & Credential Handling

- **Environment Variable Isolation**: Secret keys (such as `GEMMA_API_KEY`) are read strictly from environment variables or `.env`.
- **Git Protection**: `.env` is listed in `.gitignore` and is never tracked in version control.
- **Credential Redacting**: API credentials are never logged, printed to terminal output, or included in evidence citations.

---

## 5. Security Limitations & Known Risks

- **Untrusted Repositories**: While RepoPilot does not execute repository code, malicious repositories containing extremely large generated files or infinite symlink structures can increase memory consumption.
- **Model Output Control**: RepoPilot sanitizes tool call arguments, but model final answers should be treated as informative output and verified against source citations.
- **AST Analysis Bounds**: Dynamic dispatch (e.g. `getattr(obj, var)()`) cannot be statically resolved and is explicitly marked as `unresolved` or `ambiguous`.
