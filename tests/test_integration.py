# tests/test_integration.py
import pytest
from httpx import AsyncClient, ASGITransport
from bookbot.api import app, books_repo, actions_repo, recommender
import asyncio

@pytest.mark.asyncio
async def test_recommendations_endpoint():
    # Manually initialize the database (since lifespan events may not fire in test)
    await books_repo.init()
    await actions_repo.init()
    
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
