import json,sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rotnuoc import hidden_pool, UNK
S=json.load(open(sys.argv[1],encoding='utf-8'))
tubes=[list(reversed(t)) for t in S['tubes']]
pool=hidden_pool(tubes,4)
names=[]
for t in tubes:
    for c in t:
        if c!=UNK and c not in names: names.append(c)
for c in pool:
    if c not in names: names.append(c)
assert len(names)<=14,len(names)
idx={c:i+1 for i,c in enumerate(names)}
idx[UNK]=15
print(len(names),len(tubes))
for t in tubes: print(len(t),*[idx[c] for c in t])
with open(sys.argv[2],'w') as f:
    f.write(' '.join(names))
