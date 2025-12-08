# QA Agent with Web Search - TOC Final Project

智能問答 Agent，結合網路搜尋與 LLM API，能夠自動搜尋資訊並生成答案。

## 📋 專案功能

- ✅ 網路搜尋（使用 DuckDuckGo）
- ✅ 維基百科專門搜尋
- ✅ 最新資訊查詢
- ✅ 整合 LLM API 生成答案
- ✅ 支援 Open WebUI 整合

---

## 🚀 快速開始

### 1. Clone 專案
```bash
git clone https://github.com/Lienlientina/1132_TheoryOfComputation.git
cd 1132_TheoryOfComputation
```

### 2. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 3. 設置 API Key

複製 `.env.example` 為 `.env`：
```bash
copy .env.example .env
```

編輯 `.env` 檔案，將 `your-api-key-here` 替換為你的實際 API key：
```env
API_BASE_URL=https://api-gateway.netdb.csie.ncku.edu.tw
API_KEY=你的實際API金鑰

OPENAI_API_BASE_URL=https://api-gateway.netdb.csie.ncku.edu.tw
OPENAI_API_KEY=你的實際API金鑰
```

### 4. 測試 QA Tool
```bash
python qa_tool.py
```

### 5. 運行 QA Agent（推薦）
```bash
python qa_agent.py
```

這會啟動互動式 QA Agent，自動整合網路搜尋和 LLM 回答！

---

## 💻 使用方式

### 方法 A：命令列 QA Agent（主要 Demo 方式）⭐

#### 直接運行 Agent
```bash
python qa_agent.py
```

#### 使用方式
- **預設行為**：輸入問題 → 自動搜尋網路 → LLM 分析回答
- **直接對話**：輸入 `chat: 你的訊息` → 不搜尋，直接問 LLM
- **離開**：輸入 `quit` 或 `exit`

#### 範例對話
```
You: 台灣的首都是哪裡
🔍 Searching web...
✅ Found 3 results
🤖 Querying LLM...
Agent: 台灣的首都是台北市...

You: chat: 你好
Agent: 你好！有什麼我可以幫助你的嗎？

You: quit
👋 Goodbye!
```

---

### 方法 B：Open WebUI 整合（額外展示）

#### 1. 安裝 Open WebUI
```bash
pip install open-webui
```

#### 2. 啟動 Open WebUI
```bash
python start_openwebui.py
```

#### 3. 在瀏覽器開啟
```
http://localhost:8080
```

#### 4. 添加 QA Tool
1. 進入 **Workspace** > **Tools**（或 Settings > Tools）
2. 點擊 **+** 創建新工具
3. 複製貼上 `qa_tool.py` 的全部內容
4. 儲存並啟用工具

#### 5. 開始使用
在聊天中詢問問題，例如：
- "搜尋台灣的首都是哪裡"
- "查詢 2025 年台灣總統"
- "Machine Learning 是什麼"

LLM 會自動呼叫 QA Tool 搜尋網路並回答！

---

## 📁 專案結構

```
.
├── .env.example          # API 配置範本
├── .gitignore            # Git 忽略規則
├── qa_tool.py            # 搜尋工具模組（純函數）
├── qa_agent.py           # 主 Agent（整合 Tool + LLM）⭐
├── start_openwebui.py    # Open WebUI 啟動腳本
├── requirements.txt      # Python 依賴套件
└── README.md             # 本說明文件
```

### 檔案說明

- **`qa_tool.py`** - 搜尋工具模組（可重用）
  - `web_search()` - 純搜尋函數
  - `format_search_results()` - 格式化結果
  - `Tools` class - Open WebUI 兼容包裝

- **`qa_agent.py`** - 主 QA Agent ⭐
  - 整合搜尋工具 + LLM API
  - 完整的問答流程
  - 互動式命令列介面
  - **這是主要的 Demo 程式**

- **`start_openwebui.py`** - Open WebUI 配置啟動腳本
  - 自動設置環境變數
  - 簡化啟動流程

- **`.env.example`** - 環境變數範本
  - 包含 API 配置格式
  - 不含真實 API Key（安全）

---

## 🛠️ API 使用範例

### 使用純工具函數
```python
from qa_tool import web_search, format_search_results

# 搜尋網路
results = web_search("台灣的首都", max_results=3)

# 格式化結果
formatted = format_search_results(results)
print(formatted)
```

### 使用 QA Agent
```python
from qa_agent import QAAgent

# 初始化 Agent
agent = QAAgent()

# 搜尋並回答
result = agent.search_and_answer("台灣的首都是哪裡？")
print(result['answer'])

# 直接對話（不搜尋）
answer = agent.chat("你好", use_search=False)
print(answer)
```

### 在其他專案中重用
```python
# 其他專案可以 import 這些工具
from qa_tool import web_search

# 只使用搜尋功能
results = web_search("Python tutorial")
```

---

## 🏗️ 架構設計

### 模組化架構
```
用戶輸入
   ↓
qa_agent.py (主控 Agent)
   ↓
   ├─→ qa_tool.py (搜尋工具)
   │      └─→ DuckDuckGo API
   ↓
   └─→ LLM API (gpt-oss:20b)
   ↓
返回答案
```

### 設計優點
1. **模組分離**：工具和 Agent 分開，易於測試和擴展
2. **可重用性**：`qa_tool.py` 可以被其他專案 import
3. **易於擴展**：未來可以輕鬆添加新工具

---

## 🔧 系統需求

- Python 3.8+
- 網路連接
- LLM API Key（由課程提供）

---

## 📚 技術棧

- **DuckDuckGo Search** - 網路搜尋（無需 API Key）
- **Open WebUI** - 圖形化對話介面
- **LLM API** - Ollama 兼容的 API 端點
- **Python** - 主要開發語言

---

## ⚠️ 注意事項

1. **API Key 安全**
   - ❌ 不要將 `.env` 上傳到 GitHub
   - ✅ 使用 `.env.example` 作為範本

2. **網路搜尋限制**
   - DuckDuckGo 可能有速率限制
   - 建議適度使用

3. **Open WebUI Tool 設置**
   - 需要手動將 `qa_tool.py` 內容貼到 Open WebUI
   - 這是 Open WebUI 的設計限制

---

## 🎯 未來擴展

模組化設計讓擴展變得簡單：

### 添加新工具範例
```python
# calculator_tool.py
def calculate(expression: str) -> float:
    """計算數學表達式"""
    return eval(expression)

# 在 qa_agent.py 中整合
from qa_tool import web_search
from calculator_tool import calculate

class QAAgent:
    def process(self, query):
        if "計算" in query:
            return calculate(query)
        elif "搜尋" in query:
            return web_search(query)
```

### 可以添加的工具
- 📊 **數據視覺化** - matplotlib 繪圖
- 🧮 **計算器** - 數學運算
- 📄 **文件讀取** - RAG 系統
- 💾 **記憶系統** - 對話歷史儲存
- 🌐 **API 整合** - 天氣、股票等

只需要創建新的工具模組，然後在 `qa_agent.py` 中 import 即可！

---

## 📞 支援

如有問題，請查看：
- [Open WebUI 文檔](https://docs.openwebui.com/)
- [Ollama API 文檔](https://docs.ollama.com/api/)

---

## 📄 授權

本專案為 NCKU 計算理論課程期末專案。
