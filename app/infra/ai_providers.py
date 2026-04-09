from dataclasses import dataclass
from io import BytesIO
from typing import Protocol

import httpx
from google.genai import Client
from google.genai import types as genai_types
from PIL import Image

from app.core.config import settings


@dataclass
class ImageGenerationRequest:
    prompt: str
    source_assets: list[str]
    references: list[str]
    style_profile: str
    num_outputs: int = 1
    source_image_bytes: bytes | None = None
    mime_type: str = "image/png"


@dataclass
class GeneratedAsset:
    bytes_data: bytes | None
    mime_type: str
    external_url: str | None = None
    width: int | None = None
    height: int | None = None


@dataclass
class ImageGenerationResult:
    provider_job_id: str
    assets: list[GeneratedAsset]
    moderation_flags: list[str]


class ImageProvider(Protocol):
    provider_name: str

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        ...


class MockImageProvider:
    provider_name = "mock_provider"

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        return ImageGenerationResult(
            provider_job_id="mock-job-1",
            assets=[GeneratedAsset(bytes_data=None, mime_type="image/png", external_url="https://example.com/mock-output.png")],
            moderation_flags=[],
        )


class RemoveBgProvider:
    provider_name = "remove_bg"
    endpoint = "https://api.remove.bg/v1.0/removebg"

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not settings.remove_bg_api_key:
            raise ValueError("REMOVE_BG_API_KEY is not configured")
        if not request.source_image_bytes:
            raise ValueError("remove.bg requires source_image_bytes")

        files = {
            "image_file": ("input.png", request.source_image_bytes, request.mime_type),
        }
        data = {"size": "auto"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.endpoint,
                headers={"X-Api-Key": settings.remove_bg_api_key},
                files=files,
                data=data,
            )
            response.raise_for_status()
            output_bytes = response.content

        output_url = request.source_assets[0] if request.source_assets else "generated://remove-bg-result"
        image = Image.open(BytesIO(output_bytes))
        width, height = image.size
        return ImageGenerationResult(
            provider_job_id="removebg-inline",
            assets=[
                GeneratedAsset(
                    bytes_data=output_bytes,
                    mime_type="image/png",
                    external_url=output_url,
                    width=width,
                    height=height,
                )
            ],
            moderation_flags=[f"width:{width}", f"height:{height}"],
        )


class GeminiImageProvider:
    provider_name = "gemini_image"

    def __init__(self, model_name: str = "gemini-2.5-flash-image-preview") -> None:
        self.model_name = model_name

    async def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        if not settings.google_genai_api_key:
            raise ValueError("GOOGLE_GENAI_API_KEY is not configured")

        client = Client(api_key=settings.google_genai_api_key)
        parts: list[str | genai_types.Part] = [request.prompt]
        if request.source_image_bytes:
            parts.append(
                genai_types.Part.from_bytes(
                    data=request.source_image_bytes,
                    mime_type=request.mime_type,
                )
            )

        response = await client.aio.models.generate_content(
            model=self.model_name,
            contents=parts,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        output_count = 0
        for candidate in response.candidates or []:
            for part in candidate.content.parts or []:
                if getattr(part, "inline_data", None):
                    output_count += 1

        return ImageGenerationResult(
            provider_job_id=response.response_id or "gemini-inline",
            assets=[
                GeneratedAsset(
                    bytes_data=None,
                    mime_type="image/png",
                    external_url=f"generated://gemini/{idx}",
                )
                for idx in range(output_count or 1)
            ],
            moderation_flags=[],
        )


class ProviderRegistry:
    def __init__(self) -> None:
        self.providers = {
            "mock_provider": MockImageProvider(),
            "remove_bg": RemoveBgProvider(),
            "gemini_image": GeminiImageProvider(),
        }

    def get(self, provider_name: str) -> ImageProvider:
        provider = self.providers.get(provider_name)
        if not provider:
            raise KeyError(f"Provider '{provider_name}' is not registered")
        return provider
