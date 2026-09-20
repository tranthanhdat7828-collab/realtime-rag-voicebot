import time
from backend.schemas.quer import QueryRequest
from backend.services.generator import GeneratorService
from backend.services.retriever import RetrieverService
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

router = APIRouter()
retriever = RetrieverService()
generator = GeneratorService()


@router.post("/query")
async def query_rag(request: QueryRequest):
    try:
        # 0. Bấm giờ tổng pipeline
        t_start = time.perf_counter()

        # 1. Gọi Retriever bóc tách thời gian
        context, embed_ms, search_ms = retriever.get_context_with_metrics(
            request.question
        )

        if not context or not context.strip():

            async def no_context():
                yield "Xin lỗi, tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu."

            return StreamingResponse(
                no_context(),
                media_type="text/plain; charset=utf-8",
                headers={"X-Accel-Buffering": "no"},
            )

        context_length_chars = len(context)
        approx_words = len(context.split())

        # 2. Stream & Đo đạc Pipeline TTFT
        async def stream_generator():
            first_valid_token = False
            chunk_count = 0
            real_ttft_ms = 0.0

            async for token in generator.generate_stream(
                question=request.question, context=context
            ):
                if not token or not isinstance(token, str):
                    continue

                chunk_count += 1

                # Bắt token có nghĩa đầu tiên xuất hiện ra client
                if not first_valid_token and token.strip():
                    first_valid_token = True
                    now = time.perf_counter()
                    real_ttft_ms = (now - t_start) * 1000

                    # Dùng trực tiếp visible TTFT do generator đo
                    groq_visible_ms = generator.last_ttft_ms
                    overhead_ms = max(
                        0.0, real_ttft_ms -
                        (embed_ms + search_ms + groq_visible_ms)
                    )

                    print("\n" + "=" * 62)
                    print("📊 BẢNG BÓC TÁCH CHI TIẾT ĐỘ TRỄ TỪNG BƯỚC (TTFT BREAKDOWN)")
                    print("=" * 62)
                    print(
                        f" 1. Tạo Embedding câu hỏi         : {embed_ms:8.2f} ms "
                        f" ({(embed_ms/real_ttft_ms)*100:4.1f}%)"
                    )
                    print(
                        f" 2. Vector Search (Qdrant)       : {search_ms:8.2f} ms "
                        f" ({(search_ms/real_ttft_ms)*100:4.1f}%)"
                    )
                    print(
                        f" 3. Xử lý nội bộ FastAPI          : {overhead_ms:8.2f} ms "
                        f" ({(overhead_ms/real_ttft_ms)*100:4.1f}%)"
                    )
                    print(
                        f" 4. Groq First Raw Chunk         : {generator.last_raw_ttft_ms:8.2f}"
                        " ms"
                    )
                    print(
                        f" 5. Groq First Visible Token     : {groq_visible_ms:8.2f} ms "
                        f" ({(groq_visible_ms/real_ttft_ms)*100:4.1f}%)  👈 NÚT THẮT"
                    )
                    print("-" * 62)
                    print(
                        f" 🔥 TỔNG REAL TTFT               : {real_ttft_ms:8.2f} ms")
                    print(f" 🔤 Nội dung chunk đầu tiên      : {repr(token)}")
                    print(
                        f" 📄 Độ dài Context nhồi vào      : {context_length_chars} ký"
                        f" tự (~{approx_words} từ)"
                    )
                    print("=" * 62 + "\n")

                yield token

            # Tổng kết khi kết thúc toàn bộ câu
            total_duration = (time.perf_counter() - t_start) * 1000
            decoding_time = total_duration - real_ttft_ms
            speed = (
                (chunk_count / (decoding_time / 1000)) if decoding_time > 0 else 0
            )
            print(f"⏱️ Tổng thời gian chạy hết câu : {total_duration:.2f} ms")
            print(
                f"⚡ Tốc độ streaming             : {speed:.1f} chunks/giây"
                f" ({chunk_count} chunks)\n"
            )

        return StreamingResponse(
            stream_generator(),
            media_type="text/plain; charset=utf-8",
            headers={"X-Accel-Buffering": "no"},
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Lỗi trong quá trình xử lý: {str(e)}"
        )
