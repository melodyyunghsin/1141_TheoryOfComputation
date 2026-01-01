from flask import Flask, request, jsonify
from flask_cors import CORS
from fake_news_agent import FakeNewsAgent
from qa_agent import QAAgent

app = Flask(__name__)

CORS(
    app,
    resources={r"/verify": {"origins": "*"}},
    methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"]
)

agent = FakeNewsAgent()
qa_agent = QAAgent()

@app.route("/verify", methods=["POST", "OPTIONS"])
def verify():

    if request.method == "OPTIONS":
        return "", 200

    data = request.get_json(force=True, silent=True) or {}
    mode = data.get("mode", "news")  # "news" | "qa"
    text = data.get("text", "")
    language = data.get("language", "zh-TW")  # 預設繁體中文
    publish_date = data.get("publishDate")  # 新聞發布日期（可選）

    print(
        f"[POST /verify] mode={mode}, language={language}, "
        f"text_length={len(text)}, publishDate={publish_date}"
    )

    if not text:
        return jsonify({"error": "No text provided"}), 400

    if mode == "qa":
        # ---- QA MODE ----
        qa_result = qa_agent.search_and_answer(
            question=text,
            use_search=None
        )

        return jsonify({
            "mode": "qa",
            "question": text,
            "answer": qa_result.get("answer", ""),
            "success": qa_result.get("success", False)
        })

    else:
        # ---- NEWS VERIFICATION MODE (default) ----
        result = agent.run(
            text,
            language=language,
            publish_date=publish_date
        )
        return jsonify(result)


@app.route("/")
def health():
    return "Fake News Agent Server Running"


if __name__ == "__main__":
    print("🚀 Starting Fake News Agent Server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
