
import os

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def read_pdf(pdf_path):

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if os.path.getsize(pdf_path) == 0:
        raise ValueError(f"PDF file is empty: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
    except Exception as error:
        raise ValueError(f"Unable to read PDF: {error}")

    if reader.is_encrypted:
        raise ValueError(f"PDF is password protected: {pdf_path}")

    return reader


def extract_text_from_pdf(pdf_path):

    reader = read_pdf(pdf_path)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text()

        if text and text.strip():
            pages.append({
                "text": text,
                "source": pdf_path,
                "page": page_number
            })

    if not pages:
        raise ValueError(
            f"No extractable text found in PDF: {pdf_path}"
        )

    return pages


def get_pdf_metadata(pdf_path):

    reader = read_pdf(pdf_path)

    file_size = os.path.getsize(pdf_path)

    return {
        "filename": os.path.basename(pdf_path),
        "total_pages": len(reader.pages),
        "file_size_kb": round(file_size / 1024, 2),
        "file_size_mb": round(file_size / (1024 * 1024), 2)
    }


def get_pdf_page_preview(pdf_path, page_number):

    reader = read_pdf(pdf_path)

    if page_number < 1 or page_number > len(reader.pages):
        raise ValueError("Invalid page number.")

    text = reader.pages[page_number - 1].extract_text()

    if not text or not text.strip():
        return "No extractable text on this page."

    return text


def split_text_into_chunks(pages):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    all_chunks = []

    for page in pages:

        chunks = text_splitter.split_text(page["text"])

        for chunk in chunks:
            all_chunks.append({
                "text": chunk,
                "source": page["source"],
                "page": page["page"]
            })

    return all_chunks
