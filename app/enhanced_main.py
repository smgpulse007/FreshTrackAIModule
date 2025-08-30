import logging
import pytesseract
from PIL import Image
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List

# Enhanced shelf life database based on USDA FoodKeeper data
SHELF_LIFE_DATA = {
    # Bakery items
    'Bread, commercial': {
        'pantry': '14-18 days',
        'fridge': '2-3 weeks',
        'freezer': '3-5 months'
    },
    'Bread, flat (tortillas, pita)': {
        'pantry': '14-18 days',
        'fridge': '2-3 weeks',
        'freezer': '3-5 months'
    },
    'Rolls, yeast': {
        'pantry': '14-18 days',
        'fridge': '2-3 weeks',
        'freezer': '3-5 months'
    },
    'Cookies, bakery': {
        'pantry': '2-3 weeks',
        'fridge': '2-3 months',
        'freezer': '8-12 months'
    },
    'Muffins': {
        'pantry': '3-7 days',
        'fridge': '7-10 days',
        'freezer': '6 months'
    },
    'Crackers': {
        'pantry': '8 months',
        'fridge': '3-4 months',
        'freezer': '3-4 months'
    },
    
    # Dairy & Eggs
    'Eggs, fresh': {
        'pantry': 'Not safe',
        'fridge': '3-5 weeks',
        'freezer': 'Do not freeze (shells)'
    },
    'Eggs, raw': {
        'pantry': 'Not safe',
        'fridge': '3-5 weeks',
        'freezer': 'Do not freeze (shells)'
    },
    'Butter': {
        'pantry': 'Not recommended',
        'fridge': '1-2 months',
        'freezer': '6-9 months'
    },
    'Milk': {
        'pantry': 'Not safe',
        'fridge': '1 week',
        'freezer': '3 months'
    },
    'Cheese, hard': {
        'pantry': 'Not safe',
        'fridge': '6 months unopened, 3-4 weeks opened',
        'freezer': '6 months'
    },
    'Cheese': {
        'pantry': 'Not safe',
        'fridge': '3-4 weeks (hard), 1-2 weeks (soft)',
        'freezer': '6 months'
    },
    'Cottage cheese': {
        'pantry': 'Not safe',
        'fridge': '2 weeks unopened, 1 week opened',
        'freezer': 'Does not freeze well'
    },
    'Cream cheese': {
        'pantry': 'Not safe',
        'fridge': '2 weeks',
        'freezer': 'Does not freeze well'
    },
    'Yogurt': {
        'pantry': 'Not safe',
        'fridge': '1-2 weeks',
        'freezer': '1-2 months'
    },
    'Sour cream': {
        'pantry': 'Not safe',
        'fridge': '7-21 days',
        'freezer': 'Does not freeze well'
    },
    
    # Pantry staples
    'Peanut Butter': {
        'pantry': '6-24 months',
        'fridge': '2-3 months after opening',
        'freezer': 'Not recommended'
    },
    'Coffee, ground': {
        'pantry': '1 week after opening',
        'fridge': '3-4 months',
        'freezer': '3-4 months'
    },
    'Coffee, whole beans': {
        'pantry': '1-3 weeks',
        'fridge': '2 weeks',
        'freezer': '3-4 months'
    },
    'Flour, white': {
        'pantry': '6-12 months',
        'fridge': '1 year',
        'freezer': '6-8 months'
    },
    'Sugar': {
        'pantry': '18-24 months (never spoils)',
        'fridge': 'Not needed',
        'freezer': 'Not needed'
    },
    'Rice, white': {
        'pantry': '2 years',
        'fridge': '6 months cooked',
        'freezer': '1 year'
    },
    'Pasta, dry': {
        'pantry': '2 years',
        'fridge': '1 year after opening',
        'freezer': 'Not needed'
    },
    'Beans, dried': {
        'pantry': '1 year',
        'fridge': '1 year after opening',
        'freezer': 'Not needed'
    },
    
    # Meat & Poultry
    'Chicken, raw': {
        'pantry': 'Not safe',
        'fridge': '1-2 days',
        'freezer': '1 year (whole), 9 months (parts)'
    },
    'Beef, raw': {
        'pantry': 'Not safe',
        'fridge': '3-5 days',
        'freezer': '6-12 months'
    },
    'Pork, raw': {
        'pantry': 'Not safe',
        'fridge': '3-5 days',
        'freezer': '6-12 months'
    },
    'Ground meat': {
        'pantry': 'Not safe',
        'fridge': '1-2 days',
        'freezer': '3-4 months'
    },
    'Bacon': {
        'pantry': 'Not safe',
        'fridge': '1 week',
        'freezer': '1 month'
    },
    'Ham, fully cooked': {
        'pantry': 'Not safe',
        'fridge': '1 week (whole), 3-5 days (slices)',
        'freezer': '1-2 months'
    },
    'Hot dogs': {
        'pantry': 'Not safe',
        'fridge': '2 weeks sealed, 1 week opened',
        'freezer': '1-2 months'
    },
    'Lunch meat': {
        'pantry': 'Not safe',
        'fridge': '2 weeks sealed, 3-5 days opened',
        'freezer': '1-2 months'
    },
    
    # Fish & Seafood
    'Fish, lean': {
        'pantry': 'Not safe',
        'fridge': '1-2 days',
        'freezer': '6-8 months'
    },
    'Fish, fatty': {
        'pantry': 'Not safe',
        'fridge': '1-2 days',
        'freezer': '2-3 months'
    },
    'Shrimp': {
        'pantry': 'Not safe',
        'fridge': '1-3 days',
        'freezer': '6-18 months'
    },
    'Crab': {
        'pantry': 'Not safe',
        'fridge': '1-3 days fresh, 3-5 days pasteurized',
        'freezer': '2-4 months'
    },
    
    # Fruits
    'Apples': {
        'pantry': '3 weeks',
        'fridge': '4-6 weeks',
        'freezer': '8 months (cooked)'
    },
    'Bananas': {
        'pantry': 'Until ripe',
        'fridge': '3 days (skin will blacken)',
        'freezer': '2-3 months (whole peeled)'
    },
    'Berries': {
        'pantry': 'Use quickly',
        'fridge': '7 days',
        'freezer': '1 year'
    },
    'Citrus fruit': {
        'pantry': '10 days',
        'fridge': '1-2 weeks',
        'freezer': 'Do not freeze'
    },
    'Grapes': {
        'pantry': '1 day',
        'fridge': '1 week',
        'freezer': '1 month (whole)'
    },
    'Melons': {
        'pantry': 'Until ripe',
        'fridge': '2 weeks whole, 2-4 days cut',
        'freezer': '1 month (balls)'
    },
    
    # Vegetables
    'Onion, fresh': {
        'pantry': '1 month (dry), 1-2 weeks (green)',
        'fridge': '2 months (dry), 1-2 weeks (green)',
        'freezer': '10-12 months'
    },
    'Potatoes': {
        'pantry': '1-2 months',
        'fridge': '1-2 weeks',
        'freezer': '10-12 months (cooked and mashed)'
    },
    'Carrots': {
        'pantry': '1 day',
        'fridge': '2-3 weeks',
        'freezer': '10-12 months'
    },
    'Celery': {
        'pantry': 'Not recommended',
        'fridge': '1-2 weeks',
        'freezer': '10-12 months'
    },
    'Lettuce': {
        'pantry': 'Not recommended',
        'fridge': '1-2 weeks (iceberg), 3-7 days (leaf)',
        'freezer': 'Do not freeze'
    },
    'Tomatoes': {
        'pantry': 'Until ripe',
        'fridge': '2-3 days',
        'freezer': '2 months'
    },
    'Broccoli': {
        'pantry': 'Not recommended',
        'fridge': '3-5 days',
        'freezer': '10-12 months'
    },
    'Cauliflower': {
        'pantry': 'Not recommended',
        'fridge': '3-5 days',
        'freezer': '10-12 months'
    },
    'Cabbage': {
        'pantry': 'Not recommended',
        'fridge': '1-2 weeks',
        'freezer': '10-12 months'
    },
    'Garlic': {
        'pantry': '1 month',
        'fridge': '1-2 weeks',
        'freezer': '1 month'
    },
    'Mushrooms': {
        'pantry': 'Not recommended',
        'fridge': '3-7 days',
        'freezer': '10-12 months'
    },
    
    # Condiments & Sauces
    'Ketchup': {
        'pantry': '1 year unopened',
        'fridge': '6 months after opening',
        'freezer': 'Not recommended'
    },
    'Mayonnaise': {
        'pantry': '3-6 months unopened',
        'fridge': '2 months after opening',
        'freezer': 'Do not freeze'
    },
    'Mustard': {
        'pantry': '1-2 years unopened',
        'fridge': '1 year after opening',
        'freezer': 'Not recommended'
    },
    'Salad dressing': {
        'pantry': '10-12 months unopened',
        'fridge': '1-3 months after opening',
        'freezer': 'Not recommended'
    },
    'Soy sauce': {
        'pantry': '2-3 years unopened',
        'fridge': '1 year after opening',
        'freezer': 'Not recommended'
    },
    'Honey': {
        'pantry': '2 years (never spoils)',
        'fridge': 'Not needed',
        'freezer': 'Not needed'
    },
    'Vinegar': {
        'pantry': '2 years (indefinite)',
        'fridge': 'Not needed',
        'freezer': 'Not needed'
    },
    
    # Canned goods
    'Canned meat': {
        'pantry': '2-5 years unopened',
        'fridge': '3-4 days after opening',
        'freezer': 'Not recommended after opening'
    },
    'Canned fruit': {
        'pantry': '12-18 months unopened',
        'fridge': '5-7 days after opening',
        'freezer': 'Not recommended after opening'
    },
    'Canned vegetables': {
        'pantry': '2-5 years unopened',
        'fridge': '3-4 days after opening',
        'freezer': 'Not recommended after opening'
    }
}

