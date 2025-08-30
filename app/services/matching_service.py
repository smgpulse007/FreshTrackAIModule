from typing import List, Tuple
import re
from app.services.embedding_service import EmbeddingService
from app.services.shelf_life_service import ShelfLifeService


class MatchingService:
    def __init__(self, embedding: EmbeddingService | None = None, shelf_life: ShelfLifeService | None = None, threshold: float = 0.8):
        # If an embedding service is provided, use it for matching
        self.embedding = embedding
        self.threshold = threshold
        # Canonical names default; when ShelfLifeService is provided, use its item names
        self.canonical_names: List[str] = []
        if shelf_life:
            self.canonical_names = shelf_life.get_all_item_names()
        if not self.canonical_names:
            self.canonical_names = [
                "Onion, fresh",
                "Green Bell Pepper",
                "Blueberries",
                "Blackberries",
                "Milk (pasteurized)",
                "Bread, commercial",
                "Chicken, raw",
                "Apples",
                "Bananas",
                "Carrots",
                "Potatoes",
                "Tomatoes",
            ]
        if self.embedding:
            self.embedding.load_canonical(self.canonical_names)

        # Heuristic backups
        self.token_map = {
            "grn": "green",
            "grn.": "green",
            "bell": "bell",
            "ppr": "pepper",
            "pep": "pepper",
            "onion": "onion",
            "ylw": "yellow",
            "yell": "yellow",
            "mnch": "bunch",
            "blubry": "blueberry",
            "bluberries": "blueberries",
        }

    def _normalize(self, text: str) -> str:
        text = text.strip()
        text = re.sub(r"\b\d+\s*(lb|lbs|oz|ct|pk|pkg|ea)\b", "", text, flags=re.I)
        text = re.sub(r"\$?\d+[\d\.,]*$", "", text).strip()
        return re.sub(r"\s+", " ", text)

    def _expand_tokens(self, text: str) -> str:
        tokens = re.split(r"\s+|[-_/]", text.lower())
        out: List[str] = []
        for t in tokens:
            if not t:
                continue
            out.append(self.token_map.get(t, t))
        return " ".join(out).strip()

    def _confident_rules(self, norm_text: str, expanded: str) -> str | None:
        if "onion" in expanded:
            return "Onion, fresh"
        if all(k in expanded for k in ["green", "bell", "pepper"]):
            return "Green Bell Pepper"
        return None

    def match_item(self, item_name: str) -> str | Tuple[None, List[str]]:
        norm = self._normalize(item_name)
        expanded = self._expand_tokens(norm)
        direct = self._confident_rules(norm, expanded)
        if direct:
            return direct

        if self.embedding and self.embedding.canonical_embs is not None:
            top = self.embedding.top_k(expanded, k=3)
            if not top:
                return None, self._suggestions(expanded)
            best_name, best_score = top[0]
            if best_score >= self.threshold:
                return best_name
            return None, [n for n, _ in top]

        # Fallback heuristic suggestions
        return None, self._suggestions(expanded)

    def _suggestions(self, expanded: str, top_n: int = 3) -> List[str]:
        scores = []
        for name in self.canonical_names:
            name_tokens = set(re.findall(r"[a-z]+", name.lower()))
            query_tokens = set(re.findall(r"[a-z]+", expanded))
            overlap = len(name_tokens & query_tokens)
            scores.append((name, overlap))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [n for n, _ in scores[:top_n]] or self.canonical_names[:top_n]