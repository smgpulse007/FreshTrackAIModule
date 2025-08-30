# Minimal FastAPI app for quick testing
from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image
import pytesseract
import io
import re
from typing import List

# Shelf life database
SHELF_LIFE_DATA = {
    'Bread, commercial': {
        'pantry': '2-4 days',
        'fridge': '7-12 days', 
        'freezer': '3 months'
    },
    'Milk (pasteurized)': {
        'pantry': 'Not recommended',
        'fridge': '4-7 days past sell-by',
        'freezer': '1 month (quality may change)'
    },
    'Eggs, fresh': {
        'pantry': 'Not recommended',
        'fridge': '3-5 weeks',
        'freezer': '1 year (beaten eggs)'
    },
    'Butter': {
        'pantry': '1-2 days',
        'fridge': '1-3 months',
        'freezer': '6-9 months'
    },
    'Peanut Butter': {
        'pantry': '6-12 months',
        'fridge': '6-12 months',
        'freezer': 'Not recommended'
    },
    'Coffee, ground': {
        'pantry': '3-5 months (unopened), 1-2 weeks (opened)',
        'fridge': '1-2 months',
        'freezer': '1-2 years'
    },
    'Chicken, raw': {
        'pantry': 'Not safe',
        'fridge': '1-2 days',
        'freezer': '9 months'
    },
    'Cheese': {
        'pantry': '4-8 hours',
        'fridge': '3-4 weeks (hard), 1 week (soft)',
        'freezer': '6 months'
    },
    'Onion, fresh': {
        'pantry': '1-2 months',
        'fridge': '2-3 months',
        'freezer': 'Not recommended'
    },
    'Apples': {
        'pantry': '1-2 weeks',
        'fridge': '4-6 weeks',
        'freezer': '8 months (sliced)'
    },
    'Bananas': {
        'pantry': '2-7 days',
        'fridge': '5-9 days',
        'freezer': '2-3 months'
    },
    'Potatoes': {
        'pantry': '3-5 weeks',
        'fridge': 'Not recommended',
        'freezer': '10-12 months (cooked)'
    }
}

# Enhanced food items mapping with better keyword coverage
FOOD_ITEMS = {
    # Bread and bakery
    'bread': 'Bread, commercial',
    'brd': 'Bread, commercial',
    
    # Dairy
    'milk': 'Milk (pasteurized)', 
    'eggs': 'Eggs, fresh',
    'egg': 'Eggs, fresh',
    'butter': 'Butter',
    'buttr': 'Butter',
    'cheese': 'Cheese',
    'chse': 'Cheese',
    'cheddar': 'Cheese, cheddar',
    
    # Meat and protein
    'chicken': 'Chicken, raw',
    'chkn': 'Chicken, raw',
    'beef': 'Beef, ground',
    'pork': 'Pork',
    'ham': 'Ham',
    'turkey': 'Turkey',
    
    # Produce
    'onion': 'Onion, fresh',
    'apple': 'Apples',
    'banana': 'Bananas',
    'potato': 'Potatoes',
    'tomato': 'Tomatoes',
    'pepper': 'Green Bell Pepper',
    'lettuce': 'Lettuce',
    'carrot': 'Carrots',
    
    # Pantry items
    'coffee': 'Coffee, ground',
    'folgers': 'Coffee, ground',
    'coffee': 'Coffee, ground',
    'peanut': 'Peanut Butter',
    'pnt': 'Peanut Butter',
    'rice': 'Rice, white',
    'pasta': 'Pasta, dried',
    'flour': 'Flour, all-purpose',
    'sugar': 'Sugar, granulated',
    'salt': 'Salt',
    'oil': 'Oil, vegetable',
    
    # Store brands
    'gv': 'Great Value',  # Walmart brand
    'great value': 'Great Value',
    'marketside': 'Marketside',  # Walmart fresh brand
}

app = FastAPI(title="Enhanced OCR Receipt Service with Shelf Life")

def extract_text(image_bytes: bytes) -> str:
    """Simple OCR using Tesseract"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

def parse_items(text: str) -> List[str]:
    """Extract likely food items from OCR text"""
    items = []
    for line in text.split('\n'):
        line = line.strip().upper()
        if len(line) < 3:
            continue
        # Skip obvious non-food lines
        if any(skip in line for skip in ['TOTAL', 'TAX', 'SUBTOTAL', 'PAYMENT', 'DEBIT', 'CREDIT']):
            continue
        # Remove prices and codes
        line = re.sub(r'\$?\d+\.?\d*', '', line)
        line = re.sub(r'\b\d{8,}\b', '', line)  # Remove long numbers (barcodes)
        line = re.sub(r'\s+', ' ', line).strip()
        
        if len(line) > 2 and any(c.isalpha() for c in line):
            items.append(line)
    return items

def match_food_item(item_text: str) -> tuple[str, dict]:
    """Enhanced keyword matching with multiple attempts and shelf life lookup"""
    item_lower = item_text.lower()
    
    # Direct keyword matching
    for keyword, food_name in FOOD_ITEMS.items():
        if keyword in item_lower:
            shelf_life = SHELF_LIFE_DATA.get(food_name, {
                'pantry': 'Check packaging',
                'fridge': 'Check packaging', 
                'freezer': 'Check packaging'
            })
            return food_name, shelf_life
    
    # Special cases for common abbreviations
    if 'pnt' in item_lower and 'buttr' in item_lower:
        return 'Peanut Butter', SHELF_LIFE_DATA['Peanut Butter']
    
    if 'gv' in item_lower:
        # Great Value brand - try to identify the actual product
        if any(word in item_lower for word in ['pnt', 'buttr']):
            return 'Peanut Butter', SHELF_LIFE_DATA['Peanut Butter']
        elif 'bread' in item_lower or 'brd' in item_lower:
            return 'Bread, commercial', SHELF_LIFE_DATA['Bread, commercial']
        else:
            return 'Great Value Product', {
                'pantry': 'Check packaging',
                'fridge': 'Check packaging',
                'freezer': 'Check packaging'
            }
    
    # Fallback
    return "Unknown food item", {
        'pantry': 'Check packaging',
        'fridge': 'Check packaging',
        'freezer': 'Check packaging'
    }

@app.get("/health")
async def health():
    return {"status": "ok", "message": "Simple OCR service running"}

@app.post("/ocr")
async def extract_receipt_items(file: UploadFile = File(...)):
    """Extract and match items from receipt image with shelf life data"""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file")
    
    content = await file.read()
    
    # Extract text using OCR
    ocr_text = extract_text(content)
    
    # Parse items from text
    raw_items = parse_items(ocr_text)
    
    # Match to food items with shelf life
    results = []
    for item in raw_items:
        matched_food, shelf_life = match_food_item(item)
        results.append({
            "original_text": item,
            "matched_food": matched_food,
            "shelf_life": shelf_life
        })
    
    return {
        "raw_ocr_text": ocr_text,
        "extracted_items": results,
        "item_count": len(results)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
