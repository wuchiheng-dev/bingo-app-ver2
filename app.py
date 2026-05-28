from flask import Flask, jsonify, request, render_template
import random
from collections import Counter

app = Flask(__name__)

# =====================================================
# 模擬歷史資料（你之後可以換成真實 API）
# 每期 20 個號碼（1~80）
# =====================================================
def get_latest():
    history = []
    for _ in range(100):  # 模擬最近 100 期
        draw = random.sample(range(1, 81), 20)
        history.append(draw)
    return history


# =====================================================
# ✅ 智慧選號（熱門號 + 加權機率）
# =====================================================
def smart_pick(k):
    history = get_latest()

    if not history:
        return sorted(random.sample(range(1, 81), k))

    counter = Counter()

    # 統計熱門號
    for draw in history:
        counter.update(draw)

    numbers = list(range(1, 81))
    
    # 權重（熱門越高 → 機率越高）
    weights = [counter.get(n, 0) + 1 for n in numbers]

    picked = set()

    while len(picked) < k:
        choice = random.choices(numbers, weights=weights, k=1)[0]
        picked.add(choice)

        # 避免重複
        idx = numbers.index(choice)
        weights[idx] = 0

    return sorted(picked)


# =====================================================
# 命中計算
# =====================================================
def check_hit(pick, draw):
    return list(set(pick) & set(draw))


# =====================================================
# 首頁
# =====================================================
@app.route("/")
def index():
    return render_template("index.html")


# =====================================================
# 選號 API
# =====================================================
@app.route("/pick", methods=["POST"])
def pick():
    data = request.get_json()
    count = int(data.get("count", 5))

    numbers = smart_pick(count)

    return jsonify({
        "numbers": numbers
    })


# =====================================================
