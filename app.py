def smart_pick(k):
    # 取得歷史資料（假設格式：[[1,2,3,4,5], [...], ...]）
    history = get_latest()

    # 若沒有資料 → fallback 隨機
    if not history:
        return sorted(random.sample(range(1, 40), k))  # 依你的彩種調整範圍

    from collections import Counter

    # 統計每個號碼出現次數
    counter = Counter()
    for draw in history:
        counter.update(draw)

    # 建立號碼池與權重
    numbers = list(range(1, 40))  # 依你的彩種調整
    weights = []

    for num in numbers:
        # 出現次數 + 1（避免 0 機率）
        weights.append(counter.get(num, 0) + 1)

    # 加權抽樣（不重複）
    picked = set()

    while len(picked) < k:
        choice = random.choices(numbers, weights=weights, k=1)[0]
        picked.add(choice)

        # 避免重複 → 將該號權重設為 0
        idx = numbers.index(choice)
        weights[idx] = 0

    return sorted(picked)
