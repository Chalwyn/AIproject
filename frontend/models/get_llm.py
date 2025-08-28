from typing import List, Dict, Any
from llm_client import chat_completion

def get_llm(model_name: str = "gpt-4o-mini"):
    def summarize_conversation(messages: List[Dict[str, Any]]) -> str:
        text = chat_completion(model_name, messages, temperature=0.5)
        return text or ""
    return summarize_conversation
