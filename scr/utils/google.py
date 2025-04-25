import re

_DOC_ID_RE = re.compile(r"/d/([a-zA-Z0-9_-]{10,})")

def extract_doc_id(url_or_id: str) -> str | None:
    if not url_or_id:
        return None
    m = _DOC_ID_RE.search(url_or_id)
    doc_id = m.group(1) if m else url_or_id.strip()
    return re.split(r"[/?]", doc_id)[0] or None