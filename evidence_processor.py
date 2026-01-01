"""
Evidence Processor
處理證據搜尋、過濾、分析和驗證
"""
from llm_helpers import call_llm, parse_json_response
from qa_tool import web_search


def generate_search_query(claim):
    """
    從claim中提取最佳搜尋關鍵字
    
    Args:
        claim: 待驗證的主張
    
    Returns:
        優化後的搜尋查詢字串
    """
    system = (
        "Extract the most important keywords for fact-checking this claim.\n"
        "CRITICAL: Keep the query in the SAME LANGUAGE as the claim.\n"
        "- If claim is in Chinese → return Chinese keywords\n"
        "- If claim is in English → return English keywords\n\n"
        "Return ONLY 2-4 key terms that would help find relevant evidence.\n"
        "Focus on:\n"
        "- Names of people, organizations, places\n"
        "- Specific events or policies\n"
        "- Dates or time periods\n"
        "- Core factual assertions\n\n"
        "MUST include location keywords if present (e.g., 台北, 台灣, Beijing, Taiwan)\n"
        "Remove: opinions, adjectives, unnecessary words.\n"
        "Return as a simple search query string (not JSON)."
    )
    
    try:
        query = call_llm(system, f"Claim: {claim}")
        # 清理回應，移除引號和多餘空白
        query = query.strip().strip('"').strip("'")
        
        # 強制加入地域關鍵字（如果claim中有但query中沒有）
        location_keywords = ['台北', '臺北', '台中', '臺中', '台南', '臺南', '高雄', '台灣', '臺灣', 'Taipei', 'Taichung', 'Tainan', 'Kaohsiung', 'Taiwan']
        for loc in location_keywords:
            if loc in claim and loc not in query:
                query = f"{loc} {query}"
                break
        
        return query if len(query) > 0 else claim
    except Exception:
        # 備用：直接使用claim
        return claim


def is_evidence_potentially_relevant(claim, evidence_title, evidence_body):
    """
    快速預過濾：只過濾明顯錯誤地點的證據
    
    Args:
        claim: 待驗證的主張
        evidence_title: 證據標題
        evidence_body: 證據內容
    
    Returns:
        True 保留，False 過濾掉
    """
    evidence_text = (evidence_title + " " + evidence_body)
    
    # 檢測claim中的台灣相關地點
    taiwan_locations = ['台北', '臺北', '台中', '臺中', '台南', '臺南', '高雄', '台灣', '臺灣', '新北']
    has_taiwan_location = any(loc in claim for loc in taiwan_locations)
    
    # 如果claim提到台灣地點，但證據提到明顯不相關的國外地點，則過濾
    if has_taiwan_location:
        irrelevant_locations = [
            'San Diego', 'Beijing', '北京', 'Shanghai', '上海', 
            'Hong Kong', '香港', 'Tokyo', '東京', 'Seoul', '首爾',
            'Singapore', '新加坡', 'London', 'New York', 'Paris'
        ]
        # 檢查是否有明顯衝突的地點（同時出現在證據中但不在claim中）
        for irrelevant_loc in irrelevant_locations:
            if irrelevant_loc in evidence_text and irrelevant_loc not in claim:
                return False
    
    # 預設：保留證據給LLM分析（寬鬆策略）
    return True


def analyze_evidence_stance(claim, evidence_title, evidence_body):
    """
    判斷單個證據與claim的關係：支持/反駁/無關
    
    Args:
        claim: 待驗證的主張
        evidence_title: 證據標題
        evidence_body: 證據內容
    
    Returns:
        "support" | "refute" | "irrelevant"
    """
    system = (
        "Analyze if the evidence supports, refutes, or is irrelevant to the claim.\n"
        "Return ONLY one word: support / refute / irrelevant\n"
        "Do not explain, just return the single word."
    )
    
    user = f"Claim: {claim}\n\nEvidence:\nTitle: {evidence_title}\nContent: {evidence_body}"
    
    try:
        result = call_llm(system, user).strip().lower()
        # 標準化回應
        if "support" in result:
            return "support"
        elif "refute" in result or "contradict" in result:
            return "refute"
        else:
            return "irrelevant"
    except Exception:
        return "irrelevant"


