from io import BytesIO
import unittest

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from pdf_ingestion import PDF_EMBEDDING_MODEL, extract_pdf_documents


def make_pdf(page_count=1, text="Important study note"):
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=612, height=792)

    if text:
        page = writer.pages[0]
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        font_ref = writer._add_object(font)
        resources = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
        })
        page[NameObject("/Resources")] = resources

        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)

    output = BytesIO()
    writer.write(output)
    return output.getvalue()


class PdfIngestionTests(unittest.TestCase):
    def test_uses_a_dedicated_embedding_model_separate_from_chat_models(self):
        self.assertEqual(PDF_EMBEDDING_MODEL, "nomic-embed-text")

    def test_extracts_text_with_source_and_page_metadata(self):
        documents = extract_pdf_documents(make_pdf(), "lecture-notes.pdf")

        self.assertEqual(len(documents), 1)
        self.assertIn("Important study note", documents[0].page_content)
        self.assertEqual(documents[0].metadata, {"source": "lecture-notes.pdf", "page": 1})

    def test_caps_extracted_text(self):
        documents = extract_pdf_documents(
            make_pdf(text="A long study note"),
            "notes.pdf",
            max_chars=6,
        )

        self.assertEqual(len(documents[0].page_content), 6)

    def test_rejects_file_above_upload_limit_before_pdf_parsing(self):
        with self.assertRaisesRegex(ValueError, "upload limit"):
            extract_pdf_documents(b"%PDF-" + b"x" * 100, "large.pdf", max_bytes=20)

    def test_rejects_non_pdf_content(self):
        with self.assertRaisesRegex(ValueError, "not a valid PDF"):
            extract_pdf_documents(b"not a PDF", "notes.pdf")

    def test_rejects_documents_above_page_limit(self):
        with self.assertRaisesRegex(ValueError, "page processing limit"):
            extract_pdf_documents(make_pdf(page_count=2, text=""), "long.pdf", max_pages=1)

    def test_rejects_image_only_or_empty_text_documents(self):
        with self.assertRaisesRegex(ValueError, "No selectable text"):
            extract_pdf_documents(make_pdf(text=""), "scan.pdf")

    def test_rejects_empty_payload(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            extract_pdf_documents(b"", "empty.pdf")


if __name__ == "__main__":
    unittest.main()
