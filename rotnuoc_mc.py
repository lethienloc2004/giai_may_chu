# -*- coding: utf-8 -*-
"""Đánh giá nước đi KHÔNG NHÌN TRỘM cho trò rót nước.

Với mỗi nước ứng viên: lấy N cách sắp ô ẩn ngẫu nhiên (khớp số màu), áp nước đó, rồi cho
một chiến thuật heuristic chơi tiếp mà CHỈ thấy ô đã lộ (như người chơi thật). Đo:
  - tỉ lệ thắng,
  - số ô ẩn trung bình mở được trước khi kẹt (dùng cho ván "dò đường").
python rotnuoc_mc.py STATE [thang|do] [so_the_gioi=120] [giay=60]
"""
import sys, json, random, time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rotnuoc import hidden_pool, UNK

CAP = 4
W_CHON = 2.0


# ---- thế giới: mỗi lọ là list (màu, đã_biết) từ dưới lên ----
def make_world(tubes, pool, rng):
    p = pool[:]
    rng.shuffle(p)
    it = iter(p)
    return [[(next(it), False) if c == UNK else (c, True) for c in t] for t in tubes]


def view(w):
    return [[c if k else UNK for c, k in t] for t in w]


def top_block_v(t):
    if not t or t[-1] == UNK:
        return None, 0
    c = t[-1]; n = 1
    while n < len(t) and t[-1 - n] == c:
        n += 1
    return c, n


def moves_v(v):
    res = []
    for a, ta in enumerate(v):
        c, n = top_block_v(ta)
        if not c:
            continue
        if n == len(ta) and n == CAP and UNK not in ta:
            continue
        empty_done = False
        for b, tb in enumerate(v):
            if a == b or len(tb) >= CAP:
                continue
            if tb:
                if tb[-1] != c:
                    continue
            else:
                if n == len(ta) or empty_done:
                    continue
                empty_done = True
            res.append((a, b))
    return res


def pour(w, a, b):
    """áp nước trên thế giới thật; trả số ô ẩn vừa lộ."""
    ta, tb = w[a], w[b]
    c = ta[-1][0]
    n = 1
    while n < len(ta) and ta[-1 - n][0] == c and ta[-1 - n][1]:
        n += 1
    m = min(n, CAP - len(tb))
    for _ in range(m):
        tb.append((ta.pop()[0], True))
    if ta and not ta[-1][1]:
        ta[-1] = (ta[-1][0], True)
        return 1
    return 0


def won_w(w):
    return all(not t or (len(t) == CAP and len({c for c, _ in t}) == 1) for t in w)


def score_move(v, a, b):
    """heuristic không nhìn trộm (điểm càng cao càng tốt)."""
    ta, tb = v[a], v[b]
    c, n = top_block_v(ta)
    room = CAP - len(tb)
    m = min(n, room)
    empties = sum(1 for t in v if not t)
    s = 0.0
    after_a = ta[:-m]
    if tb:
        s += 3
        if len(tb) + m == CAP and all(x == c for x in tb):
            s += 6                                   # hoàn thành lọ
    else:
        # dùng lọ rỗng: càng ít lọ rỗng càng phạt nặng
        s -= 2 if empties >= 2 else 6
        if len(after_a) <= 1:
            s += 3                                   # sắp làm rỗng lọ nguồn
    if m < n:
        s -= 3                                       # tách khối
    if not after_a:
        s += 5                                       # tạo lọ rỗng
    elif after_a[-1] == UNK:
        s += 2.5                                     # mở ô ẩn
        s += 0.5 * (CAP - len(after_a))              # lọ nguồn còn ít ô -> gần rỗng
    # gom vào lọ đích mà bên dưới còn màu khác = chôn thêm
    if tb and any(x != c for x in tb):
        s -= 1.5
    return s


