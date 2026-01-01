"""
時間相關性檢查模組
用於判斷證據的時間是否符合 claim 的時間描述
防止「舊聞充新聞」的假新聞手法
"""

from datetime import datetime, timedelta
import json
from llm_helpers import call_llm, parse_json_response


def normalize_time_expression(time_text, reference_date=None):
    """
    將任何語言的時間表達式標準化為具體日期
    
    Args:
        time_text: 時間表達式（中文/英文/任何語言）
        reference_date: 參考日期（預設為今天）
    
    Returns:
        {
            "parsed_date": "YYYY-MM-DD",
            "confidence": "high" / "medium" / "low",
            "time_type": "specific_recent" / "relative_recent" / "relative_past" / "no_time_reference",
            "original_expression": "去年"
        }
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    if isinstance(reference_date, str):
        reference_date = datetime.fromisoformat(reference_date)
    
    system_prompt = """You are a time expression parser. Parse ANY time expression in any language into a standard date.

Handle expressions like:
- Absolute: "2025-05-01", "May 2025"
- Relative recent: "today", "yesterday", "今天", "昨天", "this week"
- Relative past: "last year", "去年", "上個月", "last month"
- Day references with number: "昨(31日)", "31日", "yesterday (31st)" - interpret relative to reference date's month/year

CRITICAL for day number references:
- If reference date is 2026-01-01 and text says "昨(31日)" or "yesterday 31st", this means 2025-12-31 (previous month)
- If reference date is 2026-02-01 and text says "昨(31日)", this means 2026-01-31 (previous day)
- Always consider: is this day number BEFORE the reference date? Then use previous month/year if needed

Return JSON with this exact structure:
{
  "parsed_date": "YYYY-MM-DD",
  "confidence": "high" or "medium" or "low",
  "time_type": "specific_recent" or "relative_recent" or "relative_past" or "no_time_reference",
  "explanation": "brief explanation"
}

Time type definitions:
- specific_recent: today, yesterday, 今天, 昨天
- relative_recent: this week, last week, recently, 最近, 上週
- relative_past: last year, last month, 去年, 上個月
- no_time_reference: no time information found"""

    user_prompt = f"""Current reference date: {reference_date.strftime('%Y-%m-%d')}

Parse this time expression: "{time_text}"

IMPORTANT: If the text mentions a day number (like "31日" or "31st") with "yesterday/昨天", calculate which month it belongs to:
- Reference: 2026-01-01, Text: "昨(31日)" → Result: 2025-12-31 (previous month because Jan 1st - 1 day = Dec 31st)
- Reference: 2026-02-01, Text: "昨(31日)" → Result: 2026-01-31 (previous day in previous month)

Examples:
Input: "今天" → {{"parsed_date": "{reference_date.strftime('%Y-%m-%d')}", "confidence": "high", "time_type": "specific_recent", "explanation": "Today relative to reference date"}}
Input: "yesterday" → {{"parsed_date": "{(reference_date - timedelta(days=1)).strftime('%Y-%m-%d')}", "confidence": "high", "time_type": "specific_recent", "explanation": "One day before reference date"}}
Input: "去年" → {{"parsed_date": "{(reference_date.replace(year=reference_date.year-1, month=6, day=15)).strftime('%Y-%m-%d')}", "confidence": "medium", "time_type": "relative_past", "explanation": "Previous year relative to reference date"}}
Input: "2025-05-01" → {{"parsed_date": "2025-05-01", "confidence": "high", "time_type": "relative_past", "explanation": "Specific date provided"}}

Return ONLY the JSON, no other text."""

    try:
        response = call_llm(system_prompt, user_prompt)
        result = parse_json_response(response)
        result['original_expression'] = time_text
        return result
    except Exception as e:
        print(f"Error normalizing time expression: {e}")
        return {
            "parsed_date": None,
            "confidence": "low",
            "time_type": "no_time_reference",
            "original_expression": time_text,
            "explanation": "Failed to parse"
        }


def extract_time_from_claim(claim_text):
    """
    從 claim 中提取時間表達式
    
    Args:
        claim_text: claim 文本
    
    Returns:
        時間表達式字串，如果沒有則返回 None
    """
    system_prompt = """You are a time expression extractor. Extract ANY time-related words or phrases from the text.

Look for:
- Absolute dates: "2025-05-01", "May 2025"
- Relative time: "today", "yesterday", "recently", "last year"
- Chinese time: "今天", "昨天", "去年", "上個月", "最近", "日前"

