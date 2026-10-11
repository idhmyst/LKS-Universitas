"""Membuat objek LLM. Ganti provider/model cukup lewat file .env."""
import os
from functools import lru_cache
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

@lru_cache(maxsize=1)
def get_llm():
    model = os.getenv("LLM_MODEL")
    if not model:
        raise RuntimeError("LLM_MODEL belum diisi di file .env")
    kwargs = {}
    if os.getenv("LLM_TEMPERATURE"):
        kwargs["temperature"] = float(os.getenv("LLM_TEMPERATURE"))
    if os.getenv("LLM_BASE_URL"):
        kwargs["base_url"] = os.getenv("LLM_BASE_URL")
    return init_chat_model(model, **kwargs)