def eval_v(v):
    """chấm điểm bàn chơi chỉ dựa trên phần nhìn thấy."""
    s = 0.0
    tops = {}
    for t in v:
        if not t:
            s += W_RONG
            continue
        if len(t) == CAP and UNK not in t and len(set(t)) == 1:
            s += 14
            continue
        c, n = top_block_v(t)
        s += 1.2 * n
        for i in range(len(t) - 1):
            if t[i] != UNK and t[i + 1] != UNK and t[i] != t[i + 1]:
                s -= 2.0
        s -= 0.7 * t.count(UNK)
        if UNK in t:
            hi = max(i for i, x in enumerate(t) if x == UNK)
            s -= W_CHON * (len(t) - 1 - hi)          # số ô đã biết đè lên ô ẩn
        if c:
            tops.setdefault(c, []).append(CAP - len(t))
    for c, rooms in tops.items():
        if len(rooms) >= 2 and max(rooms) > 0:
            s += 1.0                                 # có thể gom
    return s


def pour_v(v, a, b):
    v = [list(t) for t in v]
    c, n = top_block_v(v[a])
    m = min(n, CAP - len(v[b]))
    for _ in range(m):
        v[b].append(v[a].pop())
    return v


def kv(v):
    return tuple(sorted(tuple(t) for t in v))


def choose(v, rng, seen, depth=2):
    best = None
    for a, b in moves_v(v):
        v1 = pour_v(v, a, b)
        k1 = kv(v1)
        if k1 in seen:
            continue
        sc = eval_v(v1)
        if depth > 1:
            nxt = [eval_v(pour_v(v1, x, y)) for x, y in moves_v(v1) if (x, y) != (b, a)]
            if nxt:
                sc = max(sc, max(nxt) - 0.3)
        sc += rng.random() * 0.6
        if best is None or sc > best[0]:
            best = (sc, a, b)
    return best


def plan_to_reveal(v, rng, seen, node_cap=4000):
    """BFS trên phần đã thấy. Lá = trạng thái vừa mở ô ẩn hoặc thắng.
    Chọn lá điểm cao nhất (ưu tiên đường ngắn); nếu không mở được gì thì chọn trạng thái
    chưa từng gặp có điểm cao nhất. Trả nước đầu tiên hoặc None."""
    if UNK not in [c for t in v for c in t]:
        from rotnuoc import solve_full
        try:
            sol = solve_full(v, CAP, time.time() + 3)
        except TimeoutError:
            sol = None
        if sol:
            return sol[0]
    from collections import deque
    q = deque([(v, None, 0)])
    visited = {kv(v)}
    best_leaf = None
    best_any = None
    n = 0
    while q and n < node_cap:
        cur, first, d = q.popleft()
        for a, b in moves_v(cur):
            nv = pour_v(cur, a, b)
            k = kv(nv)
            if k in visited:
                continue
            visited.add(k)
            n += 1
            f = first or (a, b)
            win = all(not t or (len(t) == CAP and UNK not in t and len(set(t)) == 1) for t in nv)
            if win:
                return f
            sc = eval_v(nv) - 0.3 * d + rng.random() * 0.4
            if nv[a] and nv[a][-1] == UNK:
                if best_leaf is None or sc > best_leaf[0]:
                    best_leaf = (sc, f)
                continue
            if k not in seen and (best_any is None or sc > best_any[0]):
                best_any = (sc, f)
            q.append((nv, f, d + 1))
    if best_leaf:
        return best_leaf[1]
    return best_any[1] if best_any else None


def rollout(w, rng, max_steps=250):
    seen = set()
    revealed = 0
    for _ in range(max_steps):
        if won_w(w):
            return True, revealed
        v = view(w)
        seen.add(kv(v))
        mv = plan_to_reveal(v, rng, seen)
        if mv is None:
            return False, revealed
        revealed += pour(w, mv[0], mv[1])
    return False, revealed


