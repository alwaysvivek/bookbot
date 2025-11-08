from typing import Optional, List
from pydantic import BaseModel

class Book(BaseModel):
    id: int
    title: str
    authors: List[str] = []
    description: Optional[str] = None
    tags: List[str] = []
    popularity: int = 0

class UserAction(BaseModel):
    user_id: str
    book_id: int
    action: str

class Recommendation(BaseModel):
    book_id: int
    score: float
