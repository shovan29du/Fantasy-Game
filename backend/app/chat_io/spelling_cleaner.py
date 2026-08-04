import re

COMMON_FIXES = {
    "scenerio": "scenario",
    "cosistancy": "consistency",
    "inregate": "integrate",
    "chatacter": "character",
    "profundi": "profound",
    "achivement": "achievement",
    "charactor": "character",
    "messege": "message",
    "teh": "the",
    "recieve": "receive",
    "seperate": "separate",
    "definately": "definitely",
    "occured": "occurred",
    "untill": "until",
}

def clean_text(text):
    cleaned = text

    for wrong, right in COMMON_FIXES.items():
        cleaned = re.sub(rf"\b{wrong}\b", right, cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def clean_chat_messages(chat):
    cleaned = []

    for msg in chat:
        item = dict(msg)
        item["speaker"] = clean_text(str(item.get("speaker", "Unknown")))
        item["text"] = clean_text(str(item.get("text", "")))
        cleaned.append(item)

    return cleaned
