# Code Flow Analysis

This reference provides procedures for tracing execution flows, call hierarchies, and import dependencies across codebase components.

---

## 1. Tracing Call Hierarchies

When investigating request flows or execution chains:

### Downstream Tracing (What does X call?)
1. Identify the entry function definition (e.g. `login_handler`).
2. Read the function body to locate function/method calls (e.g. `auth_service.login`).
3. Follow called functions downstream up to a reasonable depth (typically 3 to 5 levels).
4. Verify each call target against actual source definitions.

### Upstream Tracing (What calls X?)
1. Identify target function definition (e.g. `verify_token`).
2. Search AST call sites or references for invocations of `verify_token`.
3. Follow calling functions upstream to discover route entry points or triggers.

---

## 2. Handling Cycles & Recursion

When tracing call flows in complex or recursive codebases:
- Maintain a set of visited symbol identifiers to detect cycles.
- If symbol $A$ calls $B$ and $B$ calls $A$, mark the cycle explicitly in the flow trace:
  `A -> B -> A (cycle detected; stopping recursion)`.
- Do not enter infinite traversal loops.

---

## 3. Handling Dynamic & Unresolved Relationships

Static analysis and source reading cannot always resolve 100% of runtime calls:
- **Dynamic Dispatch / Polymorphism:** When a method call (e.g. `handler.process()`) could target multiple interface implementations, list candidate implementation classes and mark resolution as **ambiguous**.
- **External Dependencies:** Calls into third-party libraries or standard library modules (e.g. `json.loads` or `requests.get`) should be marked as **external**.
- **Metaprogramming / Reflection:** Explicitly label dynamic imports or reflection as **unresolved**.

---

## 4. Representing Request Flow Chains

Format discovered call chains clearly using directional arrows and file citations:

```text
Request Flow Chain:
[Route Entry] handle_post_login() (backend/api/routes.py:12-25)
    ↓ calls
[Service Layer] authenticate_user() (backend/services/auth_service.py:40-62)
    ↓ calls
[Repository Layer] find_user_by_email() (backend/database/user_repo.py:18-30)
```
