import logging
import pytesseract
from PIL import Image
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import io
import json
from datetime import datetime

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
    
    # Produce (truncated for space)
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
    'Onion, fresh': {
        'pantry': '1 month (dry), 1-2 weeks (green)',
        'fridge': '2 months (dry), 1-2 weeks (green)',
        'freezer': '10-12 months'
    },
    'Potatoes': {
        'pantry': '1-2 months',
        'fridge': '1-2 weeks',
        'freezer': '10-12 months (cooked and mashed)'
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
    'margarine': 'Butter',
    
    # Produce
    'bananas': 'Bananas',
    'banana': 'Bananas',
    'apples': 'Apples',
    'apple': 'Apples',
    'onions': 'Onion, fresh',
    'onion': 'Onion, fresh',
    'potatoes': 'Potatoes',
    'potato': 'Potatoes'
}

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

# Pydantic models for API responses
class ShelfLifeInfo(BaseModel):
    pantry: str
    fridge: str
    freezer: str

class ProcessedItem(BaseModel):
    id: str
    raw_text: str
    food_name: str
    confidence: str  # 'high', 'medium', 'low'
    shelf_life: ShelfLifeInfo
    category: Optional[str] = None

class ReceiptProcessResponse(BaseModel):
    success: bool
    timestamp: str
    items_found: int
    items: List[ProcessedItem]
    raw_text_preview: str
    processing_info: dict

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str

class FoodDatabaseItem(BaseModel):
    name: str
    shelf_life: ShelfLifeInfo
    aliases: List[str]
    category: str

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Grocery Receipt OCR & Shelf Life API",
    description="Advanced OCR service for grocery receipts with USDA-based shelf life information",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def categorize_food_item(food_name: str) -> str:
    """Categorize food items for better organization"""
    categories = {
        'Dairy & Eggs': ['Eggs', 'Milk', 'Butter', 'Cheese', 'Yogurt', 'Cream cheese', 'Cottage cheese', 'Sour cream'],
        'Bakery': ['Bread', 'Rolls', 'Cookies', 'Muffins', 'Crackers'],
        'Pantry Staples': ['Peanut Butter', 'Coffee', 'Flour', 'Sugar', 'Rice', 'Pasta', 'Beans'],
        'Meat & Poultry': ['Chicken', 'Beef', 'Pork', 'Ground meat', 'Bacon', 'Ham', 'Hot dogs', 'Lunch meat'],
        'Seafood': ['Fish', 'Shrimp', 'Crab'],
        'Produce': ['Apples', 'Bananas', 'Berries', 'Citrus', 'Grapes', 'Melons', 'Onion', 'Potatoes', 'Carrots', 'Tomatoes', 'Broccoli', 'Cauliflower', 'Cabbage', 'Garlic', 'Mushrooms'],
        'Condiments & Sauces': ['Ketchup', 'Mayonnaise', 'Mustard', 'Salad dressing', 'Soy sauce', 'Honey', 'Vinegar'],
        'Canned Goods': ['Canned meat', 'Canned fruit', 'Canned vegetables']
    }
    
    for category, items in categories.items():
        if any(item in food_name for item in items):
            return category
    return 'Other'

