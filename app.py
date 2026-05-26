from flask import Flask, jsonify, request, render_template_string
import random
import os
import requests
import re
from collections import Counter, defaultdict
from bs4 import BeautifulSoup

app = Flask(__name__)

# ======================================================
# 建立歷史資料（模擬）
# ======================================================

history_cache = []

def build_history(n=2000):

    global history_cache

    if history_cache:
        return history_cache

    data = []

    for _ in range(n):

        draw = sorted(random.sample(range(1,81),20))

        data.append(draw)

    history_cache = data

    return data


# ======================================================
# 熱號
# ======================================================

def hot_scores(history):

    c = Counter()

    for d in history:
        c.update(d)

    return c


# ======================================================
# 動量
# ======================================================

def momentum_scores(history):

    recent = history[-20:]

    c = Counter()

    for d in recent:
        c.update(d)

    return c


# ======================================================
# 共現矩陣
# ======================================================

def co_matrix(history):

    matrix = defaultdict(Counter)

    for draw in history:

        for a in draw:
            for b in draw:

                if a != b:
                    matrix[a][b] += 1

    return matrix


# ======================================================
# 馬可夫
# ======================================================

def markov(history):

    trans = defaultdict(Counter)

    for i in range(len(history)-1):

        current = history[i]
        nxt = history[i+1]

        for a in current:
            for b in nxt:

                trans[a][b] += 1

    return trans


# ======================================================
# 多因子模型
# ======================================================

def ensemble_model(history,k):

    hot = hot_scores(history)

    momentum = momentum_scores(history)

    co = co_matrix(history)

    mk = markov(history)

    last_draw = history[-1]

    weights = {}

    for n in range(1,81):

        score = 1

        # 熱號
        score += hot[n] * 0.5

        # 動量
        score += momentum[n] * 1.8

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
            mk_score += mk[x][n]

        score += mk_score * 0.03

        weights[n] = score

    nums = list(weights.keys())
    w = list(weights.values())

    result = set()

    while len(result) < k:

        pick = random.choices(nums,weights=w,k=1)[0]

        # 避免過度集中
        if all(abs(pick-x) > 2 for x in result):
            result.add(pick)

    return sorted(result)


# ======================================================
# 回測
# ======================================================

def hit(pred,actual):

    return len(set(pred)&set(actual))


def random_model(history,k):

    return sorted(random.sample(range(1,81),k))


def hot_model(history,k):

    hot = hot_scores(history)

    top = [x[0] for x in hot.most_common(20)]

    return sorted(random.sample(top,k))


def momentum_model(history,k):

    m = momentum_scores(history)

    top = [x[0] for x in m.most_common(20)]

    return sorted(random.sample(top,k))


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


# ======================================================
# LIVE 抓台彩
# ======================================================

def fetch_live():

    try:

        url = "https://www.taiwanlottery.com.tw/lotto/BingoBingo/drawing.aspx"

        headers = {
            "User-Agent":"Mozilla/5.0"
        }

        r = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        soup = BeautifulSoup(r.text,"html.parser")

        nums = []

        # 真正Bingo球號
        balls = soup.select(".contents_box02 .ball_green")

        for b in balls[:20]:

            txt = b.text.strip()

            if txt.isdigit():
                nums.append(int(txt))

        nums = sorted(nums)

        # 期數
        issue = "unknown"

        txt = soup.text

        m = re.search(r"第\s*(\d+)\s*期",txt)

        if m:
            issue = m.group(1)

        return {
            "issue":issue,
            "numbers":nums
        }

    except Exception as e:

        return {
            "issue":"error",
            "numbers":[],
            "error":str(e)
        }


# ======================================================
# API：選號
# ======================================================

@app.route("/pick",methods=["POST"])
def pick():

    data = request.json

    k = int(data.get("count",3))

    history = build_history()

    nums = ensemble_model(history,k)

    return jsonify({
        "numbers":nums
    })


# ======================================================
# API：LIVE
# ======================================================

@app.route("/live")
def live():

    return jsonify(fetch_live())


# ======================================================
# API：模型比較
# ======================================================

@app.route("/compare")
def compare():

    k = int(request.args.get("k",3))

    return jsonify({

        "random":backtest(random_model,k),

        "hot":backtest(hot_model,k),

        "momentum":backtest(momentum_model,k),

        "ensemble":backtest(ensemble_model,k)
    })


# ======================================================
# UI
# ======================================================

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

button{
    padding:10px 20px;
    font-size:18px;
    margin:10px;
}

select{
    padding:8px;
    font-size:18px;
}

.ball{

    width:42px;
    height:42px;

    line-height:42px;

    border-radius:50%;

    display:inline-block;

    background:#ddd;

    color:black;

    margin:4px;

    font-weight:bold;
}

.hit{
    background:red;
    color:white;
}

</style>

</head>

<body>

<h1>🎯 Bingo穩定版</h1>

<select id="count">

<option value="1">1星</option>
<option value="2">2星</option>
<option value="3">3星</option>
<option value="4">4星</option>
<option value="5" selected>5星</option>
<option value="6">6星</option>
<option value="7">7星</option>
<option value="8">8星</option>
<option value="9">9星</option>
<option value="10">10星</option>

</select>

<br>

<button onclick="pick()">智慧選號</button>

<button onclick="startMonitor()">開始監控</button>

<h2 id="my_numbers"></h2>

<h3 id="issue"></h3>

<h3 id="time"></h3>

<div id="live"></div>

<h2 id="hit"></h2>

<hr>

<button onclick="compare()">模型比較</button>

<pre id="compare_result"></pre>

<script>

let myNums=[];

let monitorStarted=false;


// ====================================
// 選號
// ====================================

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


// ====================================
// LIVE
// ====================================

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

                html +=
                `<div class="ball hit">${n}</div>`;

                hit++;

            }else{

                html +=
                `<div class="ball">${n}</div>`;
            }

        });

        document.getElementById("live").innerHTML=html;

        document.getElementById("hit").innerHTML=
            "命中："+hit+" 個";

    });

}


// ====================================
// 開始監控
// ====================================

function startMonitor(){

    loadLive();

    if(!monitorStarted){

        setInterval(loadLive,30000);

        monitorStarted=true;
    }

}


// ====================================
// 模型比較
// ====================================

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


# ======================================================
# 啟動
# ======================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT",10000))

    app.run(
        host="0.0.0.0",
        port=port
    )

