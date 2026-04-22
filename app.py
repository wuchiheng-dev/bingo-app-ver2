from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
from collections import Counter
import random

app = Flask(__name__)

HEADERS = {"User-Agent": "Mozilla/5.0"}

# =========================
# 多來源抓資料
# =========================
def fetch_bingo_history(limit=200):
    urls = [
        "https://nx4.988cp.net/history?g=BingoBingo",
        "https://www.lotto-8.com/listltoBB.asp"
    ]

    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            draws = []

            for row in soup.select("div, tr"):
                nums = [int(x) for x in row.get_text().split() if x.isdigit()]
                if len(nums) == 20:
                    draws.append(nums)
                if len(draws) >= limit:
                    return draws[:limit]
        except:
            continue

    # fallback
    return [[i for i in range(1, 21)]] * limit

# =========================
# 統計權重模型（核心）
# =========================
def build_weights(draws):
    counter = Counter()

    # 時間加權（越新越重要）
    for idx, draw in enumerate(draws):
        weight = (idx + 1) / len(draws)
        for num in draw:
            counter[num] += weight

    # 拉普拉斯平滑
    return {i: counter[i] + 1 for i in range(1, 81)}

# =========================
# 篩選號碼（統計選號）
# =========================
def smart_pick(count, weights):
    numbers = list(weights.keys())
    weight_values = list(weights.values())

    result = set()
    while len(result) < count:
        pick = random.choices(numbers, weights=weight_values, k=1)[0]
        result.add(pick)

    return sorted(result)

# =========================
# API：選號
# =========================
@app.route("/pick", methods=["POST"])
def pick():
    count = int(request.json["count"])

    draws = fetch_bingo_history(200)
    weights = build_weights(draws)

    result = smart_pick(count, weights)

    return jsonify(result)

# =========================
# 主頁
# =========================
@app.route("/")
def index():
    return render_template("index.html")

# PWA
@app.route("/manifest.json")
def manifest():
    return app.send_static_file("manifest.json")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)