Return JSON:
{
  "has_time_reference": true or false,
  "time_expression": "the extracted time expression" or null,
  "context": "surrounding context if helpful"
}"""

    user_prompt = f"""Extract time expression from this text:

"{claim_text}"

Examples:
Input: "台北今天發生地震" → {{"has_time_reference": true, "time_expression": "今天", "context": "台北今天發生地震"}}
Input: "去年GDP成長5%" → {{"has_time_reference": true, "time_expression": "去年", "context": "去年GDP成長"}}
Input: "Taiwan earthquake" → {{"has_time_reference": false, "time_expression": null, "context": ""}}

Return ONLY the JSON."""

    try:
        response = call_llm(system_prompt, user_prompt)
        result = parse_json_response(response)
        
        if result.get('has_time_reference') and result.get('time_expression'):
            return result['time_expression']
        return None
    except Exception as e:
        print(f"Error extracting time from claim: {e}")
        return None


def extract_time_from_evidence(evidence_text):
    """
    從證據文本中提取發布時間或事件時間
    
    Args:
        evidence_text: 證據文本
    
    Returns:
        {
            "time_expression": str or None - 提取的時間表達式
            "publish_date": str or None - 證據的發布日期（如果有）
        }
    """
    system_prompt = """You are a publication date and event time extractor. Extract BOTH from the text:
1. Publication/source date (when the article was published)
2. Event time expressions (relative time like "去年", "last year")

Look for:
- Explicit dates: "Published on 2025-05-01", "2025年5月發布"
- Metadata dates: dates near the beginning or end of text
- Event dates: "occurred on", "happened on", "took place on"
- Relative time: "去年", "last year", "上個月"

Return JSON:
{
  "publish_date": "YYYY-MM-DD or original date string" or null,
  "time_expression": "the time expression from content" or null
}"""

    user_prompt = f"""Extract publication date and time expression from this text:

"{evidence_text[:500]}..."

Examples:
Input: "Published on 2025-05-01. 去年台灣GDP..." → {{"publish_date": "2025-05-01", "time_expression": "去年"}}
Input: "2024年12月25日報導..." → {{"publish_date": "2024-12-25", "time_expression": null}}