# Enhanced food item mappings with store brands and variations
FOOD_ITEMS = {
    # Bread variations
    'bread': 'Bread, commercial',
    'brd': 'Bread, commercial',
    'loaf': 'Bread, commercial',
    'white bread': 'Bread, commercial',
    'wheat bread': 'Bread, commercial',
    'whole wheat': 'Bread, commercial',
    'sourdough': 'Bread, commercial',
    'gv bread': 'Bread, commercial',  # Great Value brand
    'wonder bread': 'Bread, commercial',
    'sara lee': 'Bread, commercial',
    
    # Coffee variations
    'folgers': 'Coffee, ground',
    'coffee': 'Coffee, ground',
    'maxwell house': 'Coffee, ground',
    'starbucks': 'Coffee, ground',
    'gv coffee': 'Coffee, ground',
    'cafe bustelo': 'Coffee, ground',
    'instant coffee': 'Coffee, ground',
    'k-cups': 'Coffee, ground',
    
    # Egg variations
    'eggs': 'Eggs, fresh',
    'egg': 'Eggs, fresh',
    'large eggs': 'Eggs, fresh',
    'dozen eggs': 'Eggs, fresh',
    'gv eggs': 'Eggs, fresh',
    'organic eggs': 'Eggs, fresh',
    'free range': 'Eggs, fresh',
    
    # Peanut butter variations - ENHANCED
    'gv pnt buttr': 'Peanut Butter',
    'gv peanut butter': 'Peanut Butter',
    'peanut butter': 'Peanut Butter',
    'pnt butter': 'Peanut Butter',
    'pnt buttr': 'Peanut Butter',
    'jif': 'Peanut Butter',
    'skippy': 'Peanut Butter',
    'peter pan': 'Peanut Butter',
    'simply jif': 'Peanut Butter',
    'natural pb': 'Peanut Butter',
    'organic pb': 'Peanut Butter',
    
    # Milk variations
    'milk': 'Milk',
    'whole milk': 'Milk',
    '2% milk': 'Milk',
    'skim milk': 'Milk',
    '1% milk': 'Milk',
    'gv milk': 'Milk',
    'organic milk': 'Milk',
    'lactaid': 'Milk',
    
    # Butter variations
    'butter': 'Butter',
    'salted butter': 'Butter',
    'unsalted butter': 'Butter',
    'gv butter': 'Butter',
    'land o lakes': 'Butter',
    'kerrygold': 'Butter',
    'margarine': 'Butter',  # Close enough for storage purposes
    
    # Cheese variations
    'cheese': 'Cheese',
    'cheddar': 'Cheese, hard',
    'american cheese': 'Cheese',
    'swiss cheese': 'Cheese, hard',
    'mozzarella': 'Cheese',
    'gv cheese': 'Cheese',
    'kraft': 'Cheese',
    'velveeta': 'Cheese',
    'string cheese': 'Cheese',
    'cream cheese': 'Cream cheese',
    'philadelphia': 'Cream cheese',
    
    # Produce
    'bananas': 'Bananas',
    'banana': 'Bananas',
    'apples': 'Apples',
    'apple': 'Apples',
    'gala apples': 'Apples',
    'red delicious': 'Apples',
    'granny smith': 'Apples',
    'onions': 'Onion, fresh',
    'onion': 'Onion, fresh',
    'yellow onion': 'Onion, fresh',
    'white onion': 'Onion, fresh',
    'red onion': 'Onion, fresh',
    'potatoes': 'Potatoes',
    'potato': 'Potatoes',
    'russet': 'Potatoes',
    'red potatoes': 'Potatoes',
    'carrots': 'Carrots',
    'carrot': 'Carrots',
    'baby carrots': 'Carrots',
    'tomatoes': 'Tomatoes',
    'tomato': 'Tomatoes',
    'roma tomatoes': 'Tomatoes',
    'cherry tomatoes': 'Tomatoes',
    
    # Meat
    'chicken': 'Chicken, raw',
    'chicken breast': 'Chicken, raw',
    'chicken thighs': 'Chicken, raw',
    'ground beef': 'Ground meat',
    'ground turkey': 'Ground meat',
    'beef': 'Beef, raw',
    'pork': 'Pork, raw',
    'bacon': 'Bacon',
    'ham': 'Ham, fully cooked',
    'lunch meat': 'Lunch meat',
    'deli meat': 'Lunch meat',
    'turkey slices': 'Lunch meat',
    'hot dogs': 'Hot dogs',
    'hotdogs': 'Hot dogs',
    'wieners': 'Hot dogs',
    
    # Pantry items
    'rice': 'Rice, white',
    'white rice': 'Rice, white',
    'brown rice': 'Rice, white',  # Similar storage
    'pasta': 'Pasta, dry',
    'spaghetti': 'Pasta, dry',
    'macaroni': 'Pasta, dry',
    'flour': 'Flour, white',
    'all purpose flour': 'Flour, white',
    'sugar': 'Sugar',
    'granulated sugar': 'Sugar',
    'brown sugar': 'Sugar',
    'honey': 'Honey',
    'crackers': 'Crackers',
    'saltines': 'Crackers',
    'ritz': 'Crackers',
    
    # Great Value (GV) brand mappings
    'gv': 'Great Value Brand',  # Generic fallback
    'great value': 'Great Value Brand'
}

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enhanced Grocery OCR & Shelf Life Service", version="2.0")

