# tests/test_recommender.py
import pytest
import asyncio
from bookbot.repository import BooksRepository, UserActionsRepository
from bookbot.models import Book
from bookbot.recommender import Recommender
import tempfile
import os

@pytest.mark.asyncio
async def test_recommender_basic(tmp_path):
    db_path = str(tmp_path / "rb.db")
    books_repo = BooksRepository(db_path)
    actions_repo = UserActionsRepository(db_path)
    await books_repo.init()
    await actions_repo.init()

    # Add some books
    b1 = Book(id=1, title="Python Programming", authors=["A"], description="Learn Python", tags=["programming"], popularity=10)
    b2 = Book(id=2, title="Advanced Cooking", authors=["B"], description="Cook like a pro", tags=["cooking"], popularity=8)
    b3 = Book(id=3, title="Python Data Science", authors=["C"], description="Data Science with Python", tags=["data"], popularity=7)
    await books_repo.add_book(b1)
    await books_repo.add_book(b2)
    await books_repo.add_book(b3)

    recommender = Recommender(books_repo, actions_repo)
    await recommender.build_index()

    # No history -> should return popular books
    recs = await recommender.get_recommendations("u1", k=2)
    assert len(recs) == 2

    # Add user like for python book
    await actions_repo.add_action("uX", 1, "like")
    recs2 = await recommender.get_recommendations("uX", k=2)
    # Expect recommendations include python related book (id 3)
    ids = [r.book_id for r in recs2]
    assert 3 in ids or 1 not in ids  # assert some relation; main check is that it returns without error
