"""
backend/cluster.py
──────────────────
Embeds complaint texts using bge-m3 (via Ollama) and clusters them
with HDBSCAN using cosine distance.

How it works:
  1. Each complaint text is sent to bge-m3 → returns a 1024-number
     vector that captures the *meaning* of the sentence.
  2. HDBSCAN finds groups of vectors that are close to each other
     (= similar meaning) without us telling it how many clusters to make.
  3. Each complaint gets a cluster_id:
       ≥ 0  → belongs to a group (duplicate / related issue)
       -1   → unique, doesn't match any group

Usage (from repo root):
    python -m backend.cluster                        # clusters data/results.json in place
    python -m backend.cluster --input data/results.json --min-cluster 2
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

import numpy as np
import requests
from hdbscan import HDBSCAN
from sklearn.preprocessing import normalize

# ── Config ────────────────────────────────────────────────────────────────────
OLLAMA_HOST  = "http://localhost:11434"
EMBED_MODEL  = "bge-m3"          # multilingual, works for EN / HI / MR / Hinglish
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── Step 1: Get embeddings from Ollama ───────────────────────────────────────
# We send each complaint text to bge-m3.
# It returns a list of 1024 floats — a point in 1024-dimensional space.
# Texts with similar meaning land close together in that space.
def embed_texts(texts: List[str]) -> np.ndarray:
    """Return (N, 1024) float32 array — one embedding row per text."""
    vectors = []
    for i, text in enumerate(texts):
        print(f"  Embedding {i+1}/{len(texts)}: {text[:55]}...")
        resp = requests.post(
            f"{OLLAMA_HOST}/api/embeddings",
            json={"model": EMBED_MODEL, "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        vec = resp.json()["embedding"]          # list of 1024 floats
        vectors.append(vec)

    arr = np.array(vectors, dtype=np.float32)

    # Normalize to unit length so cosine distance = euclidean distance.
    # This makes HDBSCAN work correctly with cosine similarity.
    return normalize(arr, norm="l2")


# ── Step 2: Cluster with HDBSCAN ─────────────────────────────────────────────
# HDBSCAN (Hierarchical Density-Based Spatial Clustering of Applications
# with Noise) needs no pre-set number of clusters.
# It finds dense regions automatically and labels outliers as -1.
#
# Key params:
#   min_cluster_size  – minimum complaints to form a group (default 2)
#   metric            – euclidean on L2-normalised vectors = cosine distance
def cluster_embeddings(embeddings: np.ndarray, min_cluster_size: int = 2) -> np.ndarray:
    """Return int array of cluster labels, -1 means noise / unique."""
    clusterer = HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",          # works as cosine after L2 normalisation
        cluster_selection_method="eom",
    )
    clusterer.fit(embeddings)
    return clusterer.labels_        # shape (N,), dtype int


# ── Step 3: Attach cluster_id back to the complaint dicts ────────────────────
def assign_clusters(complaints: List[dict], labels: np.ndarray) -> List[dict]:
    for complaint, label in zip(complaints, labels):
        complaint["cluster_id"] = int(label)
    return complaints


# ── Main entry point ─────────────────────────────────────────────────────────
def run_clustering(
    input_file: str = "data/results.json",
    output_file: str = "data/results.json",   # overwrites in place by default
    min_cluster_size: int = 2,
) -> List[dict]:
    input_path  = PROJECT_ROOT / input_file
    output_path = PROJECT_ROOT / output_file

    print(f"Loading complaints from {input_path}...")
    with open(input_path, encoding="utf-8") as f:
        complaints = json.load(f)

    texts = [c.get("text", c.get("summary", "")) for c in complaints]
    print(f"Embedding {len(texts)} complaints with {EMBED_MODEL}...")

    # --- embed ---
    try:
        embeddings = embed_texts(texts)
    except requests.exceptions.ConnectionError:
        print(
            "\n[ERROR] Cannot reach Ollama at http://localhost:11434\n"
            "Make sure Ollama is running and bge-m3 is pulled:\n"
            "  ollama pull bge-m3\n"
            "  ollama serve\n"
        )
        sys.exit(1)

    print(f"Clustering with HDBSCAN (min_cluster_size={min_cluster_size})...")
    labels = cluster_embeddings(embeddings, min_cluster_size=min_cluster_size)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise    = int((labels == -1).sum())
    print(f"Found {n_clusters} clusters, {n_noise} unique (noise) complaints.")

    complaints = assign_clusters(complaints, labels)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(complaints, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {output_path}")

    return complaints


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cluster civic complaints by semantic similarity.")
    parser.add_argument("--input",  default="data/results.json", help="Input JSON file")
    parser.add_argument("--output", default="data/results.json", help="Output JSON file")
    parser.add_argument("--min-cluster", type=int, default=2,
                        help="Min complaints to form a cluster (default 2)")
    args = parser.parse_args()

    run_clustering(
        input_file=args.input,
        output_file=args.output,
        min_cluster_size=args.min_cluster,
    )
