from typing import List, Dict
import json

def build_canonical_index(canonical_items_file: str) -> Dict[str, List[str]]:
    with open(canonical_items_file, 'r') as file:
        canonical_items = json.load(file)

    index = {}
    for item in canonical_items:
        normalized_name = item['name'].lower()
        if normalized_name not in index:
            index[normalized_name] = []
        index[normalized_name].append(item['name'])

    return index

if __name__ == "__main__":
    canonical_items_file = '../app/data/canonical_items.json'
    index = build_canonical_index(canonical_items_file)
    
    with open('../app/data/canonical_index.json', 'w') as index_file:
        json.dump(index, index_file, indent=4)