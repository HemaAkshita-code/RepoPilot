"""Data Models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """User entity definition."""
    id: int
    username: str
    is_active: bool = True


@dataclass
class Token:
    """Auth token entity."""
    token: str
    user_id: int


@dataclass
class PaymentRequest:
    """Payment request DTO."""
    token: str
    amount: float
    currency: str = "USD"
