from pydantic import BaseModel
from typing import List, Optional, Dict

class ItemResult(BaseModel):
    original_text: str
    matched_item: Optional[str]
    shelf_life: Optional[Dict[str, str]]
    suggestions: Optional[List[str]] = None

class ReceiptResponse(BaseModel):
    items: List[ItemResult]