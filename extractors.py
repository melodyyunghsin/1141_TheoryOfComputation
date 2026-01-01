"""
Claim and Detail Extractors
從文本中提取可驗證的主張和細節
"""
from llm_helpers import call_llm, parse_json_response


def extract_title_and_details(text, language="zh-TW"):
    """
    從新聞文本中提取標題和需要驗證的關鍵細節
    Title = 主要主張
    Details = Content中支撐Title的具體事實
    
    Args:
        text: 新聞文章全文（包含 Title: 和 Content: 標記）
        language: 輸出語言（zh-TW, en, auto）
    
    Returns:
        {"title": str, "details": [str, ...]}
    """
    # 根據語言設定回應語言
    language_instruction = ""
    if language == "zh-TW":
        language_instruction = "CRITICAL: Extract title and details in Traditional Chinese (繁體中文)."
    elif language == "en":
        language_instruction = "CRITICAL: Extract title and details in English."
    else:
        language_instruction = "CRITICAL: Extract title and details in Traditional Chinese (繁體中文)."
    
    system = (
        f"{language_instruction}\n\n"
        "You are analyzing a news article to extract:\n"
        "1. The TITLE (main claim of the article)\n"
        "2. VERIFIABLE DETAILS that DIRECTLY SUPPORT the title's core claim\n\n"
        "CRITICAL RULES:\n"
        "1. Extract ONLY from the provided text - DO NOT add information from your knowledge\n"
        "2. Details must be EXACT quotes or paraphrases from the CONTENT section\n"
        "3. If title claims '3000 police deployed' → find WHERE in content it mentions specific numbers\n"
        "4. DO NOT infer, guess, or add details not explicitly stated in the text\n"
        "5. DO NOT extract peripheral details that don't directly prove the title's main claim\n\n"
        "Details should be:\n"
        "- Specific numbers FOUND IN THE TEXT (e.g., '1300 police', '2900 MRT staff')\n"
        "- Key events MENTIONED IN THE TEXT that directly relate to the title\n"
        "- Evidence FROM THE TEXT that confirms or refutes the title's core assertion\n\n"
        "Extract 2-4 key details (quality over quantity).\n"
        "Ignore: peripheral details, opinions, vague statements, minor supporting facts.\n\n"
        "IMPORTANT: If the content doesn't contain enough specific details to support the title, return fewer details or empty array.\n"
        "DO NOT fabricate or guess details not present in the text.\n\n"
        "Return JSON with fields: title (string), details (array of strings).\n"
        "The extracted title and details MUST be in the language specified above."
    )
    
    out = call_llm(system, text)

    try:
        # Debug: 顯示 LLM 原始回應
        print(f"  LLM Response (first 500 chars): {out[:500]}")
        
        result = parse_json_response(out)
        title = result.get("title", "")
        details = result.get("details", [])
        
        # 確保 details 是 list
        if not isinstance(details, list):
            print(f"  Warning: details is not a list, got {type(details)}")
            details = []
        
        # 限制最多5個細節
        details = details[:5]
        
        print(f"  Extracted: title={title[:50]}..., details count={len(details)}")
        
        return {"title": title, "details": details}
    except Exception as e:
        print(f"  Error parsing LLM response: {e}")
        print(f"  Raw output: {out[:300]}")
        
        # 備用：嘗試從文本中提取Title行
        lines = text.split('\n')
        title = ""
        for line in lines:
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
                break
        
        return {"title": title or "Unknown", "details": []}


def extract_claims(text, language="zh-TW"):
    """
    從一般文字中提取獨立的可驗證主張
    用於：使用者直接輸入一段話，而非完整的新聞文章
    
    Args:
        text: 一般文字內容
        language: 輸出語言（zh-TW, en, auto）
    
    Returns:
        [str, str, ...] - claim 列表
    """
    # 根據語言設定回應語言
    language_instruction = ""
    if language == "zh-TW":
        language_instruction = "CRITICAL: Extract claims in Traditional Chinese (繁體中文)."
    elif language == "en":
        language_instruction = "CRITICAL: Extract claims in English."
    else:
        language_instruction = "CRITICAL: Extract claims in Traditional Chinese (繁體中文)."
    
    system = (
        f"{language_instruction}\n\n"
        "Extract 3-5 verifiable factual claims from the PROVIDED TEXT ONLY.\n\n"
        "CRITICAL: Extract ONLY from the text - DO NOT add information from your knowledge.\n\n"
        "Focus on:\n"
        "- Specific events MENTIONED IN THE TEXT\n"
        "- Concrete numbers or statistics STATED IN THE TEXT\n"
        "- Statements FROM THE TEXT that can be fact-checked\n\n"
        "Ignore:\n"
        "- Opinions or subjective statements\n"
        "- Vague or unclear claims\n"
        "- Repeated information\n"
        "- Information not explicitly present in the text\n\n"
        "DO NOT infer, extrapolate, or add claims based on your general knowledge.\n"
        "If the text contains fewer than 3 verifiable claims, return fewer items.\n\n"
        "Return a JSON array of strings (the claims).\n"
        "The extracted claims MUST be in the language specified above."
    )
    
    try:
        out = call_llm(system, text)
        claims = parse_json_response(out)
        if isinstance(claims, list):
            return claims[:5]  # 最多5個
        return []
    except Exception:
        # 備用：將整段文字當作一個claim
        return [text[:500]]  # 限制長度
