from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class ResolvedPrompt:
    system_style: str
    final_prompt: str
    template_code: str | None
    template_version: str
    moderation_tags: list[str]


class PromptEngine:
    def __init__(self, catalog_path: Path | None = None) -> None:
        self.catalog_path = catalog_path or Path(__file__).resolve().parents[1] / "prompts" / "catalog.json"
        self.catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))

    def resolve(self, mode: str, user_prompt: str, locale: str = "ru") -> ResolvedPrompt:
        template = next((item for item in self.catalog["templates"] if item["code"] == mode), None)
        if not template:
            return ResolvedPrompt(
                system_style="clean_commercial_image",
                final_prompt=user_prompt.strip(),
                template_code=None,
                template_version=self.catalog["library_version"],
                moderation_tags=["general"],
            )

        locale_payload = template["locales"].get(locale, template["locales"]["en"])
        final_prompt = locale_payload["prompt_prefix"].strip() + "\n" + user_prompt.strip()
        return ResolvedPrompt(
            system_style=template["style_profile"],
            final_prompt=final_prompt,
            template_code=template["code"],
            template_version=template["version"],
            moderation_tags=template["moderation_tags"],
        )
