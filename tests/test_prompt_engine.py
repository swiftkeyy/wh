from app.services.prompt_engine import PromptEngine


def test_prompt_engine_resolves_known_template() -> None:
    engine = PromptEngine()
    result = engine.resolve("photo_enhance", "Сделай свет мягче", locale="ru")
    assert result.template_code == "photo_enhance"
    assert "Сделай свет мягче" in result.final_prompt
