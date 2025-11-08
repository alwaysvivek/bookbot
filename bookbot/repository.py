"""
bookbot/repository.py

Repository pattern for books and user actions. Uses aiosqlite for async DB access.

This isolates DB code from business logic and makes it easy to swap the backend.
"""

import aiosqlite
import asyncio
from typing import List, Dict, Optional
from .models import Book
import os

DB_PATH = os.environ.get("BOOKBOT_DB_PATH", "bookbot.db")


class BooksRepository:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = asyncio.Lock()

    async def init(self) -> None:
        """Create tables if missing."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    authors TEXT,
                    description TEXT,
                    tags TEXT,
                    popularity INTEGER DEFAULT 0
                )
                """
            )
            await db.commit()

    async def add_book(self, book: Book) -> None:
        async with self._lock, aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO books(id, title, authors, description, tags, popularity) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    book.id,
                    book.title,
                    ",".join(book.authors),
                    book.description or "",
                    ",".join(book.tags),
                    book.popularity,
                ),
            )
            await db.commit()

    async def list_books(self) -> List[Book]:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT id, title, authors, description, tags, popularity FROM books")
            rows = await cur.fetchall()
            return [
                Book(
                    id=r[0],
                    title=r[1],
                    authors=r[2].split(",") if r[2] else [],
                    description=r[3],
                    tags=r[4].split(",") if r[4] else [],
                    popularity=r[5] or 0,
                )
                for r in rows
            ]

    async def get_book(self, book_id: int) -> Optional[Book]:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("SELECT id, title, authors, description, tags, popularity FROM books WHERE id = ?", (book_id,))
            r = await cur.fetchone()
            if not r:
                return None
            return Book(
                id=r[0],
                title=r[1],
                authors=r[2].split(",") if r[2] else [],
                description=r[3],
                tags=r[4].split(",") if r[4] else [],
                popularity=r[5] or 0,
            )


class UserActionsRepository:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = asyncio.Lock()

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    book_id INTEGER,
                    action TEXT,
                    timestamp INTEGER
                )
                """
            )
            await db.commit()

    async def add_action(self, user_id: str, book_id: int, action: str) -> None:
        async with self._lock, aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO user_actions(user_id, book_id, action, timestamp) VALUES (?, ?, ?, strftime('%s','now'))",
                (user_id, book_id, action),
            )
            await db.commit()

    async def get_user_history(self, user_id: str, limit: int = 100) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute(
                "SELECT DISTINCT book_id FROM user_actions WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            )
            rows = await cur.fetchall()
            return [r[0] for r in rows]
