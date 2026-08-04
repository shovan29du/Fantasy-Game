from collections import defaultdict
import re

def build_characters_from_chat(chat, scenario="", main_character_name=""):
    by_speaker = defaultdict(list)

    for msg in chat:
        speaker = msg.get("speaker") or "Unknown"
        by_speaker[speaker].append(msg.get("text", ""))

    characters = []

    for speaker, lines in by_speaker.items():
        if speaker.lower() in ["system", "assistant", "user"] and main_character_name:
            inferred_name = main_character_name
        else:
            inferred_name = speaker

        profile = {
            "name": inferred_name,
            "source_speaker_label": speaker,
            "scenario_alignment": infer_scenario_alignment(lines, scenario),
            "personality": infer_personality(lines),
            "role": infer_role(lines, scenario),
            "speaking_style": infer_speaking_style(lines),
            "known_goals": infer_goals(lines),
            "blank_fields_filled_from_chat": True,
            "dialogue_preserved": True,
            "note": "Dialogue was preserved per speaker; no global voice normalization applied.",
        }

        characters.append(profile)

    return characters

def infer_personality(lines):
    joined = " ".join(lines).lower()

    traits = []

    if any(w in joined for w in ["protect", "help", "save"]):
        traits.append("protective")

    if any(w in joined for w in ["gold", "profit", "trade", "merchant"]):
        traits.append("practical")

    if any(w in joined for w in ["fight", "attack", "battle"]):
        traits.append("bold")

    if any(w in joined for w in ["plan", "strategy", "wait"]):
        traits.append("strategic")

    return traits or ["context-dependent"]

def infer_role(lines, scenario):
    joined = (" ".join(lines) + " " + scenario).lower()

    if "merchant" in joined or "trade" in joined:
        return "merchant / trader"

    if "guard" in joined or "soldier" in joined:
        return "guard / fighter"

    if "king" in joined or "queen" in joined or "faction" in joined:
        return "leader / faction figure"

    if "magic" in joined or "spell" in joined:
        return "magic user"

    return "character inferred from chat"

def infer_speaking_style(lines):
    joined = " ".join(lines)

    avg_len = sum(len(x.split()) for x in lines) / max(len(lines), 1)

    if avg_len < 8:
        return "short and direct"

    if "!" in joined:
        return "emotional / expressive"

    if "?" in joined:
        return "question-driven"

    return "balanced conversational"

def infer_goals(lines):
    joined = " ".join(lines).lower()
    goals = []

    if "survive" in joined or "safe" in joined:
        goals.append("survive")

    if "profit" in joined or "gold" in joined or "trade" in joined:
        goals.append("profit")

    if "trust" in joined or "loyal" in joined:
        goals.append("loyalty")

    if "quest" in joined or "mission" in joined:
        goals.append("complete quest")

    return goals or ["continue role in scenario"]

def infer_scenario_alignment(lines, scenario):
    if not scenario:
        return "No scenario supplied; aligned only to imported dialogue."

    scenario_words = set(re.findall(r"[a-zA-Z]{4,}", scenario.lower()))
    line_words = set(re.findall(r"[a-zA-Z]{4,}", " ".join(lines).lower()))

    overlap = sorted(scenario_words.intersection(line_words))

    return {
        "shared_terms": overlap[:20],
        "alignment_score": round(len(overlap) / max(len(scenario_words), 1), 2),
    }
