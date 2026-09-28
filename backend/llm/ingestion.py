"""
Fetches an external link and returns extracted plain text - handles both
regular HTML pages and PDFs. Failures return "" rather than raising, since
one bad link shouldn't take down the whole generation job.
"""
import io
import httpx
from bs4 import BeautifulSoup
import pdfplumber


async def fetch_link_text(url: str) -> str:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
    except Exception:
        return ""

    content_type = resp.headers.get("content-type", "").lower()
    is_pdf = "application/pdf" in content_type or url.lower().endswith(".pdf")

    if is_pdf:
        return _extract_pdf_text(resp.content)
    return _extract_html_text(resp.text)


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    text_parts = []
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception:
        return ""
    return "\n".join(text_parts)


def _extract_html_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def chunk_text(text: str, chunk_size: int = 500) -> list:
    """Splits text into ~chunk_size-word passages."""
    words = text.split()
    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
        if words[i:i + chunk_size]
    ]