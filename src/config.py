"""
Configuration and LLM initialization helper supporting DeepInfra, Google, and OpenAI.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def get_llm(provider: str = "deepinfra", model_name: str = None, api_key: str = None, temperature: float = 0.2):
    """
    Returns an initialized LangChain chat model based on provider and API key.
    Default provider is DeepInfra with model deepseek-ai/DeepSeek-V4.1-Flash.
    """
    provider = provider.lower()

    if provider == "deepinfra":
        from langchain_openai import ChatOpenAI
        key = api_key or os.getenv("DEEPINFRA_API_KEY") or os.getenv("DEEPINFRA_TOKEN")
        if not key:
            raise ValueError("Vui lòng cung cấp DeepInfra API Key.")
        model = model_name or "deepseek-ai/DeepSeek-V4.1-Flash"
        return ChatOpenAI(
            model=model,
            openai_api_key=key,
            openai_api_base="https://api.deepinfra.com/v1/openai",
            temperature=temperature
        )

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("Vui lòng cung cấp Google/Gemini API Key.")
        model = model_name or "gemini-3.8-flash"
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=key,
            temperature=temperature,
            transport="rest",
            request_timeout=30,
            convert_system_message_to_human=False
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("Vui lòng cung cấp OpenAI API Key.")
        model = model_name or "gpt-4o-mini"
        return ChatOpenAI(
            model=model,
            api_key=key,
            temperature=temperature
        )

    else:
        raise ValueError(f"Provider '{provider}' không được hỗ trợ. Chọn 'deepinfra', 'google' hoặc 'openai'.")
