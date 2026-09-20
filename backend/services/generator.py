from typing import AsyncGenerator
from backend.config.settings import settings
from groq import AsyncGroq, Groq
import time


class GeneratorService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeneratorService, cls).__new__(cls)
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY CHƯA ĐƯỢC CẤU HÌNH.")
            cls._instance.client = Groq(
                api_key=settings.GROQ_API_KEY, timeout=getattr(settings, "LLM_TIMEOUT", 30.0))
            cls._instance.async_client = AsyncGroq(
                api_key=settings.GROQ_API_KEY, timeout=getattr(settings, "LLM_TIMEOUT", 30.0))
            cls._instance.last_raw_ttft_ms = 0.0
            cls._instance.last_ttft_ms = 0.0

        return cls._instance

    def build_prompt(self, question: str, context: str) -> str:
        return f"""Context:
{context}

Question:
{question}
"""

    def generate(self, question: str, context: str) -> str:
        if not context or not context.strip():
            return (
                "Xin lỗi, tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu."
            )

        prompt = self.build_prompt(question, context)
        response = self.client.chat.completions.create(
            model=settings.DEFAULT_LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            messages=[
                {
                    "role": "system",
                    "content": settings.LLM_SYSTEM_PROMPT,
                },
                {"role": "user", "content": prompt},
            ],
        )

        return (response.choices[0].message.content or "").strip()

    async def generate_stream(
        self, question: str, context: str
    ) -> AsyncGenerator[str, None]:
        if not context or not context.strip():
            yield "Xin lỗi, tôi không tìm thấy thông tin liên quan trong cơ sở dữ liệu."
            return

        prompt = self.build_prompt(question, context)
        groq_call_start = time.perf_counter()
        first_token = True

        self.last_raw_ttft_ms = 0.0
        self.last_ttft_ms = 0.0

        try:
            stream = await self.async_client.chat.completions.create(
                model=settings.DEFAULT_LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                stream=True,
                messages=[
                    {
                        "role": "system",
                        "content": settings.LLM_SYSTEM_PROMPT,
                    },
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as e:
            print(f"\n Lỗi gọi GROQ API: {e}")
            yield f"[Lỗi kết nối LLM: {str(e)}]"
            return
        try:
            async for chunk in stream:
                if not chunk.choices:
                    continue

                delta_token = chunk.choices[0].delta.content
                if not delta_token:
                    continue

                if first_token and delta_token.strip():
                    first_token = False
                    elapsed_ms = (time.perf_counter() - groq_call_start) * 1000
                    self.last_raw_ttft_ms = elapsed_ms
                    self.last_ttft_ms = elapsed_ms
                    print(
                        f"\n[GROQ TTFT]:{self.last_ttft_ms:.2f} ms| First Token: {repr(delta_token)} ")
                yield delta_token
        except Exception as e:
            print(f"\n Lỗi trong quá trình nhận chunk: {e}")
            yield f"\n[Lỗi ngắt stream: {str(e)}]"
