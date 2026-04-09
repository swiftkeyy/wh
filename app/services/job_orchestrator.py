from app.core.config import settings
from app.infra.ai_providers import ImageGenerationRequest, ProviderRegistry
from app.services.prompt_engine import PromptEngine


class JobOrchestrator:
    def __init__(
        self,
        prompt_engine: PromptEngine | None = None,
        provider_registry: ProviderRegistry | None = None,
    ) -> None:
        self.prompt_engine = prompt_engine or PromptEngine()
        self.provider_registry = provider_registry or ProviderRegistry()

    async def run_generation(
        self,
        mode: str,
        prompt: str,
        source_image_bytes: bytes | None = None,
        locale: str = "ru",
    ) -> dict:
        resolved = self.prompt_engine.resolve(mode=mode, user_prompt=prompt, locale=locale)
        provider_name = "remove_bg" if mode == "transparent_bg" else settings.ai_default_provider
        provider = self.provider_registry.get(provider_name)
        request = ImageGenerationRequest(
            prompt=resolved.final_prompt,
            source_assets=[],
            references=[],
            style_profile=resolved.system_style,
            num_outputs=1,
            source_image_bytes=source_image_bytes,
        )
        result = await provider.generate(request)
        return {
            "provider": provider_name,
            "template_code": resolved.template_code,
            "template_version": resolved.template_version,
            "output_urls": result.output_urls,
            "moderation_flags": result.moderation_flags,
        }
