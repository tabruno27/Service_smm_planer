import re

_DOC_ID_RE = re.compile(r"/d/([a-zA-Z0-9_-]{25,})")

def extract_doc_id(url_or_id: str) -> str | None:
    """Возвращает documentId (строку между /d/ и /edit) или None."""
    m = _DOC_ID_RE.search(url_or_id)
    return m.group(1) if m else url_or_id.strip() or None