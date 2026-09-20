from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    # ===========GROQ===========
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFAULT_LLM_MODEL: str = os.getenv(
        "DEFAULT_LLM_MODEL", "openai/gpt-oss-20b")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", 0.0))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", 350))
    LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", 30.0))
    LLM_SYSTEM_PROMPT: str = os.getenv(
        "LLM_SYSTEM_PROMPT",
        "Bạn là trợ lý AI RAG. Chỉ sử dụng thông tin trong Context.Trả lời ngắn gọn bằng tiếng Việt. Nếu Context không có thông tin thì trả lời: 'Xin lỗi, tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu."
    )

    # ===========EMBEDDING===========
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-mpnet-base-v2")
    VECTOR_SIZE: int = int(os.getenv("VECTOR_SIZE", 768))

    # ==========QDRANT===========
    QDRANT_STORAGE_PATH: str = os.getenv(
        "QDRANT_STORAGE_PATH", "./database/qdrant")
    QDRANT_HOST: str = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT: int = int(os.getenv("QDRANT_PORT", 6333))
    QDRANT_COLLECTION_NAME: str = os.getenv(
        "QDRANT_COLLECTION_NAME", "documents")

    # ==========RETRIEVER===========
    TOP_K: int = int(os.getenv("TOP_K", 4))
    SOURCE_THRESHOLD: float = float(os.getenv("SOURCE_THRESHOLD", 0.35))

    # =========== CHUNKER ===========
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 600))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 120))

    def validate(self):
        if not self.GROQ_API_KEY:
            print("Cảnh báo: Chưa cấu hình GROQ_API_KEY.")


settings = Settings()
settings.validate()
