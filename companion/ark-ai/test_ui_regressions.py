from pathlib import Path


HTML = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")


def test_prompt_cards_use_id_lookup_instead_of_inline_prompt_json():
    assert "const PROMPT_BY_ID=new Map(" in HTML
    assert 'data-pid="${esc(String(p.id))}"' in HTML
    assert "usePromptById(card.dataset.pid)" in HTML
    assert "JSON.stringify(p.prompt)" not in HTML


def test_lm_studio_pill_is_visible_before_first_poll():
    pill = HTML.split('id="lmsPill"', 1)[1].split(">", 1)[0]
    assert "display:flex" in pill
    assert "display:none" not in pill
    assert '<span id="lmsPillText">LM Studio</span>' in HTML
