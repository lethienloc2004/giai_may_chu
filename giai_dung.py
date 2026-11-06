# -*- coding: utf-8 -*-
"""Giải ĐÚNG trò rót nước có ô ẩn: dựng toàn bộ đồ thị trạng thái (cấu hình nhìn thấy + tập màu ẩn còn lại),
rồi tính điểm cố định (không bị lỗi vòng lặp như chienluoc.py).
  python giai_dung.py STATE [gioi_han_trang_thai=3000000]
In: (1) có chiến lược THẮNG CHẮC không; (2) xác suất thắng tối đa khi chơi tối ưu (màu ẩn lộ ra ngẫu nhiên đều theo
tập màu còn lại); (3) chuỗi nước tới lần mở ô kế tiếp.
Mô hình: ô ẩn lộ ra là một màu bất kỳ trong tập còn lại, xác suất tỉ lệ số ô còn lại của màu đó (hoán đổi được)."""
import sys, os, json, time
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rotnuoc_mc import moves_v, pour_v, kv, CAP
from rotnuoc import UNK, hidden_pool

S = json.load(open(sys.argv[1], encoding='utf-8'))
LIM = int(sys.argv[2]) if len(sys.argv) > 2 else 3000000
tubes = [list(reversed(t)) for t in S['tubes']]
pool0 = Counter(hidden_pool(tubes, CAP))
pk = lambda p: tuple(sorted((c, n) for c, n in p.items() if n > 0))


def done(v):
    return all(not t or (len(t) == CAP and UNK not in t and len(set(t)) == 1) for t in v)


ids = {}; states = []; succ = []   # succ[i] = list of ('o', j) hoặc ('r', [(prob, j), ...])
t0 = time.time()


def get(v, pool):
    k = (kv(v), pk(pool))
    i = ids.get(k)
    if i is None:
        i = len(states); ids[k] = i; states.append((v, pool)); succ.append(None)
    return i


root = get(tubes, pool0)
stack = [root]
while stack:
    i = stack.pop()
    if succ[i] is not None:
        continue
    v, pool = states[i]
    moves = []
    if not done(v):
        for a, b in moves_v(v):
            nv = pour_v(v, a, b)
            if nv[a] and nv[a][-1] == UNK:
                tot = sum(pool.values()); outs = []
                for c, n in pool.items():
                    if n <= 0: continue
                    v2 = [list(t) for t in nv]; v2[a][-1] = c
                    p2 = pool.copy(); p2[c] -= 1
                    outs.append((n / tot, get(v2, p2)))
                moves.append(((a, b), 'r', outs))
            else:
                moves.append(((a, b), 'o', get(nv, pool)))
    succ[i] = moves
    for _, kind, x in moves:
        if kind == 'o':
            if succ[x] is None: stack.append(x)
        else:
            for _, j in x:
                if succ[j] is None: stack.append(j)
    if len(states) > LIM:
        print('QUÁ NHIỀU TRẠNG THÁI (>%d) — thu hẹp bài toán' % LIM); sys.exit()
print('số trạng thái: %d (%.0fs)' % (len(states), time.time() - t0), flush=True)
N = len(states)
isdone = [done(states[i][0]) for i in range(N)]

# (1) thắng chắc: điểm cố định nhỏ nhất
win = [isdone[i] for i in range(N)]
ch = True
while ch:
    ch = False
    for i in range(N):
        if win[i]: continue
        for _, kind, x in succ[i]:
            if kind == 'o':
                if win[x]: win[i] = True; break
            elif all(win[j] for _, j in x):
                win[i] = True; break
        if win[i]: ch = True
print('THẮNG CHẮC từ đầu ván:', win[root])

# (2) xác suất thắng tối đa (lặp giá trị tăng dần)
P = [1.0 if isdone[i] else 0.0 for i in range(N)]
for it in range(2000):
    d = 0.0
    for i in range(N):
        if isdone[i]: continue
        b = P[i]
        for _, kind, x in succ[i]:
            val = P[x] if kind == 'o' else sum(p * P[j] for p, j in x)
            if val > b: b = val
        if b > P[i] + 1e-12: d = max(d, b - P[i]); P[i] = b
    if d < 1e-9: break
print('XÁC SUẤT THẮNG TỐI ĐA từ đầu ván: %.2f%% (lặp %d)' % (100 * P[root], it))

# đường NGẮN NHẤT (BFS trên các nước tối ưu) tới lần mở ô kế tiếp, đi theo trạng thái THẬT
from collections import deque


def evalmoves(v, pool):
    out = []
    for a, b in moves_v(v):
        nv = pour_v(v, a, b)
        if nv[a] and nv[a][-1] == UNK:
            tot = sum(pool.values()); val = 0.0
            for c, n in pool.items():
                if n <= 0: continue
                v2 = [list(t) for t in nv]; v2[a][-1] = c
                p2 = pool.copy(); p2[c] -= 1
                val += n / tot * P[ids[(kv(v2), pk(p2))]]
            out.append((val, (a, b), nv, 'r'))
        else:
            out.append((P[ids[(kv(nv), pk(pool))]], (a, b), nv, 'o'))
    return out


pool = pool0
q = deque([(tubes, [])]); vis = {kv(tubes)}; found = None
while q and found is None:
    v, path = q.popleft()
    if done(v): continue
    em = evalmoves(v, pool)
    if not em: continue
    top = max(e[0] for e in em)
    for val, mv, nv, kind in em:
        if val < top - 1e-9: continue
        if kind == 'r':
            found = path + [mv]; break
        if kv(nv) not in vis:
            vis.add(kv(nv)); q.append((nv, path + [mv]))
print('Chuỗi nước tới lần mở ô kế tiếp:', ' '.join('%d %d' % (a + 1, b + 1) for a, b in found) if found else '(không có)')
