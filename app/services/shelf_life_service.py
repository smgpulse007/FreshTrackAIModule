from typing import Dict, Any, Optional, List
import json
from pathlib import Path


class ShelfLifeService:
    def __init__(self, foodkeeper_data_path: str):
        path = Path(foodkeeper_data_path)
        if not path.is_absolute():
            # Service root folder (.. / .. from this file): grocery-receipt-shelflife-service/
            service_root = Path(__file__).resolve().parents[2]
            candidate = service_root / path
            if candidate.exists():
                path = candidate
        if not path.exists():
            # Fallback to CWD-relative
            path = Path.cwd() / foodkeeper_data_path
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Expect schema: { "items": [ {"name": str, "shelf_life": {..}} ] }
        self.items: List[Dict[str, Any]] = data.get("items", []) if isinstance(data, dict) else []

    def get_shelf_life(self, item_name: str) -> Optional[Dict[str, Any]]:
        key = item_name.lower()
        for item in self.items:
            if item.get('name', '').lower() == key:
                return item.get('shelf_life')
        return None

    def get_all_item_names(self) -> List[str]:
        return [item.get('name', '') for item in self.items if item.get('name')]