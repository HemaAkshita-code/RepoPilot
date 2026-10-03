"""
Central Tool Registry and Adapter for RepoPilot (Person 2 Stage 3 & Stage 4).
Injects repository context into Stage 2 & Stage 4 tools and exposes clean model schemas.
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from backend.repository.models import Repository
from backend.tools import list_files, read_file, search_code
from backend.indexing.indexer import RepositoryIndexer
from .retrieval import RepositoryRetriever
from .models import ToolResult


class ToolRegistry:
    """
    Central registry for RepoPilot tools.
    Provides model-facing schemas, argument validation, and repository context injection.
    """

    def __init__(
        self,
        repository: Union[str, Path, Repository],
        indexer: Optional[RepositoryIndexer] = None,
        retriever: Optional[RepositoryRetriever] = None,
    ):
        if isinstance(repository, Repository):
            self._repo = repository
            self._repo_root = repository.root_path
        else:
            self._repo = Repository(root_path=repository)
            self._repo_root = self._repo.root_path

        if retriever is not None:
            self._retriever = retriever
            self._indexer = retriever.indexer
        elif indexer is not None:
            self._indexer = indexer
            self._retriever = RepositoryRetriever(indexer)
        else:
            self._indexer = RepositoryIndexer(self._repo)
            self._retriever = RepositoryRetriever(self._indexer)

        self._tools: Dict[str, Dict[str, Any]] = {}
        self._register_default_tools()

    @property
    def repository(self) -> Repository:
        """Returns the associated Repository object."""
        return self._repo

    @property
    def repo_root(self) -> Path:
        """Returns the repository root path."""
        return self._repo_root

    @property
    def retriever(self) -> RepositoryRetriever:
        """Returns the attached RepositoryRetriever."""
        return self._retriever

    def _register_default_tools(self) -> None:
        """Registers the standard Stage 2 and Stage 4 repository tools."""
        self.register(
            name="list_files",
            func=list_files,
            description="Recursively list all repository-relative file paths in the codebase.",
            parameters={
                "type": "OBJECT",
                "properties": {},
                "required": [],
            },
            param_validators={},
        )

        self.register(
            name="read_file",
            func=read_file,
            description="Read the text content of a repository file given its repository-relative path.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "path": {
                        "type": "STRING",
                        "description": "Repository-relative path to the file (e.g. 'src/main.py').",
                    },
                },
                "required": ["path"],
            },
            param_validators={
                "path": lambda val: isinstance(val, str) and bool(val.strip()),
            },
        )

        self.register(
            name="search_code",
            func=search_code,
            description="Search repository source text files for occurrences of a text query string.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "Text query string to search for.",
                    },
                    "case_sensitive": {
                        "type": "BOOLEAN",
                        "description": "Optional boolean flag for case sensitivity (defaults to false).",
                    },
                },
                "required": ["query"],
            },
            param_validators={
                "query": lambda val: isinstance(val, str) and bool(val.strip()),
                "case_sensitive": lambda val: isinstance(val, bool),
            },
        )

        self.register(
            name="search_repository",
            func=self._search_repository_tool,
            description="Search the repository semantically using vector retrieval to find relevant code chunks.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "query": {
                        "type": "STRING",
                        "description": "Natural language query or keywords to search semantically across the repository.",
                    },
                    "top_k": {
                        "type": "INTEGER",
                        "description": "Optional maximum number of relevant chunks to retrieve (defaults to 5).",
                    },
                },
                "required": ["query"],
            },
            param_validators={
                "query": lambda val: isinstance(val, str) and bool(val.strip()),
                "top_k": lambda val: isinstance(val, int) and val > 0,
            },
        )

    def _search_repository_tool(self, query: str, top_k: int = 5, repo_root=None) -> Dict[str, Any]:
        """Internal adapter method for vector repository retrieval."""
        results = self._retriever.retrieve(query, top_k=top_k)
        chunks_data = [r.to_dict() for r in results]
        return {
            "query": query,
            "chunks": chunks_data,
            "count": len(chunks_data),
            "error": None,
        }

    def register_skill(self, skill: Any) -> None:
        """
        Registers an Agent Skill as a model-facing capability.
        Adapts the skill's execute method to match tool execution expectations.
        """
        def _skill_adapter(**kwargs):
            # Strip injected repo_root if present before passing kwargs to skill
            clean_kwargs = {k: v for k, v in kwargs.items() if k != "repo_root"}
            ctx = getattr(self, "_active_context", None)
            res = skill.execute(registry=self, context=ctx, **clean_kwargs)
            return res.to_dict()

        self.register(
            name=skill.name,
            func=_skill_adapter,
            description=skill.description,
            parameters=skill.parameters,
            param_validators=getattr(skill, "param_validators", {}),
        )

    def register_built_in_skills(self) -> None:
        """Registers all built-in Stage 5 Agent Skills into the registry."""
        from backend.skills import get_default_skill_manager
        manager = get_default_skill_manager()
        manager.register_skills_to_tool_registry(self)

    def register_structural_tools(self) -> None:
        """Registers Stage 6 Structural Analysis Tools into the registry."""
        from backend.analysis.tools import (
            find_symbol as find_symbol_fn,
            find_references as find_references_fn,
            get_symbol_relationships as get_symbol_relationships_fn,
            trace_call_flow as trace_call_flow_fn,
            get_file_dependencies as get_file_dependencies_fn,
        )

        self.register(
            name="find_symbol",
            func=find_symbol_fn,
            description="Find definitions of a symbol by name or identifier in the repository.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "symbol_name": {
                        "type": "STRING",
                        "description": "Symbol name or identifier (e.g. 'login' or 'backend/auth.py::login').",
                    },
                },
                "required": ["symbol_name"],
            },
            param_validators={
                "symbol_name": lambda val: isinstance(val, str) and bool(val.strip()),
            },
        )

        self.register(
            name="find_references",
            func=find_references_fn,
            description="Find references, AST call sites, and code occurrences of a symbol in the repository.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "symbol_name": {
                        "type": "STRING",
                        "description": "Symbol name or identifier to search references for.",
                    },
                },
                "required": ["symbol_name"],
            },
            param_validators={
                "symbol_name": lambda val: isinstance(val, str) and bool(val.strip()),
            },
        )

        self.register(
            name="get_symbol_relationships",
            func=get_symbol_relationships_fn,
            description="Retrieve incoming and outgoing structural relationships (calls, called_by, imports, inherits) for a symbol.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "symbol_name": {
                        "type": "STRING",
                        "description": "Symbol name or identifier.",
                    },
                },
                "required": ["symbol_name"],
            },
            param_validators={
                "symbol_name": lambda val: isinstance(val, str) and bool(val.strip()),
            },
        )

        self.register(
            name="trace_call_flow",
            func=trace_call_flow_fn,
            description="Trace bounded call hierarchy (upstream or downstream) starting from a symbol.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "symbol": {
                        "type": "STRING",
                        "description": "Starting symbol name or identifier (e.g. 'login').",
                    },
                    "direction": {
                        "type": "STRING",
                        "description": "Traversal direction: 'downstream' (called functions) or 'upstream' (calling functions).",
                    },
                    "depth": {
                        "type": "INTEGER",
                        "description": "Maximum call graph depth (defaults to 3, bounded 1 to 10).",
                    },
                },
                "required": ["symbol"],
            },
            param_validators={
                "symbol": lambda val: isinstance(val, str) and bool(val.strip()),
                "direction": lambda val: isinstance(val, str) and val.lower().strip() in ["downstream", "upstream"],
                "depth": lambda val: isinstance(val, int) and val > 0,
            },
        )

        self.register(
            name="get_file_dependencies",
            func=get_file_dependencies_fn,
            description="Get import dependencies for a specific repository file.",
            parameters={
                "type": "OBJECT",
                "properties": {
                    "file_path": {
                        "type": "STRING",
                        "description": "Repository-relative POSIX file path (e.g. 'backend/routes.py').",
                    },
                },
                "required": ["file_path"],
            },
            param_validators={
                "file_path": lambda val: isinstance(val, str) and bool(val.strip()),
            },
        )

    def register(
        self,
        name: str,
        func: Callable[..., Dict[str, Any]],
        description: str,
        parameters: Dict[str, Any],
        param_validators: Optional[Dict[str, Callable[[Any], bool]]] = None,
    ) -> None:
        """Registers a tool with model-facing metadata and validation functions."""
        self._tools[name] = {
            "name": name,
            "func": func,
            "description": description,
            "parameters": parameters,
            "param_validators": param_validators or {},
        }

    def list_tools(self) -> List[str]:
        """Returns a list of registered tool names."""
        return list(self._tools.keys())

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns the registration metadata for a specific tool name."""
        return self._tools.get(name)

    def get_model_tools(self) -> List[Dict[str, Any]]:
        """
        Returns model-facing tool declarations for LLM tool calling.
        Note: repo_root is NEVER included in model-facing parameters.
        """
        declarations = []
        for name, info in self._tools.items():
            declarations.append({
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"],
            })
        return declarations

    def validate_args(self, tool_name: str, args: Dict[str, Any]) -> Optional[str]:
        """
        Validates arguments for a tool call.

        Returns:
            Optional[str]: Error message if invalid, or None if arguments are valid.
        """
        if tool_name not in self._tools:
            return f"Unknown tool '{tool_name}'. Allowed tools are: {', '.join(self.list_tools())}"

        tool_info = self._tools[tool_name]
        params_schema = tool_info["parameters"]
        required_params = params_schema.get("required", [])
        allowed_props = params_schema.get("properties", {})
        validators = tool_info["param_validators"]

        # 1. Check for forbidden repo_root in model arguments
        if "repo_root" in args:
            return "Security violation: Model is not permitted to specify 'repo_root'."

        # 2. Check required parameters
        for req in required_params:
            if req not in args or args[req] is None:
                return f"Tool '{tool_name}' missing required argument '{req}'."

        # 3. Check for unexpected arguments
        for k in args:
            if k not in allowed_props:
                return f"Tool '{tool_name}' received unexpected argument '{k}'."

        # 4. Check type/value validators
        for k, v in args.items():
            if k in validators:
                try:
                    if not validators[k](v):
                        return f"Tool '{tool_name}' argument '{k}' has invalid type or value: {v!r}."
                except Exception as e:
                    return f"Validation error for '{k}': {e}"

        return None

    def execute(
        self,
        tool_name: str,
        args: Dict[str, Any],
        context: Optional[Any] = None,
    ) -> ToolResult:
        """
        Safely executes a registered tool or skill, injecting repository context.

        Args:
            tool_name: The name of the tool or skill.
            args: Model-provided keyword arguments (without repo_root).
            context: Optional InvestigationContext for evidence tracking.

        Returns:
            ToolResult: Structured outcome of the tool or skill execution.
        """
        validation_error = self.validate_args(tool_name, args)
        if validation_error:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                result={},
                error=validation_error,
            )

        tool_info = self._tools[tool_name]
        func = tool_info["func"]

        call_kwargs = dict(args)
        call_kwargs["repo_root"] = self._repo_root

        # Temporarily store active context for skill adapter access
        old_context = getattr(self, "_active_context", None)
        if context is not None:
            self._active_context = context

        try:
            raw_result = func(**call_kwargs)

            # Record atomic evidence into context if context was provided
            if context is not None and isinstance(raw_result, dict):
                self._record_tool_evidence(tool_name, raw_result, context)

            if isinstance(raw_result, dict) and raw_result.get("error"):
                return ToolResult(
                    success=False,
                    tool_name=tool_name,
                    result=raw_result,
                    error=raw_result["error"],
                )

            return ToolResult(
                success=True,
                tool_name=tool_name,
                result=raw_result,
                error=None,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                tool_name=tool_name,
                result={},
                error=f"Unexpected error executing '{tool_name}': {e}",
            )
        finally:
            self._active_context = old_context

    def _record_tool_evidence(
        self,
        tool_name: str,
        res: Dict[str, Any],
        context: Any,
    ) -> None:
        """Helper method to populate InvestigationContext from atomic and structural tool results."""
        if tool_name == "search_repository":
            chunks = res.get("chunks", [])
            for c in chunks:
                context.add_retrieved_chunk(
                    path=c.get("path", ""),
                    start_line=c.get("start_line", 1),
                    end_line=c.get("end_line", 1),
                    snippet=c.get("content", ""),
                    score=c.get("score", 0.0),
                )
        elif tool_name == "read_file":
            path = res.get("path")
            content = res.get("content", "")
            if path:
                context.add_inspected_file(path, content[:200])
        elif tool_name == "search_code":
            matches = res.get("matches", [])
            for m in matches:
                p = m.get("path")
                line = m.get("line", 1)
                snippet = m.get("snippet", "")
                if p:
                    context.add_search_match(p, line, snippet)
        elif tool_name in ["find_symbol", "find_references", "get_symbol_relationships", "trace_call_flow", "get_file_dependencies"]:
            if tool_name == "find_symbol":
                for sym in res.get("symbols", []):
                    p = sym.get("file_path")
                    start = sym.get("start_line")
                    end = sym.get("end_line")
                    if p:
                        context.add_structural_evidence(p, start, end, f"Symbol definition: {sym.get('name')}")
            elif tool_name == "find_references":
                for ref in res.get("ast_references", []):
                    ev = ref.get("evidence", {})
                    p = ev.get("file_path")
                    start = ev.get("start_line")
                    end = ev.get("end_line")
                    if p:
                        context.add_structural_evidence(p, start, end, f"AST Reference to {res.get('query')}")
            elif tool_name == "trace_call_flow":
                for node in res.get("nodes", []):
                    p = node.get("file_path")
                    start = node.get("start_line")
                    end = node.get("end_line")
                    if p:
                        context.add_structural_evidence(p, start, end, f"Call flow node: {node.get('name')}")

