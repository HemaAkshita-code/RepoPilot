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

    def execute(self, tool_name: str, args: Dict[str, Any]) -> ToolResult:
        """
        Safely executes a registered tool, injecting the repository context.

        Args:
            tool_name: The name of the tool.
            args: Model-provided keyword arguments (without repo_root).

        Returns:
            ToolResult: Structured outcome of the tool execution.
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

        try:
            raw_result = func(**call_kwargs)

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