Return ONLY the JSON."""

    try:
        response = call_llm(system_prompt, user_prompt)
        result = parse_json_response(response)
        
        return {
            "time_expression": result.get('time_expression'),
            "publish_date": result.get('publish_date')
        }
    except Exception as e:
        print(f"Error extracting time from evidence: {e}")
        return {
            "time_expression": None,
            "publish_date": None
        }


def calculate_time_range(time_type, parsed_date, original_expression):
    """
    根據時間類型計算允許的時間範圍
    
    Args:
        time_type: 時間類型
        parsed_date: 解析後的日期字串 "YYYY-MM-DD"
        original_expression: 原始時間表達式（用於特殊處理）
    
    Returns:
        (start_date, end_date) datetime objects
    """
    if parsed_date is None:
        return None, None
    
    reference = datetime.fromisoformat(parsed_date)
    
    if time_type == "specific_recent":
        # 今天、昨天：容忍 ±1 天（時區問題）
        return (
            reference - timedelta(days=1),
            reference + timedelta(days=1)
        )
    
    elif time_type == "relative_recent":
        # 上週、最近、日前：前 7-14 天
        if "week" in original_expression.lower() or "週" in original_expression:
            # 上週：前 7-14 天
            return (
                reference - timedelta(days=14),
                reference - timedelta(days=7)
            )
        else:
            # 最近、日前：前 7 天內
            return (
                reference - timedelta(days=7),
                reference
            )
    
    elif time_type == "relative_past":
        # 去年、上個月：必須落在那個時間段內
        if "year" in original_expression.lower() or "年" in original_expression:
            # 去年：前一年的整年
            year = reference.year - 1
            return (
                datetime(year, 1, 1),
                datetime(year, 12, 31)
            )
        elif "month" in original_expression.lower() or "月" in original_expression:
            # 上個月：前一個月
            if reference.month == 1:
                year, month = reference.year - 1, 12
            else:
                year, month = reference.year, reference.month - 1
            
            start = datetime(year, month, 1)
            if month == 12:
                end = datetime(year, 12, 31)
            else:
                end = datetime(year, month + 1, 1) - timedelta(days=1)
            
            return (start, end)
        else:
            # 其他相對過去時間：前 60 天
            return (
                reference - timedelta(days=60),
                reference
            )
    
    else:  # no_time_reference
        # 沒有時間限制，但太舊的會降權（2年）
        return (
            reference - timedelta(days=730),
            reference + timedelta(days=30)
        )


def is_temporally_relevant(claim_time_info, evidence_time_info):
    """
    檢查證據時間是否符合 claim 的時間描述
    
    Args:
        claim_time_info: normalize_time_expression() 的輸出
        evidence_time_info: normalize_time_expression() 的輸出
    
    Returns:
        {
            "is_relevant": True/False,
            "status": "relevant" / "too_old" / "too_recent" / "unknown",
            "expected_range": "YYYY-MM-DD ~ YYYY-MM-DD",
            "evidence_date": "YYYY-MM-DD",
            "deviation_days": int,
            "explanation": str
        }
    """
    # 如果沒有時間資訊或日期為空，不做限制
    evidence_date_str = evidence_time_info.get('parsed_date')
    
    if (claim_time_info.get('time_type') == 'no_time_reference' or 
        not evidence_date_str or 
        evidence_date_str is None or 
        evidence_date_str == ''):
        return {
            "is_relevant": True,
            "status": "no_constraint",
            "expected_range": "N/A",
            "evidence_date": evidence_date_str if evidence_date_str else 'unknown',
            "deviation_days": 0,
            "explanation": "No time constraint on claim or evidence"
        }
    
    # 計算 claim 的時間範圍
    time_range = calculate_time_range(
        claim_time_info['time_type'],
        claim_time_info['parsed_date'],
        claim_time_info.get('original_expression', '')
    )
    
    if time_range[0] is None:
        return {
            "is_relevant": True,
            "status": "unknown",
            "expected_range": "unknown",
            "evidence_date": evidence_time_info['parsed_date'],
            "deviation_days": 0,
            "explanation": "Cannot determine time range"
        }
    
    start_date, end_date = time_range
    evidence_date = datetime.fromisoformat(evidence_time_info['parsed_date'])
    
    # 檢查是否落在範圍內
    is_in_range = start_date <= evidence_date <= end_date
    
    # 計算偏差
    if evidence_date < start_date:
        deviation = (start_date - evidence_date).days
        status = "too_old"
        explanation = f"Evidence is {deviation} days older than expected range"
    elif evidence_date > end_date:
        deviation = (evidence_date - end_date).days
        status = "too_recent"
        explanation = f"Evidence is {deviation} days newer than expected range"
    else:
        deviation = 0
        status = "relevant"
        explanation = "Evidence date falls within expected range"
    
    return {
        "is_relevant": is_in_range,
        "status": status,
        "expected_range": f"{start_date.date()} ~ {end_date.date()}",
        "evidence_date": evidence_date.date().isoformat(),
        "deviation_days": deviation,
        "explanation": explanation
    }


if __name__ == "__main__":
    # 測試
    print("=== 測試時間標準化 ===")
    
    test_cases = [
        ("今天", "2026-01-01"),
        ("yesterday", "2026-01-01"),
        ("去年", "2025-06-01"),
        ("last month", "2026-01-01"),
        ("2025-05-01", "2026-01-01")
    ]
    
    for time_text, ref_date in test_cases:
        print(f"\n輸入: '{time_text}' (參考日期: {ref_date})")
        result = normalize_time_expression(time_text, ref_date)
        print(f"結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    print("\n=== 測試時間相關性判斷 ===")
    
    # 測試案例：新聞說「去年」，證據是 2024 年
    claim_info = {
        "parsed_date": "2025-06-15",  # claim 發布於 2025-06-15
        "time_type": "relative_past",
        "original_expression": "去年"
    }
    
    evidence_info_valid = {
        "parsed_date": "2024-05-01"  # 2024 年的證據
    }
    
    evidence_info_invalid = {
        "parsed_date": "2023-05-01"  # 2023 年的證據（前年）
    }
    
    print("\n案例 1: 新聞說「去年」，證據是 2024-05-01")
    result = is_temporally_relevant(claim_info, evidence_info_valid)
    print(f"結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    print("\n案例 2: 新聞說「去年」，證據是 2023-05-01（前年）")
    result = is_temporally_relevant(claim_info, evidence_info_invalid)
    print(f"結果: {json.dumps(result, ensure_ascii=False, indent=2)}")
