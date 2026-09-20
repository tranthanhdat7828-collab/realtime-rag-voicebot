import re
from backend.schemas.document import Document


class CleanerService:
    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        text = re.sub(r"(\b\w+)-\n\s*(\w+\b)", r"\1\2", text)
        text = re.sub(
            r"(?i)\b(trang|page)\s*\d+\s*(/|of|\-)\s*\d+\b", "", text)
        text = re.sub(r"^[ \t]*[•●○◆■–—]\s*", "- ", text, flags=re.MULTILINE)

        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            cleaned_line = line.rstrip()
            if not cleaned_line.strip().startswith("|"):
                cleaned_line = re.sub(r"[ \t]{2,}", " ", cleaned_line)
            cleaned_lines.append(cleaned_line)

        text = "\n".join(cleaned_lines)
        text = re.sub(
            r"(?<![.!?:;\n|#\-])\n(?!\s*([#\-*|]|\d+\.))\s*", " ", text)
        text = re.sub(r"[ \t]+([,.!?;:])", r"\1", text)
        text = re.sub(r"([,;])([^\s\d])", r"\1 \2", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def clean(document: Document) -> Document:
        return Document(
            content=CleanerService.clean_text(document.content),
            metadata=document.metadata
        )