def determine_confidence(raw_text: str, food_name: str) -> str:
    """Determine confidence level of the match"""
    raw_lower = raw_text.lower()
    
    # High confidence: direct brand or clear food name match
    high_confidence_indicators = ['folgers', 'eggs', 'bread', 'milk']
    if any(indicator in raw_lower for indicator in high_confidence_indicators):
        return 'high'
    
    # Medium confidence: abbreviated or store brand
    if 'gv' in raw_lower and any(word in raw_lower for word in ['pnt', 'buttr']):
        return 'high'  # Our enhanced matching for GV PNT BUTTR
    
    # Low confidence: partial match or generic fallback
    if food_name == raw_text:  # No transformation occurred
        return 'low'
    
    return 'medium'

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with detailed service information"""
    return HealthResponse(
        status="healthy",
        service="Grocery Receipt OCR & Shelf Life API",
        version="2.1.0",
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check_v1():
    """Versioned health check endpoint"""
    return await health_check()

@app.post("/api/v1/receipt/process", response_model=ReceiptProcessResponse)
async def process_receipt(file: UploadFile = File(...)):
    """
    Process grocery receipt image and return identified items with shelf life information.
    
    This is the main endpoint for receipt processing with comprehensive error handling
    and detailed response structure for frontend integration.
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": "Invalid file type", "message": "Please upload an image file (JPG, PNG, etc.)"}
            )
        
        logger.info(f"Processing receipt: {file.filename}, type: {file.content_type}")
        
        # Read and process image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"Image processed: {image.size} pixels, mode: {image.mode}")
        
        # Perform OCR with enhanced settings
        custom_config = r'--oem 3 --psm 6 -c tesseract_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,/$%- '
        raw_text = pytesseract.image_to_string(image, config=custom_config)
        
        logger.info(f"OCR completed: {len(raw_text)} characters extracted")
        
        # Process text into lines and extract food items
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        processed_items = []
        
        # Skip patterns for non-food items
        skip_patterns = [
            'total', 'subtotal', 'tax', 'walmart', 'store', 'thank you', 
            'receipt', 'cashier', 'card', 'cash', 'change', 'balance',
            'member', 'save', 'tc#', 'st#', 'op#', 'te#', 'debit', 'credit',
            'account', 'network', 'ref #', 'appr code', 'eft', 'payment',
            'manager', 'phone', 'address', 'layaway', 'electronics'
        ]
        
        item_id_counter = 1
        
        for line in lines:
            # Skip non-food lines
            if any(skip_word in line.lower() for skip_word in skip_patterns):
                continue
            
            # Skip very short lines, pure numbers, or obvious non-food items
            if len(line) < 3 or line.replace(' ', '').replace('.', '').replace('-', '').replace('/', '').isdigit():
                continue
            
            # Try to match food items
            food_name, shelf_life = match_food_item(line)
            
            # Only add items with meaningful shelf life data
            if shelf_life and shelf_life != {} and not all(v == "Check packaging" for v in shelf_life.values() if v != "Follow use-by date" and v != "Generally 3-6 months"):
                confidence = determine_confidence(line, food_name)
                category = categorize_food_item(food_name)
                
                processed_item = ProcessedItem(
                    id=f"item_{item_id_counter:03d}",
                    raw_text=line,
                    food_name=food_name,
                    confidence=confidence,
                    shelf_life=ShelfLifeInfo(**shelf_life),
                    category=category
                )
                
                processed_items.append(processed_item)
                logger.info(f"Processed item {item_id_counter}: '{line}' -> '{food_name}' ({confidence} confidence)")
                item_id_counter += 1
        
        # Deduplicate similar items (same food_name)
        unique_items = {}
        for item in processed_items:
            key = item.food_name
            if key not in unique_items or item.confidence == 'high':
                unique_items[key] = item
        
        final_items = list(unique_items.values())
        
        logger.info(f"Final processing result: {len(final_items)} unique food items identified")
        
        return ReceiptProcessResponse(
            success=True,
            timestamp=datetime.now().isoformat(),
            items_found=len(final_items),
            items=final_items,
            raw_text_preview=raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
            processing_info={
                "ocr_engine": "Tesseract",
                "total_lines_processed": len(lines),
                "raw_items_found": len(processed_items),
                "unique_items_found": len(final_items),
                "image_size": f"{image.size[0]}x{image.size[1]}",
                "image_mode": image.mode
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing receipt: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": "Processing failed",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/v1/food-database", response_model=List[FoodDatabaseItem])
async def get_food_database():
    """
    Get the complete food database with shelf life information.
    Useful for frontend autocomplete, validation, or displaying available foods.
    """
    try:
        # Build reverse mapping from food names to aliases
        food_to_aliases = {}
        for alias, food_name in FOOD_ITEMS.items():
            if food_name not in food_to_aliases:
                food_to_aliases[food_name] = []
            food_to_aliases[food_name].append(alias)
        
        database_items = []
        for food_name, shelf_life in SHELF_LIFE_DATA.items():
            aliases = food_to_aliases.get(food_name, [])
            category = categorize_food_item(food_name)
            
            database_item = FoodDatabaseItem(
                name=food_name,
                shelf_life=ShelfLifeInfo(**shelf_life),
                aliases=aliases,
                category=category
            )
            database_items.append(database_item)
        
        return database_items
        
    except Exception as e:
        logger.error(f"Error retrieving food database: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve food database"
        )

@app.get("/api/v1/food-database/{food_name}", response_model=FoodDatabaseItem)
async def get_food_item(food_name: str):
    """
    Get shelf life information for a specific food item.
    Useful for individual lookups or validation.
    """
    try:
        if food_name not in SHELF_LIFE_DATA:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Food item '{food_name}' not found in database"
            )
        
        shelf_life = SHELF_LIFE_DATA[food_name]
        aliases = [alias for alias, name in FOOD_ITEMS.items() if name == food_name]
        category = categorize_food_item(food_name)
        
        return FoodDatabaseItem(
            name=food_name,
            shelf_life=ShelfLifeInfo(**shelf_life),
            aliases=aliases,
            category=category
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving food item {food_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve food item"
        )

@app.get("/api/v1/categories")
async def get_food_categories():
    """
    Get all available food categories.
    Useful for frontend filtering and organization.
    """
    try:
        categories = set()
        for food_name in SHELF_LIFE_DATA.keys():
            category = categorize_food_item(food_name)
            categories.add(category)
        
        return {
            "categories": sorted(list(categories)),
            "total_count": len(categories)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve categories"
        )

# Legacy endpoint for backwards compatibility
@app.post("/ocr", response_model=ReceiptProcessResponse)
async def process_receipt_legacy(file: UploadFile = File(...)):
    """Legacy OCR endpoint - redirects to new API"""
    return await process_receipt(file)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
