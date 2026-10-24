"""
backend/cluster.py
──────────────────
Semantic Multilingual Clustering for Civic Complaints.
Groups citizen reports referring to the same physical issue across
English, Hindi, Marathi, and Hinglish.

Key Pipeline:
  1. Multilingual Embedding: Converts text into dense vector space (bge-m3 / multilingual cache).
  2. Cosine Distance Normalization: L2 unit normalization.
  3. Density-Based Clustering: HDBSCAN with adaptive distance threshold for small datasets.
  4. Deduplication & Metrics: Computes cluster IDs, report counts, and benchmark accuracy.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import requests
from hdbscan import HDBSCAN
from sklearn.cluster import AgglomerativeClustering
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import adjusted_rand_score, homogeneity_completeness_v_measure
from sklearn.preprocessing import normalize

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OLLAMA_HOST  = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
EMBED_MODEL  = os.environ.get("EMBED_MODEL", "bge-m3")
CACHE_FILE   = PROJECT_ROOT / "data" / ".embeddings_cache.json"


def _text_hash(text: str) -> str:
    """MD5 hash for caching text embeddings."""
    return hashlib.md5(text.strip().encode("utf-8")).hexdigest()


def _load_cache() -> Dict[str, List[float]]:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: Dict[str, List[float]]) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"[Warning] Failed to save embeddings cache: {e}")


def _fallback_tfidf_embeddings(texts: List[str]) -> np.ndarray:
    """Multilingual sub-word character n-gram TF-IDF fallback when Ollama is unreachable."""
    print("  [Notice] Using multilingual character n-gram fallback embeddings...")
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=1,
        sublinear_tf=True,
    )
    tfidf = vectorizer.fit_transform(texts)
    dense = tfidf.toarray().astype(np.float32)
    return normalize(dense, norm="l2")


def embed_texts(texts: List[str], use_cache: bool = True) -> np.ndarray:
    """Generate L2-normalized embeddings for a list of complaints."""
    cache = _load_cache() if use_cache else {}
    vectors = []
    missing_indices = []
    missing_texts = []

    for i, t in enumerate(texts):
        h = _text_hash(t)
        if use_cache and h in cache:
            vectors.append(cache[h])
        else:
            vectors.append(None)
            missing_indices.append(i)
            missing_texts.append(t)

    if missing_texts:
        print(f"Embedding {len(missing_texts)} uncached complaints with '{EMBED_MODEL}'...")
        ollama_failed = False

        for idx, text in zip(missing_indices, missing_texts):
            clean_text = text.strip() or "empty complaint"
            try:
                resp = requests.post(
                    f"{OLLAMA_HOST}/api/embeddings",
                    json={"model": EMBED_MODEL, "prompt": clean_text},
                    timeout=20,
                )
                if resp.status_code == 200:
                    vec = resp.json().get("embedding")
                    vectors[idx] = vec
                    cache[_text_hash(clean_text)] = vec
                else:
                    ollama_failed = True
                    break
            except Exception:
                ollama_failed = True
                break

        if ollama_failed:
            print(f"  [Warning] Ollama ({OLLAMA_HOST}) unreachable or '{EMBED_MODEL}' not loaded.")
            raise RuntimeError("bge-m3 embeddings unavailable: open Ollama and run: ollama pull bge-m3")

        if use_cache:
            _save_cache(cache)

    arr = np.array(vectors, dtype=np.float32)
    return normalize(arr, norm="l2")


def cluster_embeddings(
    embeddings: np.ndarray,
    min_cluster_size: int = 2,
    distance_threshold: float = 0.35,
) -> np.ndarray:
    """Cluster embeddings using HDBSCAN with adaptive fallback for sparse small datasets."""
    n_samples = len(embeddings)
    if n_samples < min_cluster_size:
        return np.full(n_samples, -1, dtype=int)

    # 1. Primary: HDBSCAN (density-based with cosine metric)
    try:
        clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric="euclidean",  # On L2-normalized vectors, Euclidean order matches Cosine distance
            cluster_selection_method="eom",
        )
        labels = clusterer.fit_predict(embeddings)
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)

        # If HDBSCAN found clusters, return them
        if n_clusters >= 1:
            return labels
    except Exception as e:
        print(f"[Warning] HDBSCAN step encountered: {e}")

    # 2. Adaptive Fallback: Agglomerative Clustering with Cosine Distance threshold
    # Useful when dataset is small (< 50 items) or density is uniform
    print(f"  [Notice] Running cosine threshold clustering (threshold={distance_threshold})...")
    agg = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=distance_threshold,
        metric="cosine",
        linkage="average",
    )
    agg_labels = agg.fit_predict(embeddings)

    # Group counts: items in a cluster of size 1 are marked as noise (-1)
    unique_labels, counts = np.unique(agg_labels, return_counts=True)
    size_map = dict(zip(unique_labels, counts))

    final_labels = np.array([lbl if size_map[lbl] >= min_cluster_size else -1 for lbl in agg_labels], dtype=int)

    # Remap positive cluster labels to sequential 0, 1, 2...
    remap = {}
    next_id = 0
    clean_labels = []
    for l in final_labels:
        if l == -1:
            clean_labels.append(-1)
        else:
            if l not in remap:
                remap[l] = next_id
                next_id += 1
            clean_labels.append(remap[l])

    return np.array(clean_labels, dtype=int)



def agglomerative_labels(embeddings, min_cluster_size=2, distance_threshold=0.25):
    """Cosine agglomerative clustering. Singletons become -1 (unique)."""
    n = len(embeddings)
    if n < min_cluster_size:
        return np.full(n, -1, dtype=int)
    lab = AgglomerativeClustering(
        n_clusters=None, distance_threshold=distance_threshold,
        metric="cosine", linkage="average",
    ).fit_predict(embeddings)
    sizes = {l: int((lab == l).sum()) for l in set(lab)}
    return np.array([l if sizes[l] >= min_cluster_size else -1 for l in lab], dtype=int)


def cluster_complaints(
    complaints: List[dict],
    min_cluster_size: int = 2,
    distance_threshold: float = 0.25,
) -> List[dict]:
    """Cluster reports within their predicted service area and return enriched records.

    Triage runs before deduplication, so a pothole and a water leak should never
    be grouped just because both reports mention the same landmark. Partitioning
    by category and department preserves that operational boundary and reduces
    false duplicate groups.
    """
    labels = np.full(len(complaints), -1, dtype=int)
    service_areas: Dict[Tuple[str, str], List[int]] = {}
    for index, complaint in enumerate(complaints):
        key = (
            str(complaint.get("category", "other")),
            str(complaint.get("department", "unknown")),
        )
        service_areas.setdefault(key, []).append(index)

    next_cluster_id = 0
    for indices in service_areas.values():
        if len(indices) < min_cluster_size:
            continue
        texts = [complaints[index].get("text", complaints[index].get("summary", "")) for index in indices]
        group_embeddings = embed_texts(texts)
        group_labels = agglomerative_labels(
            group_embeddings,
            min_cluster_size=min_cluster_size,
            distance_threshold=distance_threshold,
        )
        local_to_global: Dict[int, int] = {}
        for index, local_label in zip(indices, group_labels):
            if local_label < 0:
                continue
            if int(local_label) not in local_to_global:
                local_to_global[int(local_label)] = next_cluster_id
                next_cluster_id += 1
            labels[index] = local_to_global[int(local_label)]

    # Compute group sizes
    label_counts: Dict[int, int] = {}
    for l in labels:
        if l >= 0:
            label_counts[l] = label_counts.get(l, 0) + 1

    for c, l in zip(complaints, labels):
        c["cluster_id"] = int(l)
        c["reports"] = label_counts.get(int(l), 1)

    return complaints


def evaluate_against_ground_truth(
    complaints: List[dict],
    ground_truth_key: str = "duplicate_group",
) -> dict:
    """Evaluate clustering quality against expected duplicate_group annotations."""
    labeled_items = [c for c in complaints if c.get(ground_truth_key)]
    if not labeled_items:
        return {"status": "No ground truth duplicate_group labels found."}

    y_true = [c[ground_truth_key] for c in labeled_items]
    y_pred = [c.get("cluster_id", -1) for c in labeled_items]

    # Convert true strings to integer codes
    unique_true = list(set(y_true))
    true_map = {k: i for i, k in enumerate(unique_true)}
    y_true_codes = [true_map[k] for k in y_true]

    ari = adjusted_rand_score(y_true_codes, y_pred)
    h, c, v = homogeneity_completeness_v_measure(y_true_codes, y_pred)

    return {
        "labeled_samples": len(labeled_items),
        "true_duplicate_groups": len(unique_true),
        "adjusted_rand_index": round(float(ari), 4),
        "homogeneity": round(float(h), 4),
        "completeness": round(float(c), 4),
        "v_measure": round(float(v), 4),
    }


def run_pipeline_cluster(
    input_file: str = "data/results.json",
    output_file: str = "data/results.json",
    min_cluster_size: int = 2,
    distance_threshold: float = 0.35,
    eval_file: Optional[str] = "data/complaints.json",
) -> List[dict]:
    """CLI execution function."""
    in_path = PROJECT_ROOT / input_file
    out_path = PROJECT_ROOT / output_file

    print(f"📂 Loading complaints from: {in_path}")
    with open(in_path, "r", encoding="utf-8") as f:
        complaints = json.load(f)

    print(f"🔍 Clustering {len(complaints)} complaints (min_cluster_size={min_cluster_size})...")
    clustered = cluster_complaints(
        complaints,
        min_cluster_size=min_cluster_size,
        distance_threshold=distance_threshold,
    )

    clusters_found = len({c["cluster_id"] for c in clustered if c["cluster_id"] >= 0})
    singletons = sum(1 for c in clustered if c["cluster_id"] == -1)

    print(f"\n✅ Clustering Complete:")
    print(f"   • Total Complaints: {len(clustered)}")
    print(f"   • Incident Groups Formed: {clusters_found}")
    print(f"   • Unique Singletons: {singletons}")

    # Display Top Clusters summary
    print("\n📋 Detected Multi-Report Groups:")
    group_map: Dict[int, List[dict]] = {}
    for c in clustered:
        cid = c["cluster_id"]
        if cid >= 0:
            group_map.setdefault(cid, []).append(c)

    for cid, items in sorted(group_map.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        first_text = items[0].get("text", "")[:60]
        langs = list({i.get("language", "en") for i in items})
        print(f"   [Group #{cid}] ({len(items)} reports) Languages: {langs}")
        print(f"       Sample: \"{first_text}...\"")

    # Evaluation against complaints.json if available
    if eval_file:
        eval_path = PROJECT_ROOT / eval_file
        if eval_path.exists():
            with open(eval_path, "r", encoding="utf-8") as f:
                gt_data = json.load(f)
            # Map duplicate_group to clustered by id
            gt_map = {item["id"]: item.get("duplicate_group") for item in gt_data if "id" in item}
            for c in clustered:
                if c.get("id") in gt_map:
                    c["duplicate_group"] = gt_map[c["id"]]

            metrics = evaluate_against_ground_truth(clustered)
            print("\n📊 Ground-Truth Benchmark Metrics:")
            for k, val in metrics.items():
                print(f"   • {k}: {val}")

    # Write output
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(clustered, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Saved updated results with cluster_id & reports to: {out_path}")

    return clustered


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multilingual Semantic Clustering for Civic Complaints.")
    parser.add_argument("--input", default="data/results.json", help="Input JSON complaints path")
    parser.add_argument("--output", default="data/results.json", help="Output JSON path")
    parser.add_argument("--min-cluster", type=int, default=2, help="Minimum complaints per cluster")
    parser.add_argument("--threshold", type=float, default=0.20, help="Cosine distance threshold")
    parser.add_argument("--eval", default="data/complaints.json", help="Ground truth file for validation")
    args = parser.parse_args()

    run_pipeline_cluster(
        input_file=args.input,
        output_file=args.output,
        min_cluster_size=args.min_cluster,
        distance_threshold=args.threshold,
        eval_file=args.eval,
    )
