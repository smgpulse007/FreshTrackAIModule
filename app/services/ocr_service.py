from typing import Iterable, List, Optional, Union
import os
try:
    from paddleocr import PaddleOCR  # type: ignore
except Exception:  # pragma: no cover - optional dependency in tests
    PaddleOCR = None  # type: ignore
from PIL import Image
import numpy as np
import io
from app.core.logging import get_logger

class OCRService:
    def __init__(self, lang: str = 'en', engine: Optional[str] = None):
        # Engine can be 'PaddleOCR' or 'Tesseract'
        self.engine = (engine or os.getenv('OCR_ENGINE', 'PaddleOCR')).strip()
        self.lang = lang
        self.ocr = None
        self.logger = get_logger()
        if self.engine.lower() == 'paddleocr':
            if PaddleOCR:
                try:
                    # Initialize once; PaddleOCR lazy-loads models on first use.
                    self.ocr = PaddleOCR(lang=lang, use_angle_cls=True)
                    self.logger.info("OCR initialized: PaddleOCR")
                except Exception:
                    # PaddleOCR installed but backend 'paddle' missing or other init error
                    self.ocr = None
                    self.logger.error("Failed to initialize PaddleOCR; will attempt Tesseract fallback at runtime.")
            else:
                self.ocr = None
                self.logger.error("PaddleOCR package not available; will attempt Tesseract fallback at runtime.")
        elif self.engine.lower() == 'tesseract':
            # pytesseract is imported lazily in extract_text
            self.logger.info("OCR configured: Tesseract")
        else:
            # Unknown engine; default to none and let extract_text raise
            self.ocr = None
            self.logger.error("Unknown OCR engine configured: %s", self.engine)

    def _to_numpy(self, image: Union[Image.Image, bytes, bytearray, io.BytesIO]) -> np.ndarray:
        if image is None:
            raise ValueError("image is None")
        if isinstance(image, (bytes, bytearray)):
            image = Image.open(io.BytesIO(image))
        elif isinstance(image, io.BytesIO):
            image = Image.open(image)
        if isinstance(image, Image.Image):
            image = image.convert('RGB')
            return np.array(image)
        raise TypeError("Unsupported image type for OCR. Provide PIL.Image or bytes.")

    def extract_text(self, image: Union[Image.Image, bytes, bytearray, io.BytesIO]) -> str:
        np_img = self._to_numpy(image)
        eng = self.engine.lower()
        if eng == 'paddleocr' and self.ocr:
            try:
                result = self.ocr.ocr(np_img, cls=True)
            except Exception as e:
                # Paddle failed at runtime; fall through to Tesseract
                self.logger.error("PaddleOCR runtime error; falling back to Tesseract: %s", str(e))
            else:
                # result for single image is typically: [ [ [box, (text, conf)], ... ] ]
                entries = []
                if isinstance(result, list) and result:
                    inner = result[0]
                    if isinstance(inner, list):
                        entries = inner

                if not entries:
                    return ""

                # Prepare structures: compute y-center, x-left, height, keep only confident texts
                records = []
                heights: List[float] = []
                for it in entries:
                    try:
                        box, meta = it[0], it[1]
                        text, conf = meta[0], float(meta[1])
                        if not text:
                            continue
                        # simple confidence gate to reduce noise
                        if conf < 0.3:
                            continue
                        xs = [p[0] for p in box]
                        ys = [p[1] for p in box]
                        x_left = float(min(xs))
                        y_center = float(sum(ys) / 4.0)
                        # approximate height as vertical span
                        h = float(max(ys) - min(ys))
                        heights.append(h)
                        records.append((y_center, x_left, text))
                    except Exception:
                        continue

                if not records:
                    return ""

                # Sort by y (top to bottom), then x (left to right)
                records.sort(key=lambda r: (r[0], r[1]))

                # Determine line merge threshold using median height
                med_h = 0.0
                if heights:
                    hs = sorted(heights)
                    mid = len(hs) // 2
                    med_h = (hs[mid] if len(hs) % 2 == 1 else (hs[mid - 1] + hs[mid]) / 2.0) or 12.0
                line_thresh = max(10.0, 0.7 * med_h)

                # Group into lines
                lines_buckets: List[List[tuple]] = []
                current: List[tuple] = []
                current_y = None  # type: Optional[float]
                for y, x, t in records:
                    if current_y is None:
                        current = [(x, t)]
                        current_y = y
                        continue
                    if abs(y - current_y) <= line_thresh:
                        current.append((x, t))
                    else:
                        # flush current
                        current.sort(key=lambda z: z[0])
                        lines_buckets.append(current)
                        current = [(x, t)]
                        current_y = y
                if current:
                    current.sort(key=lambda z: z[0])
                    lines_buckets.append(current)

                lines: List[str] = [" ".join(t for _, t in bucket).strip() for bucket in lines_buckets if bucket]

                # Debug: log a preview of OCR lines
                try:
                    preview = " | ".join(lines[:5])
                    self.logger.info("PaddleOCR extracted %d lines. Preview: %s", len(lines), preview)
                except Exception:
                    pass

                return "\n".join(lines)

        # Tesseract path (explicit or fallback from Paddle)
        if eng == 'paddleocr' and self.ocr is None:
            self.logger.warning("Falling back to Tesseract OCR because PaddleOCR unavailable.")

        if eng == 'tesseract' or (eng == 'paddleocr' and self.ocr is None):
            try:
                import pytesseract  # type: ignore
            except Exception as e:
                raise RuntimeError(
                    "pytesseract not installed; install it or set OCR_ENGINE=PaddleOCR with valid backend"
                ) from e
            try:
                # If provided, honor explicit tesseract binary path
                tess_cmd = os.getenv('TESSERACT_CMD')
                if tess_cmd:
                    pytesseract.pytesseract.tesseract_cmd = tess_cmd  # type: ignore[attr-defined]
                text = pytesseract.image_to_string(Image.fromarray(np_img))
                return text
            except pytesseract.TesseractNotFoundError as e:  # type: ignore[attr-defined]
                raise RuntimeError("Tesseract binary not found. Install Tesseract OCR and ensure it's on PATH.") from e

        # No valid OCR engine available
        raise RuntimeError("No valid OCR engine available. Set OCR_ENGINE to PaddleOCR or Tesseract.")

    def parse_items(self, ocr_text: str) -> List[str]:
        if not isinstance(ocr_text, str):
            raise ValueError("ocr_text must be a string")
        items: List[str] = []
        for raw in ocr_text.splitlines():
            line = raw.strip()
            if not line:
                continue
            # Filter totals, payments, card info, prices-only lines
            lower = line.lower()
            if any(k in lower for k in ["total", "subtotal", "tax", "change", "visa", "mastercard", "debit", "credit"]):
                continue
            tokens = line.split()
            # Drop price-like tail tokens ($2.99, 2.99, 3 X 1.99)
            while tokens and (self._is_price_token(tokens[-1]) or tokens[-1].lower() in {"f", "n", "o"}):
                tokens.pop()
            if not tokens:
                continue

            # Remove UPC/EAN-like or long digit-only tokens and short flags in the middle
            cleaned: List[str] = []
            for t in tokens:
                t_clean = t.strip("-:;.,#")
                if not t_clean:
                    continue
                if self._is_upc_like(t_clean):
                    continue
                if t_clean.lower() in {"f", "n", "o"}:
                    continue
                # remove unit-only tokens like 16OZ, 3LB, 12CT unless part of a word
                if self._is_qty_token(t_clean):
                    continue
                cleaned.append(t_clean)

            if not cleaned:
                continue

            core = " ".join(cleaned).strip()
            core = core.replace("  ", " ")
            if self._looks_like_item(core):
                items.append(core)
        return items

    def _strip_trailing_qty(self, text: str) -> str:
        tokens = text.split()
        if not tokens:
            return text
        last = tokens[-1]
        if any(last.endswith(suf) for suf in ["LB", "LBS", "OZ", "CT", "PK", "PKG", "EA"]):
            return " ".join(tokens[:-1])
        return text

    def _looks_like_item(self, line: str) -> bool:
        if len(line) < 3:
            return False
        # Disallow lines that are mostly numbers/symbols
        letters = sum(c.isalpha() for c in line)
        digits = sum(c.isdigit() for c in line)
        return letters >= digits and letters >= 3

    def _is_upc_like(self, token: str) -> bool:
        # UPC/EAN and similar: mostly digits and length >= 8
        if len(token) >= 8 and token.isdigit():
            return True
        # allow tokens with hyphens/spaces removed
        comp = token.replace("-", "")
        return len(comp) >= 8 and comp.isdigit()

    def _is_qty_token(self, token: str) -> bool:
        t = token.upper()
        # Patterns like 16OZ, 3LB, 12CT, 2PK, 1EA
        return bool(
            (any(t.endswith(suf) for suf in ["OZ", "LB", "LBS", "CT", "PK", "PKG", "EA"]) and any(ch.isdigit() for ch in t))
            or t in {"EA"}
        )

    def _is_price_token(self, token: str) -> bool:
        t = token.strip().replace(",", "")
        if t.startswith("$"):
            t = t[1:]
        # Accept 1.23 or 10 or 3x1.99
        return t.replace(".", "", 1).isdigit()