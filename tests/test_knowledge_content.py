"""D&D reference docs and the auto-generated character-options document."""
from pathlib import Path

from core.character_data import generate_character_options_doc, DND_RACES, PROFESSIONS

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent / "knowledge"


def test_dnd_reference_docs_exist_and_are_nonempty():
    dnd_dir = KNOWLEDGE_DIR / "dnd"
    docs = sorted(dnd_dir.glob("*.md"))
    assert len(docs) >= 8
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        assert len(text) > 500, f"{doc.name} looks too short to be a real reference doc"


def test_character_options_doc_covers_every_race():
    doc = generate_character_options_doc()
    for race_name in DND_RACES:
        assert race_name in doc


def test_character_options_doc_covers_professions():
    doc = generate_character_options_doc()
    for prof in PROFESSIONS[:10]:
        assert prof in doc


def test_character_options_doc_is_indexable_by_knowledge_base(temp_db):
    from core.knowledge_base import index_file, search_knowledge
    import tempfile
    doc = generate_character_options_doc()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(doc)
        path = f.name
    assert index_file(path) is True
    results = search_knowledge("Elf")
    assert results
