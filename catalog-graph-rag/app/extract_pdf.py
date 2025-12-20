import fitz
import pdfplumber

def extract_pages(pdf_path: str) -> list[dict]:
    pages = []
    pdf = fitz.open(pdf_path)
    with pdfplumber.open(pdf_path) as pl:
        for i in range(len(pdf)):
            text = (pdf[i].get_text() or "").strip()
            tables = pl.pages[i].extract_tables() or []
            table_text = "\n".join(
                [" | ".join([c for c in row if c]) for t in tables for row in t if row]
            ).strip()
            pages.append({"page_no": i+1, "text": text, "tables": table_text})
    return pages
