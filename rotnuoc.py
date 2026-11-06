# -*- coding: utf-8 -*-
"""Bộ giải trò rót nước (WaterSort, com.global.tmslg) có ô ẩn '?'.

Luật (từ WaterSortBattleData.CheckAction): lọ 4 lớp; rót được khi lọ nguồn có màu trên cùng,
lọ đích còn chỗ và (rỗng hoặc cùng màu trên cùng). Rót cả khối cùng màu trên cùng, tối đa
bằng chỗ trống. Ô ẩn (máy chủ gửi màu 0) chỉ lộ khi lên trên cùng. Thắng khi mọi lọ rỗng
hoặc đầy 4 cùng màu.

Trạng thái JSON (work/rot.json):
  {"cap":4, "tubes":[["nau","hongnhat","reu","la"], ["reu","tim","dodam","?"], ..., []]}
  mỗi lọ liệt kê TỪ TRÊN XUỐNG; lọ rỗng = [].
Lệnh:
  python rotnuoc.py STATE goiy [so_the_gioi=150] [giay=60]  -> gợi ý nước tiếp theo
  python rotnuoc.py STATE rot A B                           -> ghi nhận rót lọ A sang B (đánh số từ 1)
  python rotnuoc.py STATE mo A mau                          -> ghi nhận ô vừa lộ ở đỉnh lọ A là màu gì
  python rotnuoc.py STATE show
"""
import sys, json, random, time
from collections import Counter

sys.setrecursionlimit(10000)
UNK = '?'


def top_block(t):
    """t: list dưới->trên. Trả (màu, số lớp) của khối trên cùng (đã biết)."""
    if not t or t[-1] == UNK:
        return None, 0
    c = t[-1]
    n = 1
    while n < len(t) and t[-1 - n] == c:
        n += 1
    return c, n


def legal_moves(tubes, cap):
    res = []
    for a, ta in enumerate(tubes):
        c, n = top_block(ta)
        if not c:
            continue
        uniform = n == len(ta)
        if uniform and n == cap:
            continue                      # lọ đã xong
        tried_empty = False
        for b, tb in enumerate(tubes):
            if a == b or len(tb) >= cap:
                continue
            if tb:
                if tb[-1] != c:
                    continue
            else:
                if uniform or tried_empty:
                    continue              # đổ cả lọ một màu sang lọ rỗng: vô ích; chỉ thử 1 lọ rỗng
                tried_empty = True
            res.append((a, b))
    return res


def apply(tubes, a, b, cap):
    tubes = [list(t) for t in tubes]
    c, n = top_block(tubes[a])
    m = min(n, cap - len(tubes[b]))
    for _ in range(m):
        tubes[b].append(tubes[a].pop())
    return tubes, m


def won(tubes, cap):
    return all(not t or (len(t) == cap and len(set(t)) == 1 and t[0] != UNK) for t in tubes)


def key(tubes):
    return tuple(sorted(tuple(t) for t in tubes))


def solve_full(tubes, cap, deadline, memo=None):
    """Giải khi biết hết. Trả list nước hoặc None. Ném TimeoutError khi quá hạn."""
    dead = set() if memo is None else memo
    path = []

    def dfs(ts):
        if won(ts, cap):
            return True
        k = key(ts)
        if k in dead:
            return False
        dead.add(k)                       # đánh dấu ngay khi vào (tránh vòng lặp)
        if time.time() > deadline:
            raise TimeoutError
        mv = legal_moves(ts, cap)
        # ưu tiên: rót vào lọ cùng màu (không tốn lọ rỗng), rồi tạo lọ hoàn chỉnh
        def score(m):
            a, b = m
            s = 0
            if ts[b]:
                s -= 2
            nt, cnt = apply(ts, a, b, cap)
            if len(nt[b]) == cap and len(set(nt[b])) == 1:
                s -= 3
            if not nt[a]:
                s -= 1
            return s
        mv.sort(key=score)
        for a, b in mv:
            nt, _ = apply(ts, a, b, cap)
            path.append((a, b))
            if dfs(nt):
                return True
            path.pop()
        dead.add(k)
        return False

    return list(path) if dfs([list(t) for t in tubes]) else None


