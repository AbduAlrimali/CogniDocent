from typing import Optional
import base64
import litellm
from src.core.interfaces.ivision_provider import IVisionProvider
from src.core.dtos.llm_provider_dtos import LLMRouteConfigDTO


class LiteLLMVisionProvider(IVisionProvider):
    def __init__(self, config: Optional[LLMRouteConfigDTO] = None) -> None:
        self.config = config

    async def extract_markdown(
        self, image_bytes: bytes, config: Optional[LLMRouteConfigDTO] = None
    ) -> str:
        active_config = config or self.config
        if not active_config:
            raise ValueError("LLMRouteConfigDTO must be provided to extract_markdown or on initialization.")

        # 1. Base64 encode the PNG bytes for the LiteLLM payload
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:image/png;base64,{b64_image}"

        # 2. Strict system prompt forcing Markdown structure and detailed image description in reading order
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an expert document parser. Convert this document image into clean, structured Markdown. "
                    "Perfectly preserve all tables, headers, lists, and reading order. "
                    "Whenever you encounter images, figures, charts, diagrams, or visual illustrations in the page, "
                    "describe them thoroughly and accurately in-place within the Markdown text matching the natural reading order. "
                    "Do not add conversational text."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}}
                ],
            },
        ]

        # 3. Route through LiteLLM using the dedicated vision model config
        response = await litellm.acompletion(
            model=active_config.model_name,
            messages=messages,
            api_key=active_config.api_key,
            api_base=active_config.base_url,
            temperature=0.0,  # Force deterministic extraction
        )

        return response.choices[0].message.content
