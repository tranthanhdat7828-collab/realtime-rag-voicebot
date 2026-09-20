import os
import uuid
from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import HTTPException
from backend.services.qdrant import QdrantService
from backend.services.embedding import EmbeddingService
from backend.services.chunker import ChunkService
from backend.services.cleaner import CleanerService
from backend.services.parser import ParserService

router = APIRouter()
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(TEMP_DIR, unique_name)
    qdrant_service = None
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        document = ParserService.parse(file_path)
        document.metadata["source"] = file.filename
        document = CleanerService.clean(document)
        chunks = ChunkService.chunk(document)
        if not chunks:
            raise HTTPException(
                status_code=400, detail="Không trích xuất nội dung từ file."
            )
        embedding_service = EmbeddingService()
        embedded_chunks = embedding_service.embed_chunks(chunks)
        qdrant_service = QdrantService()
        qdrant_service.create_collection()
        qdrant_service.insert_chunks(embedded_chunks)

        total_chunks = qdrant_service.count_points()
        return {
            "status": "success",
            "filename": file.filename,
            "chunks": len(chunks),
            "embedded_chunk": len(embedded_chunks),
            "total_chunks": total_chunks
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Lỗi khi upload và xử lý file:{str(e)}"
        )
    finally:
        if qdrant_service and hasattr(qdrant_service, "close"):
            qdrant_service.close()

        if os.path.exists(file_path):
            os.remove(file_path)
