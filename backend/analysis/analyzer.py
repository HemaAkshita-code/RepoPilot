"""
Python AST Analyzer implementation for RepoPilot (Person 1 Stage 6).
Performs static Python AST analysis to extract symbols, definitions, imports, calls, and inheritance.
No dynamic execution, eval, exec, or subprocess calls.
"""

import ast
from typing import Any, Dict, List, Optional, Tuple

from .models import Relationship, Symbol


class PythonASTVisitor(ast.NodeVisitor):
    """
    AST Visitor to discover symbols and relationships within a single Python file.
    """

    def __init__(self, file_path: str, content_lines_count: int):
        self.file_path = file_path
        self.content_lines_count = max(content_lines_count, 1)

        self.symbols: List[Symbol] = []
        self.relationships: List[Relationship] = []
        self.parse_error: Optional[str] = None

        # Stack to track enclosing parent symbol IDs and scopes
        self._scope_stack: List[Tuple[str, str]] = []  # List of (symbol_id, symbol_type)

        # Create module symbol
        module_id = file_path
        mod_name = file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        self.module_symbol = Symbol(
            symbol_id=module_id,
            name=mod_name,
            symbol_type="module",
            file_path=file_path,
            start_line=1,
            end_line=self.content_lines_count,
            parent_symbol=None,
            language="python",
        )
        self.symbols.append(self.module_symbol)
        self._scope_stack.append((module_id, "module"))

    @property
    def current_parent_id(self) -> str:
        """Returns the symbol ID of the current enclosing scope."""
        return self._scope_stack[-1][0] if self._scope_stack else self.file_path

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Process class definition and inheritance."""
        start_line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", start_line)

        parent_id = self.current_parent_id
        class_id = f"{self.file_path}::{node.name}"

        docstring = ast.get_docstring(node)

        class_symbol = Symbol(
            symbol_id=class_id,
            name=node.name,
            symbol_type="class",
            file_path=self.file_path,
            start_line=start_line,
            end_line=end_line,
            parent_symbol=parent_id,
            language="python",
            docstring=docstring[:150] if docstring else None,
        )
        self.symbols.append(class_symbol)

        # Record contains relationship
        rel_id = f"contains::{parent_id}->{class_id}"
        self.relationships.append(Relationship(
            relationship_id=rel_id,
            relationship_type="contains",
            source=parent_id,
            target=class_id,
            evidence={"file_path": self.file_path, "start_line": start_line, "end_line": end_line},
            resolution_status="resolved",
        ))

        # Process inheritance
        for base in node.bases:
            base_name = self._get_node_name(base)
            if base_name:
                inherits_rel_id = f"inherits::{class_id}->{base_name}::{start_line}"
                self.relationships.append(Relationship(
                    relationship_id=inherits_rel_id,
                    relationship_type="inherits",
                    source=class_id,
                    target=base_name,
                    evidence={"file_path": self.file_path, "start_line": start_line, "end_line": start_line},
                    resolution_status="unresolved",  # To be resolved by indexer
                ))

        self._scope_stack.append((class_id, "class"))
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Process function or method definition."""
        self._handle_function_def(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Process async function or method definition."""
        self._handle_function_def(node)

    def _handle_function_def(self, node: Any) -> None:
        start_line = getattr(node, "lineno", 1)
        end_line = getattr(node, "end_lineno", start_line)

        parent_id, parent_type = self._scope_stack[-1] if self._scope_stack else (self.file_path, "module")
        symbol_type = "method" if parent_type == "class" else "function"

        if parent_type == "class":
            func_id = f"{parent_id}.{node.name}"
        else:
            func_id = f"{self.file_path}::{node.name}"

        # Extract parameter names signature summary
        arg_names = [arg.arg for arg in node.args.args]
        sig_str = f"def {node.name}({', '.join(arg_names)})"
        docstring = ast.get_docstring(node)

        func_symbol = Symbol(
            symbol_id=func_id,
            name=node.name,
            symbol_type=symbol_type,
            file_path=self.file_path,
            start_line=start_line,
            end_line=end_line,
            parent_symbol=parent_id,
            language="python",
            docstring=docstring[:150] if docstring else None,
            signature=sig_str,
        )
        self.symbols.append(func_symbol)

        # Record contains relationship
        rel_id = f"contains::{parent_id}->{func_id}"
        self.relationships.append(Relationship(
            relationship_id=rel_id,
            relationship_type="contains",
            source=parent_id,
            target=func_id,
            evidence={"file_path": self.file_path, "start_line": start_line, "end_line": end_line},
            resolution_status="resolved",
        ))

        self._scope_stack.append((func_id, symbol_type))
        self.generic_visit(node)
        self._scope_stack.pop()

    def visit_Import(self, node: ast.Import) -> None:
        """Process standard import statements (import foo, import bar.baz as b)."""
        line = getattr(node, "lineno", 1)
        for alias in node.names:
            mod_target = alias.name
            rel_id = f"imports::{self.file_path}->{mod_target}::{line}"
            self.relationships.append(Relationship(
                relationship_id=rel_id,
                relationship_type="imports",
                source=self.file_path,
                target=mod_target,
                evidence={"file_path": self.file_path, "start_line": line, "end_line": line},
                resolution_status="unresolved",
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Process from import statements (from foo.bar import baz)."""
        line = getattr(node, "lineno", 1)
        module_name = node.module or ""
        for alias in node.names:
            target_name = f"{module_name}.{alias.name}" if module_name else alias.name
            rel_id = f"imports::{self.file_path}->{target_name}::{line}"
            self.relationships.append(Relationship(
                relationship_id=rel_id,
                relationship_type="imports",
                source=self.file_path,
                target=target_name,
                evidence={"file_path": self.file_path, "start_line": line, "end_line": line},
                resolution_status="unresolved",
            ))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Process function and method calls."""
        line = getattr(node, "lineno", 1)
        caller_id = self.current_parent_id
        call_target = self._get_node_name(node.func)

        if call_target:
            rel_id = f"calls::{caller_id}->{call_target}::{line}"
            self.relationships.append(Relationship(
                relationship_id=rel_id,
                relationship_type="calls",
                source=caller_id,
                target=call_target,
                evidence={"file_path": self.file_path, "start_line": line, "end_line": line},
                resolution_status="unresolved",
            ))
        self.generic_visit(node)

    def _get_node_name(self, node: ast.AST) -> Optional[str]:
        """Extracts a simple textual string identifier from an AST expression node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val_name = self._get_node_name(node.value)
            if val_name:
                return f"{val_name}.{node.attr}"
            return node.attr
        elif isinstance(node, ast.Call):
            return self._get_node_name(node.func)
        return None


def parse_python_file(file_path: str, content: str) -> Tuple[List[Symbol], List[Relationship], Optional[str]]:
    """
    Statically parses a Python file's source text into symbols and relationships using standard library AST.

    Args:
        file_path: Repository-relative POSIX file path.
        content: Source code string.

    Returns:
        Tuple[List[Symbol], List[Relationship], Optional[str]]: Discovered symbols, relationships, and error message if any.
    """
    if not content or not content.strip():
        # Empty file handling
        mod_symbol = Symbol(
            symbol_id=file_path,
            name=file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0],
            symbol_type="module",
            file_path=file_path,
            start_line=1,
            end_line=1,
            language="python",
        )
        return [mod_symbol], [], None

    content_lines_count = len(content.splitlines())

    try:
        tree = ast.parse(content, filename=file_path)
    except (SyntaxError, UnicodeDecodeError, ValueError, Exception) as e:
        # Return fallback module symbol and parse error description
        mod_symbol = Symbol(
            symbol_id=file_path,
            name=file_path.rsplit("/", 1)[-1].rsplit(".", 1)[0],
            symbol_type="module",
            file_path=file_path,
            start_line=1,
            end_line=content_lines_count,
            language="python",
        )
        return [mod_symbol], [], f"AST parse error in '{file_path}': {e}"

    visitor = PythonASTVisitor(file_path, content_lines_count)
    visitor.visit(tree)
    return visitor.symbols, visitor.relationships, None