def hidden_pool(tubes, cap):
    cnt = Counter(c for t in tubes for c in t if c != UNK)
    nunk = sum(t.count(UNK) for t in tubes)
    pool = []
    for c, n in cnt.items():
        pool += [c] * (cap - n)
    extra = nunk - len(pool)
    if extra > 0 and extra % cap == 0:
        for k in range(extra // cap):          # màu chưa từng thấy: đặt tên tạm
            pool += ['chuabiet%d' % (k + 1)] * cap
    if len(pool) != nunk:
        raise ValueError('Số ô ẩn (%d) không khớp số màu còn thiếu (%d): %s' % (nunk, len(pool), dict(Counter(pool))))
    return pool


def sample_world(tubes, pool, rng):
    p = pool[:]
    rng.shuffle(p)
    it = iter(p)
    return [[next(it) if c == UNK else c for c in t] for t in tubes]


def suggest(tubes, cap, nworld, limit):
    pool = hidden_pool(tubes, cap)
    rng = random.Random(1)
    worlds = [sample_world(tubes, pool, rng) for _ in range(nworld)] if pool else [tubes]
    if not pool:
        worlds = worlds[:1]
    moves = legal_moves(tubes, cap)
    if not moves:
        print('KHÔNG còn nước đi hợp lệ.')
        return
    t0 = time.time()
    per = limit / max(1, len(moves))
    results = []
    for a, b in moves:
        ok = tot = to = 0
        dl = time.time() + per
        for w in worlds:
            if time.time() > dl:
                break
            nw, _ = apply(w, a, b, cap)
            tot += 1
            try:
                if solve_full(nw, cap, time.time() + 2.0) is not None:
                    ok += 1
            except TimeoutError:
                to += 1
        nt, m = apply(tubes, a, b, cap)
        reveal = nt[a][-1:] == [UNK]
        h = 0
        if tubes[b]:
            h += 3                         # chồng lên cùng màu, không tốn lọ rỗng
        if len(nt[b]) == cap and len(set(nt[b])) == 1:
            h += 4                         # hoàn thành một lọ
        if not nt[a]:
            h += 2                         # giải phóng một lọ
        if reveal:
            h += 1                         # mở thông tin
        if m < top_block(tubes[a])[1]:
            h -= 2                         # tách khối màu ra hai nơi
        results.append((ok / max(1, tot), a, b, tot, to, reveal, h))
    best = max(r[0] for r in results)
    results.sort(key=lambda r: (-(r[0] >= best - 0.03), -r[6], -r[0]))
    print('Ô ẩn còn lại:', dict(Counter(pool)) if pool else 'không')
    print('Nước    tỉ lệ thắng (thế giới thử)  ghi chú')
    for r, a, b, tot, to, rev, h in results[:10]:
        print('%2d -> %-2d  %5.1f%%  (%d, quá giờ %d) điểm phụ %d%s' % (a + 1, b + 1, 100 * r, tot, to, h, '  [mở ô ẩn]' if rev else ''))
    print('(%.0fs)' % (time.time() - t0))


def main():
    path, cmd = sys.argv[1], sys.argv[2]
    S = json.load(open(path, encoding='utf-8'))
    cap = S.get('cap', 4)
    tubes = [list(reversed(t)) for t in S['tubes']]       # nội bộ: dưới -> trên

    def save():
        S['tubes'] = [list(reversed(t)) for t in tubes]
        json.dump(S, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    def show():
        for i, t in enumerate(tubes):
            print('  lọ %2d: %s' % (i + 1, ' '.join(reversed(t)) if t else '(rỗng)'))
        if won(tubes, cap):
            print('  ==> ĐÃ XẾP XONG')

    if cmd == 'show':
        show()
    elif cmd == 'goiy':
        n = int(sys.argv[3]) if len(sys.argv) > 3 else 150
        lim = float(sys.argv[4]) if len(sys.argv) > 4 else 60
        suggest(tubes, cap, n, lim)
    elif cmd == 'rot':
        a, b = int(sys.argv[3]) - 1, int(sys.argv[4]) - 1
        if (a, b) not in [(x, y) for x, y in legal_moves(tubes, cap)] and not (
                tubes[a] and top_block(tubes[a])[0] and len(tubes[b]) < cap and (not tubes[b] or tubes[b][-1] == tubes[a][-1])):
            print('Nước không hợp lệ!'); sys.exit(1)
        tubes, m = apply(tubes, a, b, cap)
        print('Rót %d lớp.' % m)
        if tubes[a] and tubes[a][-1] == UNK:
            print('  -> lọ %d lộ ô ẩn: xem màn hình rồi gọi "mo %d <màu>"' % (a + 1, a + 1))
        save(); show()
    elif cmd == 'mo':
        a, c = int(sys.argv[3]) - 1, sys.argv[4]
        assert tubes[a][-1] == UNK
        tubes[a][-1] = c
        save(); show()
        hidden_pool(tubes, cap)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
