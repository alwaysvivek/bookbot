"""
bookbot/recommender.py

Content-based recommender using TF-IDF on titles+descriptions.
- Precomputes TF-IDF vectors for all books in a background task.
- Provides get_recommendations(user_id, k) using user history to compute a profile vector.
- Uses asyncio.to_thread to run blocking sklearn code off the event loop.

Notes:
- Dependencies: scikit-learn, numpy
"""

from typing import List, Tuple, Dict
import asyncio
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from .repository import BooksRepository, UserActionsRepository
from .models import Recommendation, Book
import logging

logger = logging.getLogger(__name__)


class Recommender:
    def __init__(self, books_repo: BooksRepository, actions_repo: UserActionsRepository):
        self.books_repo = books_repo
        self.actions_repo = actions_repo
        self._lock = asyncio.Lock()
        self._vectorizer: TfidfVectorizer = None
        self._matrix = None  # TF-IDF matrix (num_books x features)
        self._book_index: List[int] = []  # book ids in matrix order
        self._id_to_pos: Dict[int, int] = {}

    async def build_index(self) -> None:
        """
        Build TF-IDF index from books. Runs blocking sklearn operations in threadpool.
        Call this on startup and after bulk updates.
        """
        books = await self.books_repo.list_books()
        texts = [f"{b.title} {b.description or ''}" for b in books]
        book_ids = [b.id for b in books]

        # run TF-IDF in threadpool to avoid blocking the event loop
        def build():
            vec = TfidfVectorizer(stop_words="english", max_features=10000)
            mat = vec.fit_transform(texts)
            return vec, mat

        vec, mat = await asyncio.to_thread(build)

        async with self._lock:
            self._vectorizer = vec
            self._matrix = mat  # csr_matrix
            self._book_index = book_ids
            self._id_to_pos = {bid: i for i, bid in enumerate(book_ids)}
            logger.info("Recommender index built with %d books", len(book_ids))

    async def get_recommendations(self, user_id: str, k: int = 10) -> List[Recommendation]:
        """
        Recommend k books for user_id.
        Strategy:
        - Get user history (liked/read book ids).
        - If no history: return top-k popular books.
        - Else: compute user profile vector by averaging TF-IDF vectors of liked books and compute cosine similarities.
        """
        books = await self.books_repo.list_books()
        if not books:
            return []

        history = await self.actions_repo.get_user_history(user_id)
        # map book ids to positions
        async with self._lock:
            if self._matrix is None:
                # index not ready: fallback to popularity
                sorted_books = sorted(books, key=lambda b: b.popularity, reverse=True)
                return [Recommendation(book_id=b.id, score=0.0) for b in sorted_books[:k]]

            id_to_pos = self._id_to_pos
            mat = self._matrix

        if not history:
            # no history: fallback to popularity
            sorted_books = sorted(books, key=lambda b: b.popularity, reverse=True)
            return [Recommendation(book_id=b.id, score=0.0) for b in sorted_books[:k]]

        # compute user profile vector: average of vectors for history items
        positions = [id_to_pos[b] for b in history if b in id_to_pos]
        if not positions:
            # history books not in current index
            sorted_books = sorted(books, key=lambda b: b.popularity, reverse=True)
            return [Recommendation(book_id=b.id, score=0.0) for b in sorted_books[:k]]

        # get submatrix for user books
        user_mat = mat[positions]
        # average (dense)
        # run dot product and similarity in threadpool
        def compute_sim():
            # user profile as mean of rows
            profile = np.asarray(user_mat.mean(axis=0)).ravel()
            # cosine similarity via linear_kernel
            sims = linear_kernel(profile.reshape(1, -1), mat).ravel()
            return sims

        sims = await asyncio.to_thread(compute_sim)

        # exclude user's own books
        for p in positions:
            sims[p] = -1.0

        # get top k indices
        top_idx = np.argpartition(-sims, range(min(k, len(sims))))[:k]
        top_scores = [(int(self._book_index[i]), float(sims[i])) for i in top_idx]
        # sort by score
        top_scores.sort(key=lambda x: x[1], reverse=True)
        return [Recommendation(book_id=bid, score=score) for bid, score in top_scores]
