from typing import List

def extract_items_from_text(ocr_text: str) -> List[str]:
    lines = ocr_text.splitlines()
    items = []
    for line in lines:
        # Basic filtering to ignore lines that are likely prices or totals
        if not any(char.isdigit() for char in line) and line.strip():
            items.append(line.strip())
    return items

def clean_item_name(item_name: str) -> str:
    # Normalize item names by lowering case and stripping whitespace
    return item_name.lower().strip()