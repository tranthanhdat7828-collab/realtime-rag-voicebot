from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.schemas.document import Document
from backend.schemas.chunk import Chunk
from backend.config.settings import settings
import re


class ChunkService:

    @staticmethod
    def chunk(
        document: Document,
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> list[Chunk]:
        if not document.content or not document.content.strip():
            return []

        c_size = chunk_size or getattr(settings, "CHUNK_SIZE", 600)
        c_overlap = chunk_overlap or getattr(settings, "CHUNK_OVERLAP", 120)

        lines = document.content.split("\n")
        sections = []
        current_headers = {1: "", 2: "", 3: ""}
        current_content = []

        def get_breadcrumb() -> str:
            headers = [current_headers[lvl]
                       for lvl in (1, 2, 3)
                       if current_headers[lvl]]
            return " > ".join(headers) if headers else ""

        for line in lines:
            match = re.match(r"^(#{1,3})\s+(.*)$", line)
            if match:
                if current_content:
                    sections.append(
                        (get_breadcrumb(), "\n".join(current_content)))
                    current_content = []

                level = len(match.group(1))
                title = match.group(2).strip()
                current_headers[level] = title

                for l in range(level + 1, 4):
                    current_headers[l] = ""
            else:
                current_content.append(line)
        if current_content:
            sections.append((get_breadcrumb(), "\n".join(current_content)))

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=c_size,
            chunk_overlap=c_overlap,
            separators=[
                "\n\n",
                "\n### ", "\n## ", "\n# ",
                "\nBước ", "\nBuoc ", "\nbuoc ",
                "\nĐiều ", "\nChương ", "\nPhần ", "\nMục ",
                "\n- ", "\n* ", "\n+ ",
                "\n1.", "\n2.", "\n3.", "\n4.", "\n5.",
                "\n", ". ", "? ", "! ", " ", ""
            ],
        )

        chunks: list[Chunk] = []
        global_idx = 0
        doc_source = document.metadata.get("source", "doc")

        for breadcrumb, text in sections:
            if not text.strip():
                continue

            table_header_block = ""
            text_lines = text.split("\n")
            for idx, l in enumerate(text_lines):
                line_str = l.strip()
                if line_str.startswith("|") and "---" not in line_str:
                    if idx + 1 < len(text_lines) and "---" in text_lines[idx + 1]:
                        table_header_block = f"{line_str}\n{text_lines[idx + 1].strip()}"
                        break

            sub_texts = splitter.split_text(text)

            for i, sub_text in enumerate(sub_texts):
                final_content = sub_text
                if (
                    i > 0
                    and table_header_block
                    and sub_text.strip().startswith("|")
                    and "---" not in sub_text
                ):
                    final_content = f"{table_header_block}\n{sub_text}"
                if breadcrumb:
                    enriched_text = f"[{breadcrumb}]\n{final_content}"
                else:
                    enriched_text = final_content

                chunk_meta = document.metadata.copy()
                chunk_meta.update({
                    "chunk_index": global_idx,
                    "breadcrumb": breadcrumb or None,
                    "char_length": len(final_content),
                    "enriched_char_length": len(enriched_text)
                })
                unique_chunk_id = f"{doc_source}_{global_idx}"

                chunks.append(
                    Chunk(
                        chunk_id=unique_chunk_id,
                        content=final_content,
                        enriched_content=enriched_text,
                        metadata=chunk_meta
                    )
                )
                global_idx += 1
        return chunks
