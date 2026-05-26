from flask import Flask, jsonify, request, render_template_string
import random
import os
import requests
import re
from collections import Counter, defaultdict

app = Flask(__name__)

# =====================================================
# 歷史資料
# =====================================================

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

    for i in range(len(history)-1):

        current = history[i]
        nxt = history[i+1]

        for a in current:
            for b in nxt:

                trans[a][b] += 1

    return trans


# =====================================================
# 智慧選號（主模型）
# =====================================================

def smart_pick(k):

    history = build_history()

    hot = hot_scores(history)

    momentum = momentum_scores(history)

    co = co_matrix(history)

    mk = markov(history)

    last_draw = history[-1]

    weights = {}

    for n in range(1,81):

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

        # 分散化
        if all(abs(pick-x)>2 for x in result):
            result.add(pick)

    return sorted(result)


# =====================================================
# 抓台彩LIVE
# =====================================================

def fetch_live():

    try:

        url = "https://www.taiwanlottery.com/lotto/result/bingo_bingo"

        headers = {
            "User-Agent":"Mozilla/5.0"
        }

        r = requests.get(
            url,
            headers=headers,
            timeout=8
        )

        html = r.text

        # 抓20個號碼
        nums = re.findall(
            r'ball_tx ball_yellow">(\d+)',
            html
        )

        if len(nums) < 20:

            nums = re.findall(
                r'>(\d{2})<',
                html
            )[:20]

        nums = [int(x) for x in nums[:20]]

        nums = sorted(nums)

        # 抓期數
        issue = "unknown"

        m = re.search(
            r'第(\d+)期',
            html
        )

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


# =====================================================
# API：選號
# =====================================================

@app.route("/pick",methods=["POST"])
def pick():

    data = request.json

    k = int(data.get("count",3))

    nums = smart_pick(k)

    return jsonify({
        "numbers":nums
    })


# =====================================================
# API：LIVE
# =====================================================

@app.route("/live")
def live():

    return jsonify(fetch_live())


# =====================================================
# UI
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

button{

    padding:10px 20px;

    font-size:18px;

    margin:10px;

    border:none;

    border-radius:10px;

    cursor:pointer;
}

select{

    font-size:20px;

    padding:5px;
}

.ball{

    display:inline-block;

    width:42px;
    height:42px;

    line-height:42px;

    border-radius:50%;

    margin:4px;

    background:#ddd;

    color:black;

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
<option value="5">5星</option>
<option value="6" selected>6星</option>
<option value="7">7星</option>
<option value="8">8星</option>
<option value="9">9星</option>
<option value="10">10星</option>

</select>

<br>

<button onclick="pick()">智慧選號</button>

<button onclick="startMonitor()">
開始監控
</button>

<h2 id="my_numbers"></h2>

<h3 id="issue"></h3>

<h3 id="time"></h3>

<div id="live"></div>

<h2 id="hit"></h2>

<script>

let myNums=[];

let started=false;


// ====================================
// 智慧選號
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
// LIVE監控
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

        document.getElementById("live").innerHTML=
            html;

        document.getElementById("hit").innerHTML=
            "命中："+hit+" 個";

    });

}


// ====================================
// 開始監控
// ====================================

function startMonitor(){

    loadLive();

    if(!started){

        setInterval(loadLive,30000);

        started=true;
    }

}

</script>

</body>

</html>

""")


# =====================================================
# 啟動
# =====================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT",10000))

    app.run(
        host="0.0.0.0",
        port=port
    )

