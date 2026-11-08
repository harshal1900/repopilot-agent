"""Chooses the chat model from settings. Gemini is the default; Ollama is the free local fallback."""

import os

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from repopilot.config import Settings


# One function chooses the model. Agents only call get_model, so switching provider means changing .env, not the agents.
def get_model(settings: Settings) -> BaseChatModel:
    if settings.model_provider == "google":
        # init_chat_model creates a chat model from a 'provider:model' string. The prefix google_genai selects the Gemini integration.
        return init_chat_model(f"google_genai:{settings.model_name}")
    if settings.model_provider == "ollama":
        # The import sits inside the if-block, so the Ollama package loads only when it is used.
        from langchain_ollama import ChatOllama

        return ChatOllama(model=settings.model_name)
    if settings.model_provider == "deepseek":
        return ChatOpenAI(
            model=settings.model_name,
            api_key=os.environ["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com",
        )
    # OpenAI-compatible providers: (base URL, environment variable holding the key).
    openai_compatible = {
        "deepseek": ("https://api.deepseek.com", "DEEPSEEK_API_KEY"),
        "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
        "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
        "cerebras": ("https://api.cerebras.ai/v1", "CEREBRAS_API_KEY"),
    }
    if settings.model_provider in openai_compatible:
        from langchain_openai import ChatOpenAI

        base_url, key_name = openai_compatible[settings.model_provider]
        return ChatOpenAI(
            model=settings.model_name,
            api_key=os.environ[key_name],
            base_url=base_url,
        )
    raise ValueError(f"unknown MODEL_PROVIDER: {settings.model_provider}")
