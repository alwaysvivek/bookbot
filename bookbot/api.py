"""
bookbot/api.py

FastAPI application exposing:
- GET /recommendations
- POST /user/actions
- GET /search
- simple book management endpoints (add/list)
"""

from fastapi import FastAPI, HTTPException, Query
from typing import List
import asyncio
import logging
from .repository import BooksRepository, UserActionsRepository
from .recommender import Recommender
from .models import Book, UserAction, Recommendation
import os
from rapidfuzz import fuzz, process  # for fuzzy search

logger = logging.getLogger(__name__)

app = FastAPI(title="BookBot Recommender")

books_repo = BooksRepository()
actions_repo = UserActionsRepository()
recommender = Recommender(books_repo, actions_repo)


@app.on_event("startup")
async def startup():
    await books_repo.init()
    await actions_repo.init()
    # Build index in background
    asyncio.create_task(recommender.build_index())


@app.post("/books", status_code=201)
async def add_book(book: Book):
    existing = await books_repo.get_book(book.id)
    if existing:
        raise HTTPException(status_code=409, detail="book id exists")
    await books_repo.add_book(book)
    # rebuild recommender index (async)
    asyncio.create_task(recommender.build_index())
    return {"status": "ok"}


@app.get("/books", response_model=List[Book])
async def list_books():
    return await books_repo.list_books()


@app.post("/user/actions")
async def user_action(action: UserAction):
    await actions_repo.add_action(action.user_id, action.book_id, action.action)
    # optional: schedule index rebuild (not needed for small updates)
    return {"status": "ok"}


@app.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations(user_id: str = Query(...), k: int = Query(10, ge=1, le=50)):
    recs = await recommender.get_recommendations(user_id, k)
    return recs


# Simple fuzzy search endpoint
@app.get("/search")
async def search(q: str = Query(...), limit: int = Query(20, ge=1, le=100)):
    books = await books_repo.list_books()
    # basic fuzzy matching on title + authors
    choices = {f"{b.title} - {' '.join(b.authors)}": b for b in books}
    results = process.extract(q, choices.keys(), scorer=fuzz.WRatio, limit=limit)
    # results: list of (choice, score, idx)
    out = []
    for choice, score, _ in results:
        b = choices[choice]
        out.append({"book": b, "score": score})
    return out
