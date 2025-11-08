"""
bookbot/models.py

Pydantic models for BookBot API and internal DTOs.
"""

from typing import Optional, List
from pydantic import BaseModel


class Book(BaseModel):
    id: int
    title: str
    authors: List[str] = []
    description: Optional[str] = None
    tags: List[str] = []
    popularity: int = 0  # simple popularity metric


class UserAction(BaseModel):
    user_id: str
    book_id: int
    action: str  # 'like' | 'read'


class Recommendation(BaseModel):
    book_id: int
    score: float
