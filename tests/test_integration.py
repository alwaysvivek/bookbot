# tests/test_integration.py
import pytest
from httpx import AsyncClient, ASGITransport
from bookbot.api import app
from bookbot.repository import BooksRepository, UserActionsRepository
from bookbot.recommender import Recommender
import asyncio
import os
import tempfile

@pytest.mark.asyncio
async def test_recommendations_endpoint(tmp_path):
    # Use a temporary database for this test
    test_db = str(tmp_path / "test_integration.db")
    
    # Create fresh instances for this test
    test_books_repo = BooksRepository(test_db)
    test_actions_repo = UserActionsRepository(test_db)
    test_recommender = Recommender(test_books_repo, test_actions_repo)
    
    # Manually initialize the database
    await test_books_repo.init()
    await test_actions_repo.init()
    
    # Monkey patch the app's repositories for this test
    import bookbot.api as api_module
    original_books_repo = api_module.books_repo
    original_actions_repo = api_module.actions_repo
    original_recommender = api_module.recommender
    
    api_module.books_repo = test_books_repo
    api_module.actions_repo = test_actions_repo
    api_module.recommender = test_recommender
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
            # ensure app startup ran
            resp = await client.get("/books")
            assert resp.status_code == 200
            # POST a book and user action, then call recommendations
            book = {"id": 100, "title": "Integration Book", "authors": ["X"], "description": "Integration testing", "tags": [], "popularity": 1}
            r = await client.post("/books", json=book)
            assert r.status_code in (200, 201)
            
            # Wait a bit for the background index build to complete
            await asyncio.sleep(1)
            
            # record action
            await client.post("/user/actions", json={"user_id": "testu", "book_id": 100, "action": "like"})
            recs = await client.get("/recommendations", params={"user_id": "testu", "k": 5})
            assert recs.status_code == 200
            # returns a list
            assert isinstance(recs.json(), list)
    finally:
        # Restore original repositories
        api_module.books_repo = original_books_repo
        api_module.actions_repo = original_actions_repo
        api_module.recommender = original_recommender
