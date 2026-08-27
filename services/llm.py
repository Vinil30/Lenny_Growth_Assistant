import requests
from utils.config import settings


class LLMError(RuntimeError):
    pass


class LLMProvider:
    name = "base"

    def generate(self, prompt: str, fast=False, temperature=0.2, max_tokens=900) -> str:
        raise NotImplementedError


class GroqProvider(LLMProvider):
    name = "groq"

    def generate(self, prompt, fast=False, temperature=0.2, max_tokens=900):
        if not settings.groq_api_key:
            raise LLMError("GROQ_API_KEY is not configured.")
        model = settings.groq_fast_model if fast else settings.groq_main_model
        if not model:
            raise LLMError("Groq model is not configured.")
        res = requests.post(
            f"{settings.groq_base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": temperature, "max_tokens": max_tokens},
            timeout=settings.request_timeout_seconds,
        )
        if res.status_code >= 400:
            raise LLMError(f"Groq request failed: {res.status_code}")
        return res.json()["choices"][0]["message"]["content"]


class OllamaProvider(LLMProvider):
    name = "ollama"

    def generate(self, prompt, fast=False, temperature=0.2, max_tokens=900):
        model = settings.ollama_fast_model if fast else settings.ollama_main_model
        res = requests.post(
            f"{settings.ollama_base_url.rstrip('/')}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "options": {"temperature": temperature, "num_predict": max_tokens}},
            timeout=settings.request_timeout_seconds,
        )
        if res.status_code >= 400:
            raise LLMError(f"Ollama request failed: {res.status_code}. Is Ollama running and is the model pulled?")
        data = res.json()
        return data.get("response", "")


class MockProvider(LLMProvider):
    name = "mock"

    def generate(self, prompt, fast=False, temperature=0.2, max_tokens=900):
        return "Mock response grounded in the supplied context."


def get_llm_provider():
    if settings.llm_provider == "groq":
        return GroqProvider()
    if settings.llm_provider == "mock":
        return MockProvider()
    return OllamaProvider()
