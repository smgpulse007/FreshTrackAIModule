from __future__ import annotations
from typing import List, Tuple
import numpy as np
import torch
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model_name: str = "intfloat/e5-small-v2", device: str | None = None) -> None:
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model = SentenceTransformer(model_name, device=self.device)
        self.canonical_names: List[str] = []
        self.canonical_embs: np.ndarray | None = None  # shape (N, D)

    def _encode(self, texts: List[str]) -> np.ndarray:
        # E5 models expect "query: ..." for queries and "passage: ..." for docs; for simplicity use raw texts
        embs = self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True, device=self.device)
        return embs.astype(np.float32)

    def load_canonical(self, names: List[str]) -> None:
        self.canonical_names = list(dict.fromkeys(names))  # dedupe preserving order
        self.canonical_embs = self._encode(self.canonical_names)

    def top_k(self, text: str, k: int = 3) -> List[Tuple[str, float]]:
        if self.canonical_embs is None or not self.canonical_names:
            return []
        q = self._encode([text])  # shape (1, D)
        # cosine since already normalized
        scores = (self.canonical_embs @ q.T).squeeze(-1)  # shape (N,)
        idxs = np.argsort(-scores)[:k]
        return [(self.canonical_names[i], float(scores[i])) for i in idxs]