def verify_claim(claim, language="zh-TW"):
    """
    驗證單個主張
    
    Args:
        claim: 待驗證的主張
        language: 回應語言
    
    Returns:
        {
            "verdict": "Supported" | "Contradicted" | "Insufficient evidence",
            "explanation": str,
            "evidence_count": int,
            "search_query": str,
            "evidence_breakdown": {"support": int, "refute": int, "irrelevant": int}
        }
    """
    # 初始化預設值，避免變數未定義
    search_query = claim
    valid_results = []
    
    try:
        # 先生成更精準的搜尋查詢
        search_query = generate_search_query(claim)
        print(f"  → 搜尋關鍵字: {search_query}")
    except Exception as e:
        print(f"  Warning: Search query generation failed ({e}), using original claim")
        search_query = claim
    
    try:
        # 搜尋至少10個結果
        search_results = web_search(search_query, max_results=10)
        
        # 過濾有效結果
        valid_results = [r for r in search_results if r.get('title') and r.get('body')]
    except Exception as e:
        print(f"  Error: Search failed ({e})")
        return {
            "verdict": "Insufficient evidence",
            "explanation": f"Search error: {str(e)}",
            "evidence_count": 0,
            "search_query": search_query
        }
    
    # 即使少於3個也繼續分析，但會在結果中註明
    evidence_warning = ""
    if len(valid_results) < 3:
        evidence_warning = f"[Warning] Only found {len(valid_results)} evidence source(s). Recommended: at least 3 sources."
    
    if len(valid_results) == 0:
        return {
            "verdict": "Insufficient evidence",
            "explanation": "No relevant evidence found. Cannot verify this claim.",
            "evidence_count": 0,
            "search_query": search_query,
            "evidence_breakdown": {"support": 0, "refute": 0, "irrelevant": 0}
        }

    # 分析每個證據的立場
    print(f"  → Analyzing stance of {len(valid_results)} evidence sources...")
    
    # 先預過濾明顯不相關的結果
    filtered_results = []
    filtered_out = 0
    for r in valid_results:
        if is_evidence_potentially_relevant(claim, r.get('title', ''), r.get('body', '')):
            filtered_results.append(r)
        else:
            filtered_out += 1
    
    if filtered_out > 0:
        print(f"     Pre-filtered {filtered_out} obviously irrelevant sources")
    
    # 如果過濾後沒有結果，返回證據不足
    if len(filtered_results) == 0:
        return {
            "verdict": "Insufficient evidence",
            "explanation": f"All {len(valid_results)} search results were irrelevant to the claim (wrong location/topic).",
            "evidence_count": len(valid_results),
            "search_query": search_query,
            "evidence_breakdown": {"support": 0, "refute": 0, "irrelevant": len(valid_results)}
        }
    
    categorized_evidence = {
        "support": [],
        "refute": [],
        "irrelevant": []
    }
    
    for r in filtered_results:
        title = r.get('title', '')
        body = r.get('body', '')
        stance = analyze_evidence_stance(claim, title, body)
        
        categorized_evidence[stance].append({
            "title": title,
            "snippet": body[:200] + "..." if len(body) > 200 else body,
            "href": r.get('href', '')
        })
    
    support_count = len(categorized_evidence["support"])
    refute_count = len(categorized_evidence["refute"])
    irrelevant_count = len(categorized_evidence["irrelevant"])
    
    # 加上被預過濾掉的數量
    total_irrelevant = irrelevant_count + filtered_out
    
    print(f"     Support: {support_count}, Refute: {refute_count}, Irrelevant: {total_irrelevant} (pre-filtered: {filtered_out})")
    
    # 建立分類後的證據摘要給LLM
    context = ""
    
    if categorized_evidence["support"]:
        context += "=== Supporting Evidence ===\n"
        for i, ev in enumerate(categorized_evidence["support"], 1):
            context += f"{i}. [{ev['title']}]\n   {ev['snippet']}\n\n"
    
    if categorized_evidence["refute"]:
        context += "=== Refuting Evidence ===\n"
        for i, ev in enumerate(categorized_evidence["refute"], 1):
            context += f"{i}. [{ev['title']}]\n   {ev['snippet']}\n\n"
    
    if categorized_evidence["irrelevant"]:
        context += f"=== Irrelevant Evidence ({total_irrelevant} sources total, {filtered_out} pre-filtered) ===\n(Not shown for brevity)\n\n"

    # 根據語言設定回應語言
    language_instruction = ""
    if language == "zh-TW":
        language_instruction = "CRITICAL: You MUST respond in Traditional Chinese (繁體中文). All explanations must be in Traditional Chinese."
    elif language == "en":
        language_instruction = "CRITICAL: You MUST respond in English. All explanations must be in English."
    else:
        language_instruction = "CRITICAL: You MUST respond in Traditional Chinese (繁體中文). All explanations must be in Traditional Chinese."

    system = (
        f"{language_instruction}\n\n"
        "You are verifying a factual claim using categorized evidence.\n"
        f"Evidence summary:\n"
        f"- Supporting evidence: {support_count}\n"
        f"- Refuting evidence: {refute_count}\n"
        f"- Irrelevant evidence: {total_irrelevant} (filtered out)\n\n"
        "Based on the categorized evidence, classify the claim as:\n"
        "- Supported: If supporting evidence is strong and refuting evidence is weak/absent\n"
        "- Contradicted: If refuting evidence is strong and supporting evidence is weak/absent\n"
        "- Insufficient evidence: If evidence is too weak, contradictory, or mostly irrelevant\n\n"
        "In your explanation, mention:\n"
        "1. Key supporting/refuting evidence\n"
        "2. Why you reached this conclusion\n"
        "3. Any uncertainty or conflicting information\n\n"
        f"{evidence_warning}\n"
        f"IMPORTANT: Your entire response (verdict + explanation) must be in the language specified above.\n"
        "Return JSON with fields: verdict, explanation."
    )

    user = f"Claim:\n{claim}\n\n{context}"

    out = call_llm(system, user)

    try:
        result = parse_json_response(out)
        result['evidence_count'] = len(valid_results)
        result['search_query'] = search_query
        result['evidence_breakdown'] = {
            "support": support_count,
            "refute": refute_count,
            "irrelevant": total_irrelevant
        }
        if evidence_warning:
            result['explanation'] = evidence_warning + "\n\n" + result['explanation']
        return result
    except Exception as e:
        return {
            "verdict": "Insufficient evidence",
            "explanation": f"Unable to parse verification result. {evidence_warning}",
            "evidence_count": len(valid_results),
            "search_query": search_query,
            "evidence_breakdown": {
                "support": support_count,
                "refute": refute_count,
                "irrelevant": total_irrelevant
            }
        }
