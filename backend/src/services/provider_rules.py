import litellm
from typing import Any, Dict
from src.core.enums import AIProvider

GLOBAL_REGISTRY: Dict[str, Dict[str, Any]] = {p.value: {} for p in AIProvider}


def build_models_registry() -> Dict[str, Dict[str, Any]]:
    allowed_providers = {p.value.lower(): p for p in AIProvider}

    for model_key, metadata in litellm.model_cost.items():
        if "/" not in model_key:
            continue

        raw_provider, model_name = model_key.split("/", 1)
        if raw_provider not in allowed_providers:
            continue

        provider_enum = allowed_providers[raw_provider]

        # Ask LiteLLM dynamically what this specific model supports
        supported_params = litellm.get_supported_openai_params(
            model=model_key, custom_llm_provider=raw_provider
        )

        supports_thinking = "reasoning_effort" in supported_params or metadata.get(
            "supports_reasoning", False
        )

        GLOBAL_REGISTRY[provider_enum.value][model_name] = {
            "supports_thinking": supports_thinking,
            "allowed_levels": ["low", "medium", "high"] if supports_thinking else [],
            "max_input_tokens": metadata.get("max_input_tokens"),
            "max_output_tokens": metadata.get("max_output_tokens"),
        }

    return GLOBAL_REGISTRY
