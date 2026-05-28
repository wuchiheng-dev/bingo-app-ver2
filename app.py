from flask import Flask, jsonify, request, render_template
import random
import os
from collections import Counter, defaultdict

app = Flask(__name__)

# =====================================================
# 歷史資料（模擬2000期）
# =====================================================

history_cache = []


def build_history(n=2000):

    global history_cache

    if history_cache:
        return history_cache

    data = []

    for _ in range(n):

        draw = sorted(
            random.sample(range(1, 81), 20)
        )

        data.append(draw)

    history_cache = data

    return data


# =====================================================
# 熱號
# =====================================================

def hot_scores(history):

    c = Counter()

    for d in history:
        c.update(d)

    return c


# =====================================================
# 動量
# =====================================================

def momentum_scores(history):

    recent = history[-20:]

    c = Counter()

    for d in recent:
        c.update(d)

    return c


# =====================================================
# 共現矩陣
# =====================================================

def co_matrix(history):

    matrix = defaultdict(Counter)

    for draw in history:

        for a in draw:
            for b in draw:

                if a != b:
                    matrix[a][b] += 1

    return matrix


# =====================================================
# 馬可夫
# =====================================================

def markov(history):

    trans = defaultdict(Counter)

    for i in range(len(history) - 1):

        current = history[i]
        nxt = history[i + 1]

        for a in current:
            for b in nxt:

                trans[a][b] += 1

    return trans


# =====================================================
# 智慧選號
# =====================================================

def smart_pick(k):

    history = build_history()

    hot = hot_scores(history)

    momentum = momentum_scores(history)

    co = co_matrix(history)

    mk = markov(history)

    last_draw = history[-1]

    weights = {}

    for n in range(1, 81):

        score = 1

        # 熱號
        score += hot[n] * 0.45

        # 動量
        score += momentum[n] * 1.8

        # 冷號補償
        if hot[n] < 400:
            score *= 1.15

        # 共現
        co_score = 0

        for x in last_draw:
            co_score += co[x][n]

        score += co_score * 0.04

        # 馬可夫
        mk_score = 0

        for x in last_draw:
            mk_score += mk[x][n]

        score += mk_score * 0.03

        weights[n] = score

    nums = list(weights.keys())
    w = list(weights.values())

    result = set()

    while len(result) < k:

        pick = random.choices(
            nums,
            weights=w,
            k=1
        )[0]

        # 避免太集中
        if all(abs(pick - x) > 2 for x in result):
            result.add(pick)

    return sorted(result)


# =====================================================
# API: 智慧選號
# =====================================================

@app.route("/pick", methods=["POST"])
def pick():

    data = request.json

    k = int(data.get("count", 3))

    nums = smart_pick(k)

    return jsonify({
        "numbers": nums
    })


# =====================================================
# 首頁
# =====================================================

@app.route("/")
def home():

    return render_template("index.html")


# =====================================================
# 啟動
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
