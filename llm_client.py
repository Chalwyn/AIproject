import os
from typing import List, Dict, Any
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

def _client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # lazy: don't crash during import-only
        return None
    if OpenAI is None:
        return None
    return OpenAI()

def chat_completion(model: str, messages: List[Dict[str, Any]], **kwargs) -> str:
    client = _client()
    if client is None:
        return ""
    resp = client.chat.completions.create(model=model, messages=messages, **kwargs)
    return resp.choices[0].message.content if resp and resp.choices else ""