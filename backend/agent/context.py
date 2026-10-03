"""
Structured investigation context and evidence classification for RepoPilot Stage 4.
Distinguishes between retrieved chunks (RAG) and directly inspected files/search matches.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EvidenceItem:
    """
    Represents a piece of evidence gathered during repository investigation.

    Attributes:
        path: Repository-relative POSIX file path.
        start_line: 1-indexed starting line number if available.
        end_line: 1-indexed ending line number if available.
        evidence_type: Type of evidence ("retrieved_chunk", "inspected_file", or "search_match").
        snippet: Content or snippet of the evidence.
        score: Optional relevance score.
    """
    path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    evidence_type: str = "retrieved_chunk"
    snippet: str = ""
    score: Optional[float] = None

    @property
    def source_location(self) -> str:
        """Returns formatted citation location string, e.g. 'backend/auth.py:1-40'."""
        if self.start_line is not None and self.end_line is not None:
            return f"{self.path}:{self.start_line}-{self.end_line}"
        return self.path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "evidence_type": self.evidence_type,
            "snippet": self.snippet,
            "score": self.score,
            "source_location": self.source_location,
        }


@dataclass
class InvestigationContext:
    """
    Maintains structured investigation evidence distinguishing between
    retrieved RAG chunks and directly inspected files.
    """
    retrieved_chunks: List[EvidenceItem] = field(default_factory=list)
    inspected_files: List[EvidenceItem] = field(default_factory=list)
    search_matches: List[EvidenceItem] = field(default_factory=list)

    def add_retrieved_chunk(self, path: str, start_line: int, end_line: int, snippet: str, score: float) -> None:
        item = EvidenceItem(
            path=path,
            start_line=start_line,
            end_line=end_line,
            evidence_type="retrieved_chunk",
            snippet=snippet,
            score=score,
        )
        self.retrieved_chunks.append(item)

    def add_inspected_file(self, path: str, snippet: str = "") -> None:
        item = EvidenceItem(
            path=path,
            evidence_type="inspected_file",
            snippet=snippet,
        )
        self.inspected_files.append(item)

    def add_search_match(self, path: str, line: int, snippet: str) -> None:
        item = EvidenceItem(
            path=path,
            start_line=line,
            end_line=line,
            evidence_type="search_match",
            snippet=snippet,
        )
        self.search_matches.append(item)

    def get_all_source_locations(self) -> List[str]:
        """Returns deduplicated list of all source locations cited."""
        locs: List[str] = []
        for item in self.inspected_files + self.retrieved_chunks + self.search_matches:
            loc = item.source_location
            if loc not in locs:
                locs.append(loc)
        return locs

    def format_retrieved_context_for_prompt(self, max_items: int = 5) -> str:
        """Formats compact retrieved chunks for model prompt injection."""
        if not self.retrieved_chunks:
            return ""

        lines = ["[Retrieved Repository Context]"]
        for item in self.retrieved_chunks[:max_items]:
            score_str = f" (Score: {item.score:.2f})" if item.score is not None else ""
            lines.append(f"Source: {item.source_location}{score_str}")
            lines.append("```")
            lines.append(item.snippet)
            lines.append("```\n")

        return "\n".join(lines)
