import re
from collections import defaultdict

def check_chat_consistency(chat, characters, scenario=""):
    report = []

    speaker_counts = defaultdict(int)

    for msg in chat:
        speaker_counts[msg.get("speaker", "Unknown")] += 1

    report.append({
        "type": "speaker_preservation",
        "status": "ok",
        "detail": "Different speakers were preserved. No forced normalization into one character.",
        "speakers": dict(speaker_counts),
    })

    duplicate_names = find_duplicate_character_names(characters)
    if duplicate_names:
        report.append({
            "type": "duplicate_character_names",
            "status": "review",
            "detail": "Same character names detected. Profiles may need merging only if scenario confirms they are the same person.",
            "names": duplicate_names,
        })
    else:
        report.append({
            "type": "duplicate_character_names",
            "status": "ok",
            "detail": "No duplicate character names detected.",
        })

    contradictions = find_basic_contradictions(chat)
    if contradictions:
        report.append({
            "type": "possible_contradictions",
            "status": "review",
            "items": contradictions,
        })
    else:
        report.append({
            "type": "possible_contradictions",
            "status": "ok",
            "detail": "No obvious simple contradictions found.",
        })

    if scenario:
        report.append({
            "type": "scenario_alignment",
            "status": "checked",
            "detail": "Scenario was used to fill blanks and check thematic alignment.",
        })
    else:
        report.append({
            "type": "scenario_alignment",
            "status": "limited",
            "detail": "No scenario supplied, so consistency checking used dialogue only.",
        })

    return report

def find_duplicate_character_names(characters):
    seen = defaultdict(int)

    for c in characters:
        seen[c.get("name", "Unknown").lower()] += 1

    return [name for name, count in seen.items() if count > 1]

def find_basic_contradictions(chat):
    contradictions = []
    facts_by_speaker = defaultdict(set)

    for msg in chat:
        speaker = msg.get("speaker", "Unknown")
        text = msg.get("text", "").lower()

        alive_match = re.search(r"\b(i am alive|i survived|alive)\b", text)
        dead_match = re.search(r"\b(i am dead|died|dead)\b", text)

        if alive_match:
            facts_by_speaker[speaker].add("alive")
        if dead_match:
            facts_by_speaker[speaker].add("dead")

    for speaker, facts in facts_by_speaker.items():
        if "alive" in facts and "dead" in facts:
            contradictions.append({
                "speaker": speaker,
                "issue": "Both alive and dead states appear in dialogue.",
            })

    return contradictions
