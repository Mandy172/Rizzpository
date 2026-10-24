import json, copy
from collections import Counter
from sklearn.metrics import adjusted_rand_score as ari
from backend.cluster import cluster_complaints

res = json.load(open("data/results.json", encoding="utf-8"))

def score(items, label):
    truth = [c["duplicate_group"] if c.get("duplicate_group") not in (None, "", "None") else f"solo-{i}"
             for i, c in enumerate(items)]
    pred = [c["cluster_id"] if c.get("cluster_id", -1) >= 0 else 10000 + i for i, c in enumerate(items)]
    sizes = sorted(Counter(c["cluster_id"] for c in items if c.get("cluster_id", -1) >= 0).values(), reverse=True)
    print(f"{label}: ARI = {ari(truth, pred):.2f} | cluster sizes = {sizes}")

score(res, "Before (stored)")
fresh = cluster_complaints(copy.deepcopy(res))
score(fresh, "After (new code)")
print("Answer key sizes:", sorted(Counter(c["duplicate_group"] for c in res
      if c.get("duplicate_group") not in (None, "", "None")).values(), reverse=True))
