"""Unit tests for DocumentProcessor — text extraction, chunking, type detection."""

from __future__ import annotations

import csv
import io

import pytest

from rag_service.core.document_processor import DocumentProcessor


@pytest.fixture
def processor():
    return DocumentProcessor(chunk_size=100, chunk_overlap=10)


class TestSupportedTypes:
    def test_pdf_type_supported(self, processor):
        assert "application/pdf" in processor.SUPPORTED_TYPES

    def test_csv_type_supported(self, processor):
        assert "text/csv" in processor.SUPPORTED_TYPES

    def test_txt_type_supported(self, processor):
        assert "text/plain" in processor.SUPPORTED_TYPES

    def test_md_type_supported(self, processor):
        assert "text/markdown" in processor.SUPPORTED_TYPES

    def test_unsupported_type_raises(self, processor):
        with pytest.raises(ValueError, match="Unsupported"):
            processor.process(b"data", "file.xyz", "application/unknown")


class TestTextExtraction:
    def test_extract_plain_text(self, processor):
        content = b"Hello world, this is a test document."
        result = processor.process(content, "test.txt", "text/plain")
        assert "Hello world" in result.raw_text
        assert result.content_type == "text/plain"

    def test_extract_markdown(self, processor):
        content = b"# Title\n\nSome paragraph text."
        result = processor.process(content, "test.md", "text/markdown")
        assert "# Title" in result.raw_text

    def test_extract_csv(self, processor):
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["name", "email"])
        writer.writerow(["John", "john@test.com"])
        writer.writerow(["Jane", "jane@test.com"])
        content = buf.getvalue().encode("utf-8")

        result = processor.process(content, "data.csv", "text/csv")
        assert "John" in result.raw_text
        assert "jane@test.com" in result.raw_text

    def test_empty_csv(self, processor):
        result = processor.process(b"", "empty.csv", "text/csv")
        assert result.raw_text == ""

    def test_infer_type_from_extension(self, processor):
        content = b"Plain text content"
        result = processor.process(content, "readme.txt", "application/octet-stream")
        assert "Plain text content" in result.raw_text


class TestChunking:
    def test_short_text_single_chunk(self, processor):
        content = b"Short text."
        result = processor.process(content, "test.txt", "text/plain")
        assert len(result.chunks) == 1

    def test_long_text_multiple_chunks(self):
        proc = DocumentProcessor(chunk_size=10, chunk_overlap=2)
        text = "A" * 1000  # 1000 chars, chunk_size=10*4=40 chars
        content = text.encode("utf-8")
        result = proc.process(content, "long.txt", "text/plain")
        assert len(result.chunks) > 1

    def test_chunk_index_sequential(self, processor):
        text = "word " * 500  # Long enough for multiple chunks
        result = processor.process(text.encode(), "test.txt", "text/plain")
        for i, chunk in enumerate(result.chunks):
            assert chunk.chunk_index == i

    def test_chunk_metadata_has_source(self, processor):
        text = "word " * 500
        result = processor.process(text.encode(), "report.txt", "text/plain")
        for chunk in result.chunks:
            assert chunk.metadata["source"] == "report.txt"

    def test_empty_text_no_chunks(self, processor):
        result = processor.process(b"   ", "test.txt", "text/plain")
        assert len(result.chunks) == 0

    def test_overlap_creates_overlapping_content(self):
        proc = DocumentProcessor(chunk_size=10, chunk_overlap=5)
        text = "ABCDE" * 100  # 500 chars with chunk_size=40, overlap=20
        result = proc.process(text.encode(), "test.txt", "text/plain")
        if len(result.chunks) >= 2:
            # Overlap means end of chunk N overlaps with start of chunk N+1
            c1_end = result.chunks[0].metadata["end_char"]
            c2_start = result.chunks[1].metadata["start_char"]
            assert c2_start < c1_end  # Overlap exists


class TestProcessedDocumentMetadata:
    def test_metadata_has_doc_type(self, processor):
        result = processor.process(b"text", "test.txt", "text/plain")
        assert result.metadata["doc_type"] == "txt"

    def test_metadata_has_char_count(self, processor):
        text = b"Hello world"
        result = processor.process(text, "test.txt", "text/plain")
        assert result.metadata["char_count"] == len(text.decode())
