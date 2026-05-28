from flask import Flask, jsonify, request, render_template
import requests
import random
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# =====================================================
# LIVE網站
# =====================================================

def fetch_live():

    try:

        url = "https://lotto.auzonet.com/bingobingoV1.php"

        html = requests.get(
            url,
            headers=HEADERS,
            timeout=5
        ).text

        soup = BeautifulSoup(html, "lxml")

        rows = soup.find_all("tr")

        for r in rows:

            t = r.get_text(" ", strip=True)

            parts = t.split()

            if len(parts) >= 22 and parts[0].isdigit():

                return {
                    "term": int(parts[0]),
                    "time": parts[1],
                    "numbers": list(map(int, parts[2:22])),
                    "source": "live"
                }

    except Exception as e:

        print("LIVE解析錯:", e)

    return None


# =====================================================
# 官方API備援
# =====================================================

def fetch_api():

    try:

        url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult"

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=5
        ).json()

        d = r["content"]["lotteryBingoLatestPost"]

        return {
            "numbers": [int(x) for x in d["bigShowOrder"]],
            "term": int(d["drawTerm"]),
            "time": d["dDate"].replace("T", " "),
            "source": "api"
        }

    except Exception as e:

        print("API錯:", e)

        return None


# =====================================================
# 最新資料
# =====================================================

def get_latest():

    live = fetch_live()

    api = fetch_api()

    sources = [s for s in [live, api] if s]

    if not sources:

        return {
            "term": 0,
            "numbers": [],
            "time": "error",
            "source": "none"
        }

    return max(
        sources,
        key=lambda x: x["term"]
    )


# =====================================================
# 智慧選號
# =====================================================

def smart_pick(k):

    step = 80 // k

    nums = []

    for i in range(k):

        low = i * step + 1

        high = (i + 1) * step

        nums.append(
            random.randint(low, high)
        )

    return sorted(nums)


# =====================================================
# 命中
# =====================================================

def check_hit(pick, draw):

    return list(
        set(pick) & set(draw)
    )


# =====================================================
# 首頁
# =====================================================

@app.route("/")
def index():

    return render_template("index.html")


# =====================================================
# 選號
# =====================================================

@app.route("/pick", methods=["POST"])
def pick():

    data = request.json

    k = int(data.get("count", 3))

    return jsonify({
        "numbers": smart_pick(k)
    })


# =====================================================
# 監控
# =====================================================

@app.route("/monitor")
def monitor():

    nums = request.args.get("nums", "")

    my = [
        int(x)
        for x in nums.split(",")
        if x
    ]

    latest = get_latest()

    hit = check_hit(
        my,
        latest["numbers"]
    )

    return jsonify({
        "term": latest["term"],
        "time": latest["time"],
        "draw": latest["numbers"],
        "hit": hit,
        "source": latest["source"]
    })


# =====================================================
# 啟動
# =====================================================

if __name__ == "__main__":

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
