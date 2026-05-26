from flask import Flask, jsonify, request, render_template_string
import random
import os
import requests
import re
from collections import Counter, defaultdict
from bs4 import BeautifulSoup

app = Flask(__name__)

# =====================================================
# 建立歷史資料（模擬2000期）
# =====================================================

history_cache = []


def build_history(n=2000):

    global history_cache

    if history_cache:
        return history_cache

    data = []

    for _ in range(n):
        draw = sorted(random.sample(range(1, 81), 20))
        data.append(draw)

    history_cache = data

    return data


# =====================================================
# 熱號模型
# =====================================================

def hot_scores(history):

    c = Counter()

    for d in history:
        c.update(d)

    return c


# =====================================================
# 最近20期動量
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

def co_occurrence(history):

    matrix = defaultdict(Counter)

    for draw in history:

        for a in draw:
            for b in draw:

                if a != b:
                    matrix[a][b] += 1

    return matrix


# =====================================================
# 馬可夫轉移
# =====================================================

def markov_transition(history):

    trans = defaultdict(Counter)

    for i in range(len(history) - 1):

        current = history[i]
        nxt = history[i + 1]

        for a in current:
            for b in nxt:
                trans[a][b] += 1

    return trans


# =====================================================
# 貝葉斯更新
# =====================================================

def bayes_update(prior, evidence):

    result = {}

    for n in range(1, 81):

        p = prior.get(n, 1)
        e = evidence.get(n, 1)

        result[n] = (p * e) + 1

    return result


# =====================================================
# 多因子模型
# =====================================================

def ensemble_model(history, k):

    hot = hot_scores(history)

    momentum = momentum_scores(history)

    co = co_occurrence(history)

    markov = markov_transition(history)

    last_draw = history[-1]

    weights = {}

    for n in range(1, 81):

        score = 1

        # 熱號
        score += hot[n] * 0.4

        # 動量
        score += momentum[n] * 1.5

        # 冷號補償
        if hot[n] < 400:
            score *= 1.2

        # 共現
        co_score = 0

        for x in last_draw:
            co_score += co[x][n]

        score += co_score * 0.05

        # 馬可夫
        mk_score = 0

        for x in last_draw:
            mk_score += markov[x][n]

        score += mk_score * 0.03

        weights[n] = score

    # 貝葉斯更新
    weights = bayes_update(weights, momentum)

    nums = list(weights.keys())
    w = list(weights.values())

    result = set()

    while len(result) < k:

        pick = random.choices(nums, weights=w, k=1)[0]

        # 避免過度集中
        if all(abs(pick - x) > 2 for x in result):
            result.add(pick)

    return sorted(result)


# =====================================================
# 隨機模型
# =====================================================

def random_model(k):

    return sorted(random.sample(range(1, 81), k))


# =====================================================
# 熱號模型
# =====================================================

def hot_model(history, k):

    hot = hot_scores(history)

    top = [x[0] for x in hot.most_common(20)]

    return sorted(random.sample(top, k))


# =====================================================
# 動量模型
# =====================================================

def momentum_model(history, k):

    momentum = momentum_scores(history)

    top = [x[0] for x in momentum.most_common(20)]

    return sorted(random.sample(top, k))


# =====================================================
# 命中數
# =====================================================

def hit_count(pick, draw):

    return len(set(pick) & set(draw))


# =====================================================
# 回測
# =====================================================

def backtest(model_func, k):

    history = build_history()

    train = history[:1800]

    test = history[1800:]

    results = []

    for i in range(len(test) - 1):

        hist = train + test[:i]

        pred = model_func(hist, k)

        actual = test[i]

        h = hit_count(pred, actual)

        results.append(h)

    avg = sum(results) / len(results)

    return round(avg, 2)


# =====================================================
# 抓台彩LIVE
# =====================================================

def fetch_live():

    try:

        url = "https://www.taiwanlottery.com/lotto/result/bingo_bingo"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        nums = []

        balls = soup.select(".ball_tx")

        for b in balls[:20]:

            try:
                nums.append(int(b.text.strip()))
            except:
                pass

        nums = sorted(nums)

        issue = "LIVE"

        m = re.search(r"第(\d+)期", soup.text)

        if m:
            issue = m.group(1)

        return {
            "issue": issue,
            "numbers": nums
        }

    except Exception as e:

        return {
            "issue": "error",
            "numbers": [],
            "error": str(e)
        }


