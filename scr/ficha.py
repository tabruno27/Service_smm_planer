import re


def format_text(text: str) -> str:
    text = text.replace(" - ", " – ")
    text = re.sub(r'”|’|\"', '»', text)
    text = re.sub(r'“|”|\"', '«', text)
    text = ' '.join(text.split())
    return text
