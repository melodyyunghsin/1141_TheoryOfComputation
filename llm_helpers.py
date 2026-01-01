"""
LLM Helper Functions
提供 LLM API 調用和回應解析的統一介面
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = "gpt-oss:20b"


def call_llm(system_prompt, user_prompt):
    """
    調用 LLM API 並返回回應內容
    
    Args:
        system_prompt: 系統提示詞
        user_prompt: 使用者提示詞
    
    Returns:
        LLM 的回應文本
    """
    if not API_KEY:
        raise RuntimeError("API_KEY not set")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
    }
    
    r = requests.post(
        f"{API_BASE_URL}/api/chat",
        headers=headers,
        json=payload,
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"]


def parse_json_response(llm_output):
    """
    清理 LLM 回應中的 markdown 代碼塊並解析 JSON
    處理 ```json ... ``` 或 ``` ... ``` 包裹的情況
    
    Args:
        llm_output: LLM 的原始輸出文本
    
    Returns:
        解析後的 Python 對象（dict 或 list）
    """
    cleaned = llm_output.strip()
    
    # 移除 markdown 代碼塊標記
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    cleaned = cleaned.strip()
    
    return json.loads(cleaned)
