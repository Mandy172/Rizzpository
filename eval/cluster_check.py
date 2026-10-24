import json
import numpy as np
import ollama
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import normalize

data = json.load(open("data/complaints.json", encoding="utf-8"))
texts = [c["text"] for c in data]
truth = [c.get("duplicate_group") if c.get("duplicate_group") not in (None, "", "None") else f"solo-{i}"
         for i, c in enumerate(data)]

# Part 1: does bge-m3 understand meaning across languages?
demo = [
    "Big pothole near the bus stop",
    "बस थांब्याजवळ रस्त्यावर मोठा खड्डा आहे",
    "Bus stop ke paas sadak mein gaddha hai",
    "Garbage not collected for 3 days",
]
v = normalize(np.array(ollama.embed(model="bge-m3", input=demo)["embeddings"]))
print("Cosine similarity of pothole sentences to the first one:", np.round(v[1:] @ v[0], 2))
print("(first two should be high, garbage should be clearly lower)\n")

# Part 2: blind clustering vs the answer key
vecs = normalize(np.array(ollama.embed(model="bge-m3", input=texts)["embeddings"]))
print("embedding size:", vecs.shape)
best = None
for th in (0.25, 0.3, 0.35, 0.4, 0.5):
    lab = AgglomerativeClustering(n_clusters=None, distance_threshold=th,
                                  metric="cosine", linkage="average").fit_predict(vecs)
    ari = adjusted_rand_score(truth, lab)
    print(f"threshold {th}: {len(set(lab))} clusters, agreement with answer key (ARI) = {ari:.2f}")
    if best is None or ari > best[0]:
        best = (ari, th, lab)

print("\nBest threshold", best[1], "- clusters of 2 or more:")
for k in sorted(set(best[2])):
    idx = [i for i, l in enumerate(best[2]) if l == k]
    if len(idx) > 1:
        print(f"\nCluster {k} ({len(idx)} reports)")
        for i in idx[:6]:
            print(f"  [{truth[i]}] {texts[i][:70]}")