def evaluate(tubes, nworld, limit, mode):
    pool = hidden_pool(tubes, CAP)
    rng = random.Random(7)
    base = [make_world(tubes, pool, rng) for _ in range(nworld)]
    v0 = [list(t) for t in tubes]
    mv = moves_v(v0)
    if not mv:
        print('KHÔNG còn nước hợp lệ.'); return
    res = []
    t0 = time.time()
    per = limit / len(mv)
    for a, b in mv:
        wins = rev = tot = 0
        dl = time.time() + per
        for w0 in base:
            if time.time() > dl and tot >= 10:
                break
            w = [list(t) for t in w0]
            r0 = pour(w, a, b)
            ok, r = rollout(w, rng)
            wins += ok; rev += r0 + r; tot += 1
        res.append((wins / tot, rev / tot, a, b, tot, score_move(v0, a, b)))
    key = (lambda r: (-r[0], -r[1])) if mode == 'thang' else (lambda r: (-r[1], -r[0]))
    res.sort(key=key)
    nunk = sum(t.count(UNK) for t in tubes)
    print('Ô ẩn: %d | chế độ: %s' % (nunk, 'thắng' if mode == 'thang' else 'dò đường (mở nhiều ô nhất)'))
    print('Nước    thắng   ô mở TB  (số lần thử) điểm heuristic')
    for wr, rv, a, b, tot, h in res[:12]:
        print('%2d -> %-2d %5.1f%%  %5.1f   (%d)  %.1f' % (a + 1, b + 1, 100 * wr, rv, tot, h))
    print('(%.0fs)' % (time.time() - t0))


def duong(tubes, node_cap=30000, top=15):
    """Liệt kê các chuỗi nước (chỉ dùng phần đã thấy) dẫn tới MỞ một ô ẩn, kèm chi phí."""
    from collections import deque
    v = [list(t) for t in tubes]
    q = deque([(v, [])])
    visited = {kv(v)}
    leaves = {}
    n = 0
    while q and n < node_cap:
        cur, path = q.popleft()
        for a, b in moves_v(cur):
            nv = pour_v(cur, a, b)
            k = kv(nv)
            if k in visited:
                continue
            visited.add(k); n += 1
            p2 = path + [(a, b)]
            if nv[a] and nv[a][-1] == UNK:
                empties = sum(1 for t in nv if not t)
                room = sum(CAP - len(t) for t in nv if t)
                done = sum(1 for t in nv if len(t) == CAP and UNK not in t and len(set(t)) == 1)
                chon = 0
                for t in nv:
                    if UNK in t:
                        hi = max(i for i, x in enumerate(t) if x == UNK)
                        chon += len(t) - 1 - hi
                key = (a, empties, room, done, chon)
                if key not in leaves or len(leaves[key]) > len(p2):
                    leaves[key] = p2
                continue
            q.append((nv, p2))
    rows = sorted(leaves.items(), key=lambda kv_: (-kv_[0][1], -kv_[0][3], kv_[0][4], -kv_[0][2], len(kv_[1])))
    print('Mở ô ở lọ | lọ rỗng còn | chỗ trống | lọ xong | ô bị đè | chuỗi nước')
    for (a, e, r, d, c), p2 in rows[:top]:
        print('   %2d     |     %d       |    %2d     |   %d     |   %2d    | %s' % (
            a + 1, e, r, d, c, ' '.join('%d>%d' % (x + 1, y + 1) for x, y in p2)))
    if not rows:
        print('Không còn đường nào mở được ô ẩn (đã duyệt %d trạng thái).' % n)


def kiemtra(dapan, batdau, k):
    D = json.load(open(dapan, encoding='utf-8'))
    B = json.load(open(batdau, encoding='utf-8'))
    truth = [list(reversed(t)) for t in D['tubes']]
    mask = [list(reversed(t)) for t in B['tubes']]
    rng = random.Random(3)
    wins = 0
    for _ in range(k):
        w = [[(c, m != UNK) for c, m in zip(t, mt)] for t, mt in zip(truth, mask)]
        ok, _ = rollout(w, rng)
        wins += ok
    print('Chiến thuật thắng %d/%d lần trên đáp án thật' % (wins, k))


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == 'duong':
        S = json.load(open(sys.argv[1], encoding='utf-8'))
        duong([list(reversed(t)) for t in S['tubes']]); sys.exit()
    if sys.argv[1] == 'kiemtra':
        kiemtra(sys.argv[2], sys.argv[3], int(sys.argv[4])); sys.exit()
    S = json.load(open(sys.argv[1], encoding='utf-8'))
    mode = sys.argv[2] if len(sys.argv) > 2 else 'thang'
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 120
    lim = float(sys.argv[4]) if len(sys.argv) > 4 else 60
    tubes = [list(reversed(t)) for t in S['tubes']]
    evaluate(tubes, n, lim, mode)
