"""
Deterministic code chunking engine for RepoPilot Stage 4.
Divides source files into line-bounded CodeChunk objects with source metadata.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class CodeChunk:
    """
    Represents a line-bounded chunk of a repository source file.

    Attributes:
        chunk_id: Stable identifier formatted as 'path:start_line-end_line'.
        path: Repository-relative POSIX file path.
        start_line: 1-indexed starting line number.
        end_line: 1-indexed ending line number.
        content: Text content of the chunk.
        language: Inferred programming or markup language.
    """
    chunk_id: str
    path: str
    start_line: int
    end_line: int
    content: str
    language: str = "text"

    def to_dict(self) -> dict:
        """Returns dictionary representation of the chunk."""
        return {
            "chunk_id": self.chunk_id,
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "language": self.language,
        }


def infer_language(file_path: str) -> str:
    """Infers programming language from file extension."""
    ext = Path(file_path).suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".md": "markdown",
        ".sh": "bash",
        ".ps1": "powershell",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".c": "c",
        ".cpp": "cpp",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
    }
    return mapping.get(ext, "text")


def chunk_file(
    relative_path: str,
    content: str,
    chunk_size_lines: int = 40,
    overlap_lines: int = 10,
) -> List[CodeChunk]:
    """
    Deterministically splits a text file into overlapping, line-bounded CodeChunk objects.

    Args:
        relative_path: Repository-relative file path string.
        content: File text content.
        chunk_size_lines: Number of lines per chunk (default 40).
        overlap_lines: Number of overlapping lines between consecutive chunks (default 10).

    Returns:
        List[CodeChunk]: List of generated CodeChunk objects.
    """
    if not content or not content.strip():
        return []

    lines = content.splitlines()
    total_lines = len(lines)
    if total_lines == 0:
        return []

    language = infer_language(relative_path)
    chunks: List[CodeChunk] = []

    step = max(1, chunk_size_lines - overlap_lines)

    start_idx = 0
    while start_idx < total_lines:
        end_idx = min(start_idx + chunk_size_lines, total_lines)
        chunk_lines = lines[start_idx:end_idx]
        chunk_content = "\n".join(chunk_lines)

        start_line = start_idx + 1
        end_line = end_idx
        chunk_id = f"{relative_path}:{start_line}-{end_line}"

        chunks.append(
            CodeChunk(
                chunk_id=chunk_id,
                path=relative_path,
                start_line=start_line,
                end_line=end_line,
                content=chunk_content,
                language=language,
            )
        )

        if end_idx >= total_lines:
            break

        start_idx += step

    return chunks