def match_food_item(ocr_text: str) -> tuple[str, dict]:
    """
    Enhanced matching for food items with better handling of store brands and variations.
    Returns tuple of (food_name, shelf_life_dict)
    """
    text_lower = ocr_text.lower().strip()
    
    # Handle specific Great Value peanut butter case
    if 'gv' in text_lower and any(word in text_lower for word in ['pnt', 'peanut', 'buttr', 'butter']):
        return 'Peanut Butter', SHELF_LIFE_DATA['Peanut Butter']
    
    # Try exact match first
    if text_lower in FOOD_ITEMS:
        food_name = FOOD_ITEMS[text_lower]
        return food_name, SHELF_LIFE_DATA.get(food_name, {})
    
    # Try partial matching for complex items
    for key, food_name in FOOD_ITEMS.items():
        if key in text_lower or any(word in text_lower for word in key.split()):
            return food_name, SHELF_LIFE_DATA.get(food_name, {})
    
    # Fallback to generic shelf life
    generic_shelf_life = {
        'pantry': 'Check packaging',
        'fridge': 'Follow use-by date',
        'freezer': 'Generally 3-6 months'
    }
    return ocr_text, generic_shelf_life

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Enhanced Grocery OCR & Shelf Life Service"}

@app.post("/ocr")
async def process_receipt(file: UploadFile = File(...)):
    """
    Process receipt image and return items with enhanced shelf life information
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        logger.info(f"Processing image: {file.filename}, type: {file.content_type}")
        
        # Read and process image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"Image loaded: {image.size} pixels, mode: {image.mode}")
        
        # Perform OCR with enhanced settings
        custom_config = r'--oem 3 --psm 6 -c tesseract_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,/$%- '
        raw_text = pytesseract.image_to_string(image, config=custom_config)
        
        logger.info(f"Raw OCR text length: {len(raw_text)} characters")
        logger.info(f"Raw OCR text preview: {raw_text[:200]}...")
        
        # Process text into lines and extract potential food items
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        food_items = []
        
        for line in lines:
            # Skip lines that are clearly prices, totals, or store info
            if any(skip_word in line.lower() for skip_word in [
                'total', 'subtotal', 'tax', 'walmart', 'store', 'thank you', 
                'receipt', 'cashier', 'card', 'cash', 'change', 'balance',
                'member', 'save', '$', 'tc#', 'st#', 'op#', 'te#'
            ]):
                continue
            
            # Skip very short lines or lines that are clearly not food items
            if len(line) < 3:
                continue
            
            # Try to match food items
            food_name, shelf_life = match_food_item(line)
            
            # Only add if we have shelf life data (indicating a successful match)
            if shelf_life and shelf_life != {}:
                food_items.append({
                    "raw_text": line,
                    "food_name": food_name,
                    "shelf_life": shelf_life
                })
                logger.info(f"Matched: '{line}' -> '{food_name}'")
        
        logger.info(f"Total matched food items: {len(food_items)}")
        
        return {
            "success": True,
            "items_found": len(food_items),
            "items": food_items,
            "raw_text_preview": raw_text[:500],
            "service_info": "Enhanced OCR with USDA FoodKeeper data"
        }
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Add missing import
import io

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
