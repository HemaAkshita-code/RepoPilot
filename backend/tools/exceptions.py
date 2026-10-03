"""
Custom exceptions for repository investigation tools.
"""

class ToolError(Exception):
    """Base exception for all investigation tool errors."""
    pass


class PathTraversalError(ToolError):
    """Raised when a path traversal attempt is detected."""
    pass


class FileAccessError(ToolError):
    """Raised when a file cannot be read or accessed."""
    pass
