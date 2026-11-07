"""Chooses the chat model from settings. Gemini is the default; Ollama is the free local fallback."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

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
    raise ValueError(f"unknown MODEL_PROVIDER: {settings.model_provider}")
