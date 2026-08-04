import json
import os
import re

try:
    import requests as _req
except ImportError:
    _req = None

def import_chat_url(url, timeout=15):
    """Fetch a chat log from a URL (e.g. a pastebin/gist raw link) and parse
    it the same way as an uploaded file. Supports JSON and plain-text bodies,
    detected from the Content-Type header or the URL's extension."""
    try:
        from core.storage import get_bool_setting
        if get_bool_setting("local_only_mode", False):
            raise RuntimeError(
                "Local-only mode is on (Settings -> Config), so importing from a "
                "link is disabled. Turn it off, or upload the file instead."
            )
    except ImportError:
        pass

    if not _req:
        raise RuntimeError("The 'requests' library isn't installed — run: pip install requests")

    url = url.strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        raise ValueError("Only http:// and https:// links are supported.")

    resp = _req.get(url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "").lower()
    ext = os.path.splitext(url.split("?")[0])[1].lower()

    if "json" in content_type or ext == ".json":
        data = resp.json()
        if isinstance(data, list):
            return normalize_message_list(data)
        if isinstance(data, dict):
            if "messages" in data:
                return normalize_message_list(data["messages"])
            if "chat" in data:
                return normalize_message_list(data["chat"])
        return []

    return parse_plain_text(resp.text)

def import_chat_file(path):
    ext = os.path.splitext(path)[1].lower()

    if ext == ".json":
        return import_json(path)

    if ext == ".txt":
        return parse_plain_text(open(path, "r", encoding="utf-8", errors="ignore").read())

    if ext == ".pdf":
        return import_pdf(path)

    if ext == ".docx":
        return import_docx(path)

    raise ValueError(f"Unsupported file type: {ext}")

def import_json(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    if isinstance(data, list):
        return normalize_message_list(data)

    if isinstance(data, dict):
        if "messages" in data:
            return normalize_message_list(data["messages"])
        if "chat" in data:
            return normalize_message_list(data["chat"])

    return []

def import_pdf(path):
    try:
        from pypdf import PdfReader
    except Exception as exc:
        raise RuntimeError("Install pypdf to import PDF: pip install pypdf") from exc

    reader = PdfReader(path)
    text_parts = []

    for page in reader.pages:
        text_parts.append(page.extract_text() or "")

    return parse_plain_text("\n".join(text_parts))

def import_docx(path):
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("Install python-docx to import DOCX: pip install python-docx") from exc

    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs)
    return parse_plain_text(text)

def normalize_message_list(items):
    messages = []

    for i, item in enumerate(items):
        if isinstance(item, dict):
            speaker = (
                item.get("speaker")
                or item.get("role")
                or item.get("character")
                or item.get("name")
                or "Unknown"
            )
            text = (
                item.get("text")
                or item.get("content")
                or item.get("message")
                or ""
            )
        else:
            speaker = "Unknown"
            text = str(item)

        messages.append({
            "index": i,
            "speaker": str(speaker).strip() or "Unknown",
            "text": str(text).strip(),
        })

    return messages

def parse_plain_text(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    messages = []
    current = None

    speaker_pattern = re.compile(r"^([A-Za-z0-9_ .'-]{1,50})\s*[:：-]\s*(.+)$")

    for line in lines:
        match = speaker_pattern.match(line)

        if match:
            if current:
                messages.append(current)

            speaker = match.group(1).strip()
            body = match.group(2).strip()

            current = {
                "index": len(messages),
                "speaker": speaker,
                "text": body,
            }
        else:
            if current:
                current["text"] += " " + line
            else:
                current = {
                    "index": len(messages),
                    "speaker": "Unknown",
                    "text": line,
                }

    if current:
        messages.append(current)

    for i, msg in enumerate(messages):
        msg["index"] = i

    return messages
