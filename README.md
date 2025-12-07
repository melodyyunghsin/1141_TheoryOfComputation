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

---

## 💻 使用方式

### 方法 A：Open WebUI 整合（推薦）

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
├── qa_tool.py            # QA 工具（網路搜尋功能）
├── start_openwebui.py    # Open WebUI 啟動腳本
├── requirements.txt      # Python 依賴套件
└── README.md             # 本說明文件
```

### 檔案說明

- **`qa_tool.py`** - 核心 QA 工具
  - `web_search_qa()` - 一般網路搜尋
  - `wikipedia_search()` - 維基百科搜尋
  - `get_current_info()` - 最新資訊查詢

- **`start_openwebui.py`** - Open WebUI 配置啟動腳本
  - 自動設置環境變數
  - 簡化啟動流程

- **`.env.example`** - 環境變數範本
  - 包含 API 配置格式
  - 不含真實 API Key（安全）

---

## 🛠️ 可用的工具函數

### 1. web_search_qa(query, max_results=5)
一般網路搜尋，回傳格式化的搜尋結果。

**範例**：
```python
from qa_tool import Tools

tools = Tools()
result = tools.web_search_qa("台灣的首都")
print(result)
```

### 2. wikipedia_search(query, max_results=3)
專門搜尋維基百科內容。

**範例**：
```python
result = tools.wikipedia_search("Machine Learning")
print(result)
```

### 3. get_current_info(query)
查詢最新資訊（2025 年新聞）。

**範例**：
```python
result = tools.get_current_info("Taiwan president")
print(result)
```

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

可以輕鬆添加更多工具：

- 📊 **數據視覺化** - 生成圖表
- 🧮 **計算器** - 數學運算
- 📄 **文件處理** - RAG 系統
- 💾 **記憶系統** - 儲存對話歷史

只需要創建新的工具模組，並在 Open WebUI 中啟用即可！

---

## 📞 支援

如有問題，請查看：
- [Open WebUI 文檔](https://docs.openwebui.com/)
- [Ollama API 文檔](https://docs.ollama.com/api/)

---

## 📄 授權

本專案為 NCKU 計算理論課程期末專案。
