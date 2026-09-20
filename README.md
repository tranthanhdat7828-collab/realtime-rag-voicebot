
from backend.services.chunker import ChunkService
from backend.services.cleaner import CleanerService
from backend.services.embedding import EmbeddingService
from backend.services.generator import GeneratorService
from backend.services.parser import ParserService
from backend.services.qdrant import QdrantService
from backend.services.retriever import RetrieverService


def main():
    # 1. PARSE & CLEAN
    document = ParserService.parse("documents/test.txt")
    document = CleanerService.clean(document)

    # 2. CHUNK
    chunks = ChunkService.chunk(document)

    # 3. EMBED
    embedding_service = EmbeddingService()
    embedded_chunks = embedding_service.embed_chunks(chunks)

    # 4. INSERT TO QDRANT
    qdrant_service = QdrantService()
    qdrant_service.create_collection()
    qdrant_service.insert_chunks(embedded_chunks)
    print("Inserted chunks into Qdrant collection.")
    qdrant_service.close()

    # 5. RETRIEVAL & GENERATION
    test_question = "Skip Connections có tác dụng gì?"
    retriever_service = RetrieverService(top_k=5)

    # Lấy kết quả tìm kiếm để in log
    results = retriever_service.retrieve(test_question)
    print("\n===== RETRIEVER =====")
    for point in results:
        print("------------")
        print(f"Chunk ID: {point.payload.get('chunk_id')}")
        print(f"Score: {point.score}")
        print(point.payload.get("content"))
        print("------------")

    # Lấy context cho LLM (PHẢI GỌI TRƯỚC KHI CLOSE)
    context = retriever_service.get_context(test_question)

    # Sau khi đã lấy xong dữ liệu từ Qdrant mới tiến hành đóng kết nối
    retriever_service.close()

    # 6. GENERATE
    print("\n========== GENERATOR ==========")
    print("--- Context nạp cho LLM ---")
    print(context)
    print("----------------------------")

    generator_service = GeneratorService()
    answer = generator_service.generate(
        question=test_question, context=context)
    print("\n--- Câu trả lời của LLM ---")
    print(answer)


if __name__ == "__main__":
    main()


