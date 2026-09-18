"""
Preprocessing + train/val/test split for the Student Early-Warning dataset.

Steps:
  1. Load raw CSV
  2. Basic text cleaning (lowercasing, whitespace normalization)
  3. Stratified split into train/val/test (70/15/15) on `category`
  4. Save processed splits to data/

Usage:
    python preprocess.py --in ../../data/raw_dataset.csv --out_dir ../../data
"""

import argparse
import re
import pandas as pd
from sklearn.model_selection import train_test_split


def clean_text(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text


def main(in_path: str, out_dir: str):
    df = pd.read_csv(in_path)
    df["text"] = df["text"].astype(str).apply(clean_text)

    # drop any empty/duplicate rows
    before = len(df)
    df = df.drop_duplicates(subset=["text"]).dropna(subset=["text", "category", "urgency"])
    after = len(df)
    print(f"Dropped {before - after} duplicate/empty rows. {after} remaining.")

    # stratified split: 70% train, 15% val, 15% test (stratify on category)
    train_df, temp_df = train_test_split(
        df, test_size=0.30, random_state=42, stratify=df["category"]
    )
    val_df, test_df = train_test_split(
        temp_df, test_size=0.50, random_state=42, stratify=temp_df["category"]
    )

    train_df.to_csv(f"{out_dir}/train.csv", index=False)
    val_df.to_csv(f"{out_dir}/val.csv", index=False)
    test_df.to_csv(f"{out_dir}/test.csv", index=False)

    print(f"Train: {len(train_df)}  Val: {len(val_df)}  Test: {len(test_df)}")
    print("\nTrain category distribution:\n", train_df["category"].value_counts())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", type=str, default="../../data/raw_dataset.csv")
    parser.add_argument("--out_dir", type=str, default="../../data")
    args = parser.parse_args()
    main(args.in_path, args.out_dir)
