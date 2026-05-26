from flask import Flask, jsonify, request, render_template_string
import requests
import random
import os
from bs4 import BeautifulSoup
from collections import Counter, defaultdict

app = Flask(**name**)

HEADERS = {"User-Agent":"Mozilla/5.0"}

# =====================================================

# LIVE 即時抓號

# =====================================================

def fetch_live():

```
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
```

# =====================================================

# API 備援

# =====================================================

def fetch_api():

```
try:

    url = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult"

    r = requests.get(
        url,
        headers=HEADERS,
        timeout=5
    ).json()

    d = r["content"]["lotteryBingoLatestPost"]

    return {

        "numbers":[int(x) for x in d["bigShowOrder"]],

        "term":int(d["drawTerm"]),

        "time":d["dDate"].replace("T"," "),

        "source":"api"
    }

except:

    return None
```

# =====================================================

# 最新資料

# =====================================================

def get_latest():

```
live = fetch_live()

api = fetch_api()

sources = [s for s in [live, api] if s]

if not sources:

    return {

        "term":0,

        "numbers":[],

        "time":"error",

        "source":"none"
    }

return max(
    sources,
    key=lambda x:x["term"]
)
```

# =====================================================

# 建立歷史資料（模擬）

# =====================================================

history_cache = []

def build_history(n=2000):

```
global history_cache

if history_cache:
    return history_cache

data = []

for _ in range(n):

    draw = sorted(
        random.sample(range(1,81),20)
    )

    data.append(draw)

history_cache = data

return data
```

# =====================================================

# 熱號

# =====================================================

def hot_scores(history):

```
c = Counter()

for d in history:
    c.update(d)

return c
```

# =====================================================

# 動量

# =====================================================

def momentum_scores(history):

```
recent = history[-20:]

c = Counter()

for d in recent:
    c.update(d)

return c
```

# =====================================================

# 共現矩陣

# =====================================================

def co_matrix(history):

```
matrix = defaultdict(Counter)

for draw in history:

    for a in draw:
        for b in draw:

            if a != b:
                matrix[a][b] += 1

return matrix
```

# =====================================================

# 馬可夫

# =====================================================

def markov(history):

```
trans = defaultdict(Counter)

for i in range(len(history)-1):

    current = history[i]

    nxt = history[i+1]

    for a in current:
        for b in nxt:

            trans[a][b] += 1

return trans
```

# =====================================================

# 智慧選號

# =====================================================

def smart_pick(k):

```
history = build_history()

hot = hot_scores(history)

momentum = momentum_scores(history)

co = co_matrix(history)

mk = markov(history)

last_draw = history[-1]

weights = {}

for n in range(1,81):

    score = 1

    score += hot[n] * 0.45

    score += momentum[n] * 1.8

    if hot[n] < 400:
        score *= 1.15

    co_score = 0

    for x in last_draw:
        co_score += co[x][n]

    score += co_score * 0.04

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

    if all(abs(pick-x)>2 for x in result):
        result.add(pick)

return sorted(result)
```

# =====================================================

# 命中

# =====================================================

def check_hit(pick, draw):

```
return list(set(pick)&set(draw))
```

# =====================================================

# 首頁

# =====================================================

@app.route("/")
def home():

```
return render_template_string("""
```

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

<button onclick="pick()">
智慧選號
</button>

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


// =====================================
// 選號
// =====================================

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


// =====================================
// 監控
// =====================================

function loadMonitor(){

    fetch("/monitor?nums="+myNums.join(","))

    .then(r=>r.json())

    .then(data=>{

        document.getElementById("issue").innerHTML=
            "期數："+data.term;

        document.getElementById("time").innerHTML=
            "開獎時間："+data.time;

        let html="";

        data.draw.forEach(n=>{

            if(data.hit.includes(n)){

                html +=
                `<div class="ball hit">${n}</div>`;

            }else{

                html +=
                `<div class="ball">${n}</div>`;
            }

        });

        document.getElementById("live").innerHTML=
            html;

        document.getElementById("hit").innerHTML=
            "命中："+data.hit.length+" 個 → "+data.hit.join(", ");

    });

}


// =====================================
// 開始監控
// =====================================

function startMonitor(){

    loadMonitor();

    if(!started){

        setInterval(loadMonitor,30000);

        started=true;
    }

}

</script>

</body>

</html>

""")

# =====================================================

# 選號 API

# =====================================================

@app.route("/pick", methods=["POST"])
def pick():

```
data = request.json

k = int(data.get("count",3))

return jsonify({
    "numbers": smart_pick(k)
})
```

# =====================================================

# 監控 API

# =====================================================

@app.route("/monitor")
def monitor():

```
nums = request.args.get("nums","")

my = [int(x) for x in nums.split(",") if x]

latest = get_latest()

hit = check_hit(my, latest["numbers"])

return jsonify({

    "term": latest["term"],

    "time": latest["time"],

    "draw": latest["numbers"],

    "hit": hit,

    "source": latest["source"]
})
```

# =====================================================

# 啟動

# =====================================================

if **name** == "**main**":

```
port = int(os.environ.get("PORT",10000))

app.run(
    host="0.0.0.0",
    port=port
)
