from flask import Flask, jsonify, request, render_template
import random
import os
from collections import Counter, defaultdict

app = Flask(__name__)

# =====================================
# 建立2000期歷史資料（模擬）
# =====================================

history_data = []

def build_history(n=2000):

    global history_data

    if history_data:
        return history_data

    data = []

    for _ in range(n):
        data.append(sorted(random.sample(range(1,81),20)))

    history_data = data

    return data


# =====================================
# 熱號模型
# =====================================

def hot_scores(history):

    c = Counter()

    for d in history:
        c.update(d)

    return c


# =====================================
# 動量模型（最近20期）
# =====================================

def momentum_scores(history):

    recent = history[-20:]

    c = Counter()

    for d in recent:
        c.update(d)

    return c


# =====================================
# 共現矩陣
# =====================================

def co_matrix(history):

    matrix = defaultdict(Counter)

    for draw in history:

        for n1 in draw:
            for n2 in draw:

                if n1 != n2:
                    matrix[n1][n2] += 1

    return matrix


# =====================================
# 馬可夫轉移
# =====================================

def markov_scores(history):

    trans = defaultdict(Counter)

    for i in range(len(history)-1):

        current = history[i]
        nxt = history[i+1]

        for c in current:
            for n in nxt:
                trans[c][n] += 1

    return trans


# =====================================
# 貝葉斯更新
# =====================================

def bayes_update(prior, evidence):

    result = {}

    for n in range(1,81):

        p = prior.get(n,1)
        e = evidence.get(n,1)

        result[n] = (p * e) + 1

    return result


# =====================================
# 多因子融合
# =====================================

def ensemble_model(history,k):

    hot = hot_scores(history)
    momentum = momentum_scores(history)

    co = co_matrix(history)

    markov = markov_scores(history)

    weights = {}

    last_draw = history[-1]

    for n in range(1,81):

        score = 1

        # 熱號
        score += hot[n] * 0.4

        # 動量
        score += momentum[n] * 1.5

        # 冷號補償
        if hot[n] < 400:
            score *= 1.2

        # 共現矩陣
        co_score = 0

        for x in last_draw:
            co_score += co[x][n]

        score += co_score * 0.05

        # 馬可夫
        mk = 0

        for x in last_draw:
            mk += markov[x][n]

        score += mk * 0.03

        weights[n] = score

    # 貝葉斯修正
    weights = bayes_update(weights,momentum)

    nums = list(weights.keys())
    w = list(weights.values())

    result = set()

    while len(result) < k:

        pick = random.choices(nums,weights=w,k=1)[0]

        # 分散化
        if all(abs(pick-x) > 2 for x in result):
            result.add(pick)

    return sorted(result)


# =====================================
# 隨機模型
# =====================================

def random_model(k):
    return sorted(random.sample(range(1,81),k))


# =====================================
# 熱號模型
# =====================================

def hot_model(history,k):

    hot = hot_scores(history)

    top = [x[0] for x in hot.most_common(20)]

    return sorted(random.sample(top,k))


# =====================================
# 動量模型
# =====================================

def momentum_model(history,k):

    m = momentum_scores(history)

    top = [x[0] for x in m.most_common(20)]

    return sorted(random.sample(top,k))


# =====================================
# 命中
# =====================================

def hit(pick,draw):

    return len(set(pick)&set(draw))


# =====================================
# 回測
# =====================================

def backtest(model_func,k):

    history = build_history()

    train = history[:1800]
    test = history[1800:]

    results = []

    for i in range(len(test)-1):

        hist = train + test[:i]

        pred = model_func(hist,k)

        actual = test[i]

        results.append(hit(pred,actual))

    return round(sum(results)/len(results),2)


# =====================================
# API 選號
# =====================================

@app.route("/pick",methods=["POST"])
def pick():

    data = request.json

    k = int(data.get("count",3))

    history = build_history()

    nums = ensemble_model(history,k)

    return jsonify({
        "numbers":nums
    })


# =====================================
# 模型比較
# =====================================

@app.route("/compare")
def compare():

    k = int(request.args.get("k",3))

    history = build_history()

    random_avg = backtest(
        lambda h,k: random_model(k),
        k
    )

    hot_avg = backtest(
        hot_model,
        k
    )

    momentum_avg = backtest(
        momentum_model,
        k
    )

    ensemble_avg = backtest(
        ensemble_model,
        k
    )

    return jsonify({
        "random":random_avg,
        "hot":hot_avg,
        "momentum":momentum_avg,
        "ensemble":ensemble_avg
    })


# =====================================
# UI
# =====================================

@app.route("/")
def index():
    return render_template("index.html")


# =====================================
# 啟動
# =====================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT",10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
