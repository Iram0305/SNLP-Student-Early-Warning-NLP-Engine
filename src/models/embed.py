"""
Sentence-embedding generation for the Week 3 improved model.

Encodes the train/val/test text splits using a pretrained sentence-transformer
(all-MiniLM-L6-v2, 384-dim) and caches the resulting vectors as .npy files so
the classifier head can be retrained quickly without re-encoding every time.

Usage:
    python embed.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
EMBED_DIR = Path(__file__).resolve().parent / "embeddings"
EMBED_DIR.mkdir(exist_ok=True)

MODEL_NAME = "all-MiniLM-L6-v2"


def embed_split(model, split_name: str):
    df = pd.read_csv(DATA_DIR / f"{split_name}.csv", keep_default_na=False)
    texts = df["text"].tolist()

    print(f"Encoding {len(texts)} examples from {split_name}.csv ...")
    vectors = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

    np.save(EMBED_DIR / f"{split_name}_embeddings.npy", vectors)
    df.to_csv(EMBED_DIR / f"{split_name}_labels.csv", index=False)

    print(f"Saved {vectors.shape} -> {EMBED_DIR / f'{split_name}_embeddings.npy'}")
    return vectors


def main():
    print(f"Loading sentence-transformer model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    for split in ["train", "val", "test"]:
        embed_split(model, split)

    print("\nDone. Embeddings cached in src/models/embeddings/")


if __name__ == "__main__":
    main()