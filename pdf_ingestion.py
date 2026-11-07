"""Bounded, local extraction of PDF study material for retrieval."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader

PDF_EMBEDDING_MODEL = "nomic-embed-text"
MAX_PDF_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 100
MAX_EXTRACTED_CHARS = 50_000


def extract_pdf_documents(
    data: bytes,
    filename: str,
    *,
    max_bytes: int = MAX_PDF_UPLOAD_BYTES,
    max_pages: int = MAX_PDF_PAGES,
    max_chars: int = MAX_EXTRACTED_CHARS,
) -> list[Document]:
    """Extract bounded page-level text documents from an uploaded PDF."""
    if not isinstance(data, bytes):
        raise TypeError("PDF content must be bytes.")
    if not data:
        raise ValueError("The uploaded PDF is empty.")
    if len(data) > max_bytes:
        raise ValueError(f"PDF exceeds the {max_bytes // (1024 * 1024)} MiB upload limit.")
    if not data.startswith(b"%PDF-"):
        raise ValueError("The uploaded file is not a valid PDF.")
    if max_pages < 1 or max_chars < 1:
        raise ValueError("PDF page and extracted-text limits must be positive.")

    try:
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            raise ValueError("Password-protected PDFs are not supported.")
        if len(reader.pages) > max_pages:
            raise ValueError(f"PDF exceeds the {max_pages}-page processing limit.")
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("The PDF could not be read. Check that it is not damaged.") from exc

    source_name = Path(filename).name or "uploaded.pdf"
    documents: list[Document] = []
    remaining = max_chars

    for page_number, page in enumerate(reader.pages, start=1):
        if remaining <= 0:
            break
        try:
            page_text = (page.extract_text() or "").strip()
        except Exception as exc:
            raise ValueError(
                f"Text could not be extracted from PDF page {page_number}."
            ) from exc
        if not page_text:
            continue

        text = page_text[:remaining]
        documents.append(
            Document(
                page_content=text,
                metadata={"source": source_name, "page": page_number},
            )
        )
        remaining -= len(text)

    if not documents:
        raise ValueError(
            "No selectable text was found. Scanned/image-only PDFs need OCR, which this app does not currently provide."
        )
    return documents
