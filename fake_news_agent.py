"""
Fake News Verification Agent (Refactored)
主流程和協調邏輯，委派具體任務給專門模組
"""
import json
from llm_helpers import call_llm, parse_json_response
from extractors import extract_title_and_details, extract_claims
from evidence_processor import verify_claim


class FakeNewsAgent:
    """
    假新聞驗證代理
    支援兩種模式：
    1. 新聞文章驗證（Title → Details → Evidence）
    2. 一般文字驗證（Claim-based）
    """
    
    def __init__(self):
        """初始化 Agent（驗證 API Key 在 llm_helpers 中處理）"""
        pass
    
    def judge_title_from_details(self, title, detail_results, language="zh-TW"):
        """
        基於細節驗證結果判斷標題的可信度
        
        Args:
            title: 新聞標題
            detail_results: 細節驗證結果列表
            language: 回應語言
        
        Returns:
            {
                "overall_credibility": "CREDIBLE" | "MISLEADING" | "UNCERTAIN",
                "explanation": str,
                "detail_summary": {"Supported": int, "Contradicted": int, "Insufficient evidence": int}
            }
        """
        # 統計細節驗證結果
        detail_counts = {"Supported": 0, "Contradicted": 0, "Insufficient evidence": 0}
        for detail in detail_results:
            detail_counts[detail["verdict"]] += 1
        
        # 根據語言設定回應語言
        language_instruction = ""
        if language == "zh-TW":
            language_instruction = "CRITICAL: You MUST respond in Traditional Chinese (繁體中文). All explanations must be in Traditional Chinese."
        elif language == "en":
            language_instruction = "CRITICAL: You MUST respond in English. All explanations must be in English."
        else:
            language_instruction = "CRITICAL: You MUST respond in Traditional Chinese (繁體中文). All explanations must be in Traditional Chinese."
        
        # 建立細節摘要給LLM
        details_summary = ""
        for i, detail in enumerate(detail_results, 1):
            details_summary += f"{i}. {detail['detail']}\n"
            details_summary += f"   Verdict: {detail['verdict']}\n"
            details_summary += f"   Brief: {detail['explanation'][:100]}...\n\n"
        
        system = (
            f"{language_instruction}\n\n"
            "You are judging whether a news article's TITLE is credible based on the verification of specific details from the content.\n\n"
            f"Title to judge: {title}\n\n"
            f"Details verification summary:\n"
            f"- Supported: {detail_counts['Supported']}\n"
            f"- Contradicted: {detail_counts['Contradicted']}\n"
            f"- Insufficient evidence: {detail_counts['Insufficient evidence']}\n\n"
            "Decision logic:\n"
            "- If most details are SUPPORTED → Title is likely TRUE\n"
            "- If key details are CONTRADICTED → Title is FALSE or MISLEADING\n"
            "- If most details lack evidence → Cannot determine title credibility\n\n"
            "Classify the title as:\n"
            "- CREDIBLE: Strong evidence supports the title\n"
            "- MISLEADING: Evidence contradicts or undermines the title\n"
            "- UNCERTAIN: Insufficient evidence to judge\n\n"
            "In your explanation:\n"
            "1. Which details support/contradict the title\n"
            "2. Overall assessment of title accuracy\n"
            "3. Any caveats or uncertainties\n\n"
            "Return JSON with fields: credibility (CREDIBLE/MISLEADING/UNCERTAIN), explanation.\n"
            "Your entire response must be in the language specified at the top."
        )
        
        user = f"Details verification:\n{details_summary}"
        
        try:
            out = call_llm(system, user)
            result = parse_json_response(out)
            
            # 標準化credibility值
            cred = result.get("credibility", "UNCERTAIN").upper()
            if "CREDIBLE" in cred and "MISLEADING" not in cred:
                overall_credibility = "CREDIBLE"
            elif "MISLEADING" in cred or "FALSE" in cred:
                overall_credibility = "MISLEADING"
            else:
                overall_credibility = "UNCERTAIN"
            
            return {
                "overall_credibility": overall_credibility,
                "explanation": result.get("explanation", ""),
                "detail_summary": detail_counts
            }
        except Exception as e:
            # 備用：簡單規則
            if detail_counts["Contradicted"] > 0:
                overall_credibility = "MISLEADING"
            elif detail_counts["Supported"] > detail_counts["Insufficient evidence"]:
                overall_credibility = "CREDIBLE"
            else:
                overall_credibility = "UNCERTAIN"
            
            return {
                "overall_credibility": overall_credibility,
                "explanation": f"Unable to generate detailed explanation. Based on {detail_counts['Supported']} supported, {detail_counts['Contradicted']} contradicted, {detail_counts['Insufficient evidence']} insufficient evidence.",
                "detail_summary": detail_counts
            }
    
    def aggregate_results(self, results):
        """
        統計並彙總多個 claim 的驗證結果
        
        Args:
            results: claim 驗證結果列表
        
        Returns:
            (credibility, counts) - 總體可信度和統計數據
        """
        counts = {"Supported": 0, "Contradicted": 0, "Insufficient evidence": 0}
        for r in results:
            counts[r["verdict"]] += 1

        if counts["Contradicted"] > 0:
            credibility = "LOW"
        elif counts["Supported"] > 0 and counts["Insufficient evidence"] == 0:
            credibility = "HIGH"
        else:
            credibility = "UNCERTAIN"

        return credibility, counts
    
    def run(self, text, language="zh-TW"):
        """
        主流程：自動偵測輸入類型並執行驗證
        
        Args:
            text: 輸入文本（新聞文章或一般陳述）
            language: 回應語言（zh-TW, en, auto）
        
        Returns:
            驗證結果字典（格式取決於模式）
        """
        # 偵測是否為新聞文章結構（包含 "Title:" 和 "Content:"）
        is_news_article = ("Title:" in text and "Content:" in text)
        
        if is_news_article:
            # === 模式 A: 新聞文章驗證（三層架構）===
            print("[MODE] News Article Verification (Title→Details→Evidence)\n")
            print("Step 1: Extract title and verifiable details...")
            extraction = extract_title_and_details(text, language=language)
            title = extraction["title"]
            details = extraction["details"]
            
            print(f"Title: {title}")
            print(f"Found {len(details)} verifiable details\n")

            # Step 2: Verify each detail
            detail_results = []
            for i, detail in enumerate(details, 1):
                print(f"Step 2.{i}: Verify detail {i}/{len(details)}")
                print(f"  Detail: {detail[:80]}...")
                verification = verify_claim(detail, language=language)
                detail_results.append({
                    "detail": detail,
                    "verdict": verification["verdict"],
                    "explanation": verification["explanation"],
                    "evidence_count": verification.get("evidence_count", 0),
                    "search_query": verification.get("search_query", ""),
                    "evidence_breakdown": verification.get("evidence_breakdown", {})
                })
                print(f"  Verdict: {verification['verdict']} ({verification.get('evidence_count', 0)} sources)\n")

            # Step 3: Aggregate to judge title
            print(f"Step 3: Judging title based on detail verification...")
            title_verdict = self.judge_title_from_details(title, detail_results, language)
            
            print(f"  Title credibility: {title_verdict['overall_credibility']}")
            print(f"  Detail statistics: {title_verdict['detail_summary']}\n")
            
            return {
                "mode": "news_article",
                "title": title,
                "title_verdict": title_verdict["overall_credibility"],
                "title_explanation": title_verdict["explanation"],
                "detail_summary": title_verdict["detail_summary"],
                "details": detail_results
            }
        
        else:
            # === 模式 B: 一般文字驗證（claim-based）===
            print("[MODE] Plain Text Verification (Claim-based)\n")
            print("Step 1: Extract verifiable claims...")
            claims = extract_claims(text, language=language)
            print(f"Found {len(claims)} claims\n")

            # Step 2: Verify each claim
            results = []
            for i, claim in enumerate(claims, 1):
                print(f"Step 2: Verify claim {i}/{len(claims)}")
                print(f"  Claim: {claim[:80]}...")
                verification = verify_claim(claim, language=language)
                results.append({
                    "claim": claim,
                    "verdict": verification["verdict"],
                    "explanation": verification["explanation"],
                    "evidence_count": verification.get("evidence_count", 0),
                    "search_query": verification.get("search_query", ""),
                    "evidence_breakdown": verification.get("evidence_breakdown", {})
                })
                print(f"  Verdict: {verification['verdict']} ({verification.get('evidence_count', 0)} sources)\n")

            # Step 3: Aggregate results
            print("Step 3: Aggregating results...")
            credibility, counts = self.aggregate_results(results)
            print(f"  Overall credibility: {credibility}")
            print(f"  Verdict statistics: {counts}\n")

            summary = (
                f"Supported: {counts['Supported']}, "
                f"Contradicted: {counts['Contradicted']}, "
                f"Insufficient evidence: {counts['Insufficient evidence']}"
            )

            return {
                "mode": "plain_text",
                "overall_credibility": credibility,
                "summary": summary,
                "claims": results
            }


# ---------- For testing in terminal ----------
def main():
    agent = FakeNewsAgent()
    print("Fake News Verification Agent (Terminal Mode)")
    print("Type 'quit' to exit.")
    print("-" * 50)

    while True:
        text = input("\nInput article or claim:\n> ")
        if text.lower() in {"quit", "exit"}:
            break

        result = agent.run(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
