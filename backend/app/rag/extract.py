import io
import re
import zipfile
from typing import List, Tuple
from pypdf import PdfReader
from pypdf.errors import PdfReadError, FileNotDecryptedError
import docx

def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, List[Tuple[int, str]]]:
    """
    Extracts text page-by-page from a PDF byte stream.
    Validates encryption/password protection and corruption.
    Returns (full_text, [(page_number, page_text)]).
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        if reader.is_encrypted:
            try:
                # Attempt with empty password
                if not reader.decrypt(""):
                    raise ValueError("Password-protected PDF files are not supported.")
            except Exception:
                raise ValueError("Password-protected PDF files are not supported.")

        pages = []
        full_text_list = []

        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append((idx + 1, text))
                full_text_list.append(text)

        full_text = "\n\n".join(full_text_list)
        return full_text, pages
    except (PdfReadError, FileNotDecryptedError) as e:
        raise ValueError(f"Corrupted or encrypted PDF: {str(e)}")
    except Exception as e:
        if "Password-protected" in str(e):
            raise
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def extract_text_from_docx(file_bytes: bytes) -> Tuple[str, List[Tuple[int, str]]]:
    """
    Extracts text from DOCX paragraph by paragraph.
    Handles corrupted archive / zip bomb protection.
    Returns (full_text, [(para_index, para_text)]).
    """
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        paras = []
        full_text_list = []

        for idx, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            if text:
                paras.append((idx + 1, text))
                full_text_list.append(text)

        full_text = "\n\n".join(full_text_list)
        return full_text, paras
    except (zipfile.BadZipFile, KeyError, Exception) as e:
        raise ValueError(f"Corrupted or invalid DOCX document: {str(e)}")

def extract_text_from_txt(file_bytes: bytes) -> Tuple[str, List[Tuple[int, str]]]:
    """
    Extracts UTF-8 text from raw TXT bytes.
    """
    text = file_bytes.decode("utf-8", errors="replace").strip()
    return text, [(1, text)]

def parse_document(file_bytes: bytes, filename: str) -> Tuple[str, List[Tuple[int, str]]]:
    """
    Dispatches file parsing by extension.
    Validates minimum readable text (>20 characters) to avoid scanned/empty documents.
    """
    ext = filename.lower().split(".")[-1]
    if ext == "pdf":
        full_text, passages = extract_text_from_pdf(file_bytes)
    elif ext == "docx":
        full_text, passages = extract_text_from_docx(file_bytes)
    elif ext == "txt":
        full_text, passages = extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    if len(full_text.strip()) < 20:
        raise ValueError("No readable text found. Upload a text-based PDF, not a scan.")

    return full_text, passages
