from backend.services.embedding import EmbeddingService
from backend.services.qdrant import QdrantService
from typing import List, Any, Optional
from backend.config.settings import settings
import time


class RetrieverService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RetrieverService, cls).__new__(cls)
            cls._instance.embedding_service = EmbeddingService()
            cls._instance.qdrant_service = QdrantService()
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, top_k: Optional[int] = None, source_threshold: Optional[float] = None):
        if getattr(self, "_initialized", False):
            if top_k is not None:
                self.top_k = top_k
            if source_threshold is not None:
                self.source_threshold = source_threshold
            return

        self.top_k = settings.TOP_K if top_k is None else top_k
        self.source_threshold = (
            settings.SOURCE_THRESHOLD
            if source_threshold is None
            else source_threshold
        )
        self._initialized = True

    def retrieve_with_timing(self, question: str, top_k: Optional[int] = None) -> tuple[List[Any], float, float]:
        if not question or not question.strip():
            return [], 0.0, 0.0

        k = self.top_k if top_k is None else top_k

        t0 = time.perf_counter()
        query_vector = self.embedding_service.embed_query(question)
        embed_ms = (time.perf_counter() - t0) * 1000

        t1 = time.perf_counter()
        results = self.qdrant_service.search(
            query_vector=query_vector,
            top_k=k
        )
        search_ms = (time.perf_counter() - t1) * 1000

        return results, embed_ms, search_ms

    def retrieve(self, question: str, top_k: Optional[int] = None) -> List[Any]:
        points, _, _ = self.retrieve_with_timing(question, top_k)
        return points

    def format_context(self, points: List[Any]) -> str:
        if not points:
            return ""
        context_blocks = []
        for idx, point in enumerate(points, 1):
            if hasattr(point, "score") and point.score < self.source_threshold:
                continue
            payload = point.payload or {}
            content = payload.get("content", "") or payload.get("text", "")
            source = payload.get("source", "Tài liệu")

            if content:
                context_blocks.append(f"[{idx}.Nguồn: {source}]\n{content}")
        return "\n\n".join(context_blocks)

    def get_context(self, question: str, top_k: Optional[int] = None) -> str:
        points = self.retrieve(question, top_k)
        return self.format_context(points)

    def get_context_with_metrics(self, question: str, top_k: Optional[int] = None) -> tuple[str, float, float]:
        points, embed_ms, search_ms = self.retrieve_with_timing(
            question, top_k)
        context = self.format_context(points)
        return context, embed_ms, search_ms

    def close(self):
        pass
