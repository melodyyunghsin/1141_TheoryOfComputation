"""
測試時間相關性檢查功能
"""
from fake_news_agent import FakeNewsAgent
import json


def test_case_1():
    """
    測試案例 1: 新聞說「今天」但找到的證據都是舊的
    預期：應該偵測到時間不符
    """
    print("=" * 80)
    print("測試案例 1: 新聞聲稱「今天發生」，但證據都是舊的")
    print("=" * 80)
    
    # 模擬一則假新聞：說今天發生，但實際是舊聞
    news = """
Title: 台北今天凌晨發生規模6.0地震
Content: 
根據報導，台北市今天凌晨3點發生規模6.0地震，震央位於信義區。
地震造成多棟建築物受損，目前已知有50人受傷。
中央氣象署表示這是近年來台北地區最大的地震。
消防局動員超過200名消防員進行救援工作。
"""
    
    agent = FakeNewsAgent()
    result = agent.run(news, language="zh-TW", temporal_check=True)
    
    print("\n=== 驗證結果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\n")


def test_case_2():
    """
    測試案例 2: 新聞說「去年」
    預期：只接受 2024 年的證據，2023 年的應該被過濾
    """
    print("=" * 80)
    print("測試案例 2: 新聞提到「去年」的事件")
    print("=" * 80)
    
    news = """
Title: 去年台灣GDP成長率創新高
Content:
根據統計，去年台灣GDP成長率達到5.8%，創下近年新高。
主計處表示，去年經濟表現優於預期，主要受惠於出口暢旺。
去年第四季成長率達到6.2%，帶動全年表現。
"""
    
    agent = FakeNewsAgent()
    result = agent.run(news, language="zh-TW", temporal_check=True)
    
    print("\n=== 驗證結果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\n")


def test_case_3():
    """
    測試案例 3: 無時間描述的新聞
    預期：不做時間限制
    """
    print("=" * 80)
    print("測試案例 3: 沒有特定時間描述的新聞")
    print("=" * 80)
    
    news = """
Title: 台北101是台灣最高的建築物
Content:
台北101大樓高度達到509公尺，是台灣最高的摩天大樓。
大樓共有101層，曾經是世界最高建築。
每年跨年煙火秀都在這裡舉行，吸引大量遊客。
"""
    
    agent = FakeNewsAgent()
    result = agent.run(news, language="zh-TW", temporal_check=True)
    
    print("\n=== 驗證結果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\n")


def test_case_4():
    """
    測試案例 4: 關閉時間檢查
    預期：即使有時間描述也不做限制
    """
    print("=" * 80)
    print("測試案例 4: 關閉時間檢查功能（temporal_check=False）")
    print("=" * 80)
    
    news = """
Title: 台北今天凌晨發生地震
Content:
根據報導，台北市今天凌晨發生地震。
"""
    
    agent = FakeNewsAgent()
    result = agent.run(news, language="zh-TW", temporal_check=False)
    
    print("\n=== 驗證結果 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("開始測試時間相關性檢查功能")
    print("當前日期: 2026-01-01")
    print("=" * 80 + "\n")
    
    # 選擇要執行的測試
    print("請選擇測試案例:")
    print("1. 測試「今天」的時間檢查（假新聞用舊聞）")
    print("2. 測試「去年」的時間範圍")
    print("3. 測試無時間限制的新聞")
    print("4. 測試關閉時間檢查")
    print("5. 執行所有測試（警告：會呼叫很多次 API）")
    
    choice = input("\n輸入選項 (1-5): ").strip()
    
    if choice == "1":
        test_case_1()
    elif choice == "2":
        test_case_2()
    elif choice == "3":
        test_case_3()
    elif choice == "4":
        test_case_4()
    elif choice == "5":
        print("\n執行所有測試...\n")
        test_case_1()
        input("按 Enter 繼續下一個測試...")
        test_case_2()
        input("按 Enter 繼續下一個測試...")
        test_case_3()
        input("按 Enter 繼續下一個測試...")
        test_case_4()
    else:
        print("無效的選項，執行測試案例 1")
        test_case_1()
    
    print("\n" + "=" * 80)
    print("測試完成")
    print("=" * 80)
