# BookBot — Personalized Recommendations (Enhancement)

This enhancement adds a modular, production-friendly recommendation service and a fast fuzzy search to BookBot.

Contents
- TDD: `TDD.md` (design and trade-offs)
- API: `/recommendations`, `/search`, `/user/actions`, `/books`
- Components:
  - `bookbot/repository.py` — Repository pattern (aiosqlite)
  - `bookbot/recommender.py` — TF-IDF content-based recommender (sklearn)
  - `bookbot/api.py` — FastAPI endpoints
  - `bookbot/models.py` — Pydantic models
- Tests under `tests/` (unit + integration examples)

Quickstart
1. Create virtualenv and install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn aiosqlite scikit-learn numpy rapidfuzz pytest pytest-asyncio httpx
   ```
2. Run the app:
   ```
   uvicorn bookbot.api:app --reload
   ```
3. Use the API:
   - Add books: POST /books
   - Record user actions: POST /user/actions
   - Request recommendations: GET /recommendations?user_id=alice&k=10
   - Search: GET /search?q=harry

Design notes
- Repository Pattern decouples persistence from business logic.
- Recommender builds TF-IDF vectors in a thread (asyncio.to_thread) to avoid blocking the event loop.
- The system uses in-process in-memory vectors for low-latency recommendations; for production, migrate vectors and nearest-neighbour search to an external vector DB.

Configuration
- BOOKBOT_DB_PATH (default "bookbot.db")

Testing
- Run `pytest` to run unit tests and the provided integration smoke test.
- Aim: unit tests for repository and recommender achieve >90% coverage for these modules.

Next steps (recommended)
- Add persistent job metrics and telemetry.
- Replace in-memory vector index with FAISS/Milvus for large catalogs.
- Add caching (Redis) for hot recommendation queries.

---

# Original BookBot

BookBot is my first [Boot.dev](https://www.boot.dev) project!
