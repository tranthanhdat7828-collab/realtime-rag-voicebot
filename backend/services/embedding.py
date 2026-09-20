from fastembed import TextEmbedding
from backend.config.settings import settings
from backend.schemas.chunk import Chunk
from backend.schemas.embed import EmbeddedChunk


class EmbeddingService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.model = TextEmbedding(
                model_name=settings.EMBEDDING_MODEL)
        return cls._instance

    def embed_query(self, query: str) -> list[float]:
        if not query or not query.strip():
            return []
        vector = list(self.model.embed([query]))
        return vector[0].tolist()

    def embed_chunks(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        if not chunks:
            return []
        text_to_embed = [chunk.enriched_content
                         if (hasattr(chunk, "enriched_content") and chunk.enriched_content)
                         else chunk.content
                         for chunk in chunks]
        vectors = list(self.model.embed(text_to_embed, batch_size=32))

        embedded_chunks: list[EmbeddedChunk] = []
        for chunk, vector in zip(chunks, vectors):
            embedded_chunks.append(
                EmbeddedChunk(
                    chunk_id=str(chunk.chunk_id),
                    content=chunk.content,
                    vector=vector.tolist(),
                    metadata=chunk.metadata
                )
            )
        return embedded_chunks
