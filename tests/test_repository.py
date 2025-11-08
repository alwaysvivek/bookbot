# tests/test_repository.py
import pytest
import os
import asyncio
import tempfile
from bookbot.repository import BooksRepository, UserActionsRepository
from bookbot.models import Book

@pytest.mark.asyncio
async def test_books_repo_and_user_actions(tmp_path):
    db_path = str(tmp_path / "test.db")
    books_repo = BooksRepository(db_path)
    actions_repo = UserActionsRepository(db_path)
    await books_repo.init()
    await actions_repo.init()

    b = Book(id=1, title="Test Book", authors=["Alice"], description="A test", tags=["test"], popularity=5)
    await books_repo.add_book(b)
    books = await books_repo.list_books()
    assert len(books) == 1
    fetched = await books_repo.get_book(1)
    assert fetched.title == "Test Book"

    await actions_repo.add_action("user1", 1, "like")
    history = await actions_repo.get_user_history("user1")
    assert 1 in history
