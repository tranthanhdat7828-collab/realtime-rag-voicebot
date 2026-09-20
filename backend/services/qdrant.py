import uuid
from typing import Optional, List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, PayloadSchemaType
from backend.schemas.embed import EmbeddedChunk
from backend.config.settings import settings


class QdrantService:
    _instance = None
    _client = None

    COLLECTION_NAME = settings.QDRANT_COLLECTION_NAME
    VECTOR_DIMENSION = settings.VECTOR_SIZE

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QdrantService, cls).__new__(cls)
            qdrant_host = getattr(settings, "QDRANT_HOST", None)
            if qdrant_host and str(qdrant_host).strip():
                cls._client = QdrantClient(
                    host=settings.QDRANT_HOST,
                    port=getattr(settings, "QDRANT_PORT", 6333),
                    timeout=10.0
                )
            else:

                cls._client = QdrantClient(path=settings.QDRANT_STORAGE_PATH)

            cls._instance.create_collection()
            cls._instance._create_payload_indexes()

        return cls._instance

    def create_collection(self):
        try:
            collection = self._client.get_collections().collections
            exist = any(
                col.name == self.COLLECTION_NAME
                for col in collection
            )
            if not exist:
                self._client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.VECTOR_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"[Qdrant Init Warning]: {e}")

    def _create_payload_indexes(self):
        try:
            self._client.create_payload_index(
                collection_name=self.COLLECTION_NAME,
                field_name="user_id",
                field_schema=PayloadSchemaType.KEYWORD
            )
            self._client.create_payload_index(
                collection_name=self.COLLECTION_NAME,
                field_name="source",
                field_schema=PayloadSchemaType.KEYWORD
            )
        except Exception:
            pass

    def recreate_collection(self):
        try:
            self._client.recreate_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            self._create_payload_indexes()
        except Exception as e:
            print(f"[Qdrant Recreate Error]: {e}")

    def clear_all(self):
        self.recreate_collection()

    def delete_by_source(self, source: str, user_id: str):
        try:
            self._client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="source", match=MatchValue(value=source)),
                        FieldCondition(
                            key="user_id", match=MatchValue(value=user_id))
                    ]
                )
            )
        except Exception:
            pass

    def count_points(self) -> int:
        try:
            return self._client.count(collection_name=self.COLLECTION_NAME).count
        except Exception:
            return 0

    def insert_chunks(self, embedded_chunks: list[EmbeddedChunk], user_id: str = "default_user"):
        if not embedded_chunks:
            return

        sources_to_clean = {
            chunk.metadata.get("source", "unlnown").split(
                "/")[-1].split("\\")[-1]
            for chunk in embedded_chunks if chunk.metadata.get("source")
        }
        for src in sources_to_clean:
            self.delete_by_source(src, user_id)

        points = []
        for chunk in embedded_chunks:
            source = chunk.metadata.get(
                "source", "unknown").split("/")[-1].split("\\")[-1]
            unique_key = f"{user_id}_{source}_{chunk.chunk_id}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_key))
            payload_data = chunk.metadata.copy()
            payload_data["source"] = source
            payload_data["user_id"] = user_id
            points.append(
                PointStruct(
                    id=point_id,
                    vector=chunk.vector,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content,
                        **payload_data
                    }
                )
            )
        self._client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )

    def search(self, query_vector: list[float], top_k: int = settings.TOP_K, user_id: Optional[str] = None):
        if not query_vector:
            return []
        search_filter = None
        if user_id:
            search_filter = Filter(
                must=[FieldCondition(
                    key="user_id", match=MatchValue(value=user_id))]
            )

        results = self._client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector,
            query_filter=search_filter,
            limit=top_k
        )
        return results.points

    def close(self):
        pass
