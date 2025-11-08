# BookBot — Personalized Recommendations (TDD)

## Problem
BookBot currently serves book information (discover/view). Users lack personalized suggestions to find books they will likely enjoy. This reduces engagement and the value of the bot.

## Goal
Add a scalable, modular personalized recommendation service to BookBot that:
- Provides per-user recommendations (cold-start: popular + content-based hybrid).
- Completes a recommendation request in <200ms (in-memory + precomputed vectors).
- Scales to concurrent requests using asyncio and caching.

## Core Feature (Major)
Personalized Book Recommendation Engine:
- Content-based recommender using TF-IDF vectors of book descriptions + titles.
- Precompute book vectors in background worker and store them in a lightweight vector index (in-memory).
- For each user: compute a "user profile vector" from liked/read history (titles/descriptions), then find nearest neighbors (cosine similarity).
- Provide REST API: GET /recommendations?user_id=<id>&k=10
- Use Repository Pattern for data access (books, user interactions) backed by SQLite (aiosqlite).

Success Metrics:
- Latency: median recommendation API response time <200ms for catalog size <= 10k after vectors computed.
- Accuracy: Improve click-through by +X% (measured in production; simulated tests verify ranked results).
- Throughput: handle 200 concurrent recommendation requests (with caching) without blocking.

## Supporting Feature (Quality-of-life)
Fuzzy Search + Caching:
- Endpoint: GET /search?q=...&limit=20 with fuzzy match on title, author using rapidfuzz.
- Results cached in LRU cache (async-compatible) for repeated queries.
- Return results with relevance scores.

Success Metric:
- Search latency <150ms for cached queries.
- Cache hit rate >50% on repeated queries in realistic sessions.

## Architecture / Components
- FastAPI application providing REST endpoints (recommendations, search, book CRUD, user events).
- Repository layer (books_repo, users_repo) using aiosqlite — isolates DB concerns.
- Recommender service:
  - Background precompute using asyncio.to_thread to run sklearn TfidfVectorizer (blocking).
  - In-memory matrix + nearest neighbors using numpy dot / sklearn NearestNeighbors (or manual cosine).
- Cache layer: in-memory async-safe LRU for search results (aiocache or custom).
- Tests: pytest + pytest-asyncio + httpx AsyncClient for integration test.

Sequence (recommend flow):
1. Startup: load books from DB -> async background task computes TF-IDF vectors -> populate index.
2. User triggers recommendation -> API calls recommender.get_recommendations(user_id, k)
3. Recommender:
   - If user has history: build user vector from liked items -> compute cosine similarities -> return top-k
   - Else: return popular or editorial picks
4. Response returned to client.

## Trade-offs
- Using in-process in-memory vectors for low latency vs. a production vector DB (Milvus/FAISS). For scaling, migrate to vector DB.
- Sklearn TF-IDF is CPU-bound; to avoid blocking the event loop we run vectorization in threadpool (asyncio.to_thread).
- SQLite for portability; for scale use Postgres.

## API Spec (minimal)
- GET /recommendations?user_id=<id>&k=10 -> JSON list of book objects + score
- POST /user/actions {user_id, book_id, action: "like"|"read"} -> 200 OK
- GET /search?q=<term>&limit=20 -> JSON list of {book, score}

## Tests
- Unit tests for repository, recommender logic with synthetic data (target >90% coverage for these modules).
- Integration test: start FastAPI app in-process and assert recommendation flow (enqueue user actions -> recommendations reflect them).

## Deployment notes
- New env vars:
  - BOOKBOT_DB_URL (default sqlite:///./bookbot.db)
  - BOOKBOT_RECOMMENDER_WORKERS (default 1)
- Add dependency: scikit-learn, numpy, aiosqlite, rapidfuzz
- For CI: install above packages and run pytest.