# =====================================================
# API：選號
# =====================================================

@app.route("/pick", methods=["POST"])
def pick():

    data = request.json

    k = int(data.get("count", 3))

    history = build_history()

    nums = ensemble_model(history, k)

    return jsonify({
        "numbers": nums
    })


# =====================================================
# API：LIVE
# =====================================================

@app.route("/live")
def live():

    return jsonify(fetch_live())


# =====================================================
# API：模型比較
# =====================================================

@app.route("/compare")
def compare():

    k = int(request.args.get("k", 3))

    random_avg = backtest(
        lambda h, kk: random_model(kk),
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
        "random": random_avg,
        "hot": hot_avg,
        "momentum": momentum_avg,
        "ensemble": ensemble_avg
    })


# =====================================================
# 首頁
# =====================================================

@app.route("/")
def home():

    return render_template_string("""

<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<title>Bingo穩定版</title>

<style>

body{
    background:#111;
    color:white;
    font-family:Arial;
    text-align:center;
}

h1{
    color:#00ff99;
}

button{
    padding:10px 20px;
    font-size:18px;
    margin:10px;
    border:none;
    border-radius:8px;
    cursor:pointer;
}

select{
    padding:8px;
    font-size:20px;
}

.ball{

    display:inline-block;

    width:44px;
    height:44px;

    line-height:44px;

    border-radius:50%;

    background:#ddd;

    color:black;

    margin:5px;

    font-weight:bold;
}

.hit{

    background:red;
    color:white;
}

.box{
    margin-top:20px;
}

</style>

</head>

<body>

<h1>🎯 Bingo穩定版</h1>

<select id="count">

<option value="1">1星</option>
<option value="2">2星</option>
<option value="3" selected>3星</option>
<option value="4">4星</option>
<option value="5">5星</option>
<option value="6">6星</option>
<option value="7">7星</option>
<option value="8">8星</option>
<option value="9">9星</option>
<option value="10">10星</option>

</select>

<br>

<button onclick="pick()">智慧選號</button>

<button onclick="startMonitor()">開始監控</button>

<div class="box">

<h2 id="my_numbers"></h2>

<h3 id="issue"></h3>

<h3 id="time"></h3>

<div id="live"></div>

<h2 id="hit"></h2>

</div>

<hr>

<button onclick="compare()">模型比較</button>

<pre id="compare_result"></pre>

<script>

let myNums=[];

function pick(){

    let count=parseInt(
        document.getElementById("count").value
    );

    fetch("/pick",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({
            count:count
        })

    })
    .then(r=>r.json())
    .then(data=>{

        myNums=data.numbers;

        document.getElementById("my_numbers").innerHTML=
            "你的號碼："+myNums.join(", ");

    });

}


function loadLive(){

    fetch("/live")
    .then(r=>r.json())
    .then(data=>{

        document.getElementById("issue").innerHTML=
            "期數："+data.issue+" (live)";

        let now=new Date();

        document.getElementById("time").innerHTML=
            "時間："+now.toLocaleTimeString();

        let html="";

        let hit=0;

        data.numbers.forEach(n=>{

            if(myNums.includes(n)){

                html+=
                `<div class="ball hit">${n}</div>`;

                hit++;

            }else{

                html+=
                `<div class="ball">${n}</div>`;
            }

        });

        document.getElementById("live").innerHTML=html;

        document.getElementById("hit").innerHTML=
            "命中："+hit+" 個";

    });

}


function startMonitor(){

    loadLive();

    setInterval(loadLive,30000);

}


function compare(){

    let count=parseInt(
        document.getElementById("count").value
    );

    fetch("/compare?k="+count)

    .then(r=>r.json())

    .then(data=>{

        document.getElementById("compare_result").innerHTML=

`
隨機模型平均命中：${data.random}

熱號模型平均命中：${data.hot}

動量模型平均命中：${data.momentum}

多因子模型平均命中：${data.ensemble}
`;

    });

}

</script>

</body>

</html>

""")


# =====================================================
# 啟動
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
