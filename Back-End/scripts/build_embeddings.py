import json
import numpy as np

from sentence_transformers import SentenceTransformer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data" / "cleaned_catalog.json"

OUTPUT_EMBEDDINGS = BASE_DIR / "data" / "catalog_embeddings.npy"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

texts = [x["embedding_text"] for x in data]

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

embeddings = model.encode(
    texts,
    normalize_embeddings=True,
    batch_size=32,
    show_progress_bar=True,
)

np.save(
    OUTPUT_EMBEDDINGS,
    embeddings,
)

print("Saved embeddings.")