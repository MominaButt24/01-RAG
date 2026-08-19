
# Ingestion stage: turns a raw file (pdf/docx/pptx/xlsx) into a list of chunks.

# Each chunk is a dict: {"text": ..., "source": ...}
# "source" is what lets you point back to exactly which page/slide/row an
# answer came from later, at generation time


import os
from pptx import Presentation
from docx2pdf import convert
from langchain_community.document_loaders import PyPDFLoader, UnstructuredExcelLoader

from src.config import CHUNK_CHAR_CAP


def _split_capped(text: str, label_prefix: str, chunks: list):
    
    for start in range(0, len(text), CHUNK_CHAR_CAP):
        part_num = start // CHUNK_CHAR_CAP + 1
        piece = text[start : start + CHUNK_CHAR_CAP]
        chunks.append({"text": piece, "source": f"{label_prefix} (part {part_num})"})


def _process_xlsx(file_path: str) -> list:
    
    chunks = []
    loader = UnstructuredExcelLoader(file_path, mode="elements")
    documents = loader.load()

    for doc in documents:
        text = doc.page_content.strip()
        sheet_name = doc.metadata.get("page_name", "unknown_sheet")
        if text:
            _split_capped(text, f"Sheet '{sheet_name}'", chunks)

    return chunks


def _process_pptx(file_path: str) -> list:
    chunks = []
    prs = Presentation(file_path)
    for i, slide in enumerate(prs.slides):
        text_parts = []

        for shape in slide.shapes:
            if shape.has_text_frame:
                for p in shape.text_frame.paragraphs:
                    if p.text.strip():
                        text_parts.append(p.text.strip())
            elif shape.has_table:
                table = shape.table
                for row in table.rows:
                    row_text = " | ".join(
                        cell.text.strip() for cell in row.cells if cell.text.strip()
                    )
                    if row_text:
                        text_parts.append(row_text)

        if slide.has_notes_slide:
            notes_text = slide.notes_slide.notes_text_frame.text.strip()
            if notes_text:
                text_parts.append("Notes: " + notes_text)

        full_text = "\n".join(text_parts)
        if full_text:
            _split_capped(full_text, f"Slide {i + 1}", chunks)
    return chunks


def _process_pdf_or_docx(file_path: str) -> list:
   
    chunks = []
    pdf_to_read = file_path
    temp_pdf = False

    if file_path.endswith(".docx"):
        pdf_to_read = file_path.replace(".docx", "_temp.pdf")
        try:
            convert(file_path, pdf_to_read)
        except Exception:
            if not os.path.exists(pdf_to_read):
                raise
        temp_pdf = True

    loader = PyPDFLoader(pdf_to_read)
    documents = loader.load()  # one Document per page

    for doc in documents:
        text = doc.page_content.strip()
        page_num = doc.metadata["page"] + 1  # LangChain pages are 0-indexed
        if text:
            _split_capped(text, f"Page {page_num}", chunks)

    if temp_pdf and os.path.exists(pdf_to_read):
        os.remove(pdf_to_read)

    return chunks


def process_file(file_path: str) -> list:
    
    if file_path.endswith(".xlsx"):
        return _process_xlsx(file_path)
    elif file_path.endswith(".pptx"):
        return _process_pptx(file_path)
    elif file_path.endswith((".pdf", ".docx")):
        return _process_pdf_or_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
