"""
LLM-Enhanced FastAPI service for intelligent grocery receipt processing.
Integrates OpenAI GPT or local LLM for smarter item extraction and categorization.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
from PIL import Image
import io
import json
import os

from app.services.llm_ocr_service import process_receipt_with_llm

# Enhanced Pydantic models
class ProcessedItem(BaseModel):
    raw_text: str
    normalized_name: str
    confidence: float
    category: str
    price: Optional[float] = None
    brand: Optional[str] = None
    is_food_item: bool = True
    shelf_life: Optional[Dict[str, Any]] = None

class ReceiptProcessResponse(BaseModel):
    success: bool
    total_items: int
    items: List[ProcessedItem]
    parsing_method: str
    message: str
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    features: List[str]
    llm_status: str

# Initialize FastAPI app
app = FastAPI(
    title="LLM-Enhanced Grocery Receipt OCR API",
    description="AI-powered grocery receipt processing with intelligent item extraction using Large Language Models",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check with LLM status"""
    
    # Check LLM availability
    llm_status = "disabled"
    if os.getenv('OPENAI_API_KEY'):
        llm_status = "openai_available"
    else:
        try:
            from transformers import pipeline
            llm_status = "local_model_available"
        except ImportError:
            llm_status = "rule_based_only"
    
    features = [
        "OCR with Tesseract",
        "USDA FoodKeeper Database",
        "Store Brand Recognition",
        "Intelligent Text Filtering",
        "Confidence Scoring",
        "Price Extraction",
        "Category Classification"
    ]
    
    if llm_status != "rule_based_only":
        features.append("LLM-Enhanced Parsing")
    
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        features=features,
        llm_status=llm_status
    )

@app.post("/api/v1/receipt/process", response_model=ReceiptProcessResponse)
async def process_receipt(file: UploadFile = File(...)):
    """
    Process a grocery receipt image with LLM-enhanced intelligent parsing.
    
    This endpoint uses advanced AI to:
    - Extract text from receipt images using OCR
    - Intelligently identify actual food items vs. receipt metadata
    - Normalize product names and extract pricing
    - Categorize items and provide shelf life information
    - Filter out false positives like store addresses, payment info, etc.
    """
    
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        logger.info(f"Processing receipt: {file.filename}, type: {file.content_type}")
        
        # Read and process image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        logger.info(f"Image processed: {image.size} pixels, mode: {image.mode}")
        
        # Process with LLM-enhanced service
        result = process_receipt_with_llm(image)
        
        if result['success']:
            logger.info(f"Successfully processed {result['total_items']} items using {result['parsing_method']}")
            return ReceiptProcessResponse(**result)
        else:
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=result.get('message', 'Processing failed'))
            
    except Exception as e:
        logger.error(f"Receipt processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process receipt: {str(e)}")

@app.get("/api/v1/food-database")
async def get_food_database():
    """Get the complete USDA FoodKeeper database"""
    try:
        with open('/app/data/enhanced_food_database.json', 'r') as f:
            database = json.load(f)
        return {
            "success": True,
            "total_items": len(database),
            "items": database
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load food database: {str(e)}")

@app.get("/api/v1/food-database/{item_name}")
async def get_food_item(item_name: str):
    """Get specific food item information"""
    try:
        with open('/app/data/enhanced_food_database.json', 'r') as f:
            database = json.load(f)
        
        # Search for item
        for item in database:
            if item_name.lower() in item['name'].lower() or item['name'].lower() in item_name.lower():
                return {
                    "success": True,
                    "item": item
                }
        
        return {
            "success": False,
            "message": f"Food item '{item_name}' not found in database"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search food database: {str(e)}")

@app.get("/api/v1/categories")
async def get_categories():
    """Get available food categories"""
    categories = [
        "Bakery",
        "Dairy", 
        "Meat & Seafood",
        "Produce",
        "Frozen",
        "Beverages",
        "Pantry",
        "Grocery"
    ]
    
    return {
        "success": True,
        "categories": categories
    }

@app.get("/api/v1/parsing-methods")
async def get_parsing_methods():
    """Get available parsing methods and their status"""
    methods = {
        "openai": {
            "available": bool(os.getenv('OPENAI_API_KEY')),
            "description": "OpenAI GPT-powered intelligent parsing",
            "accuracy": "Highest",
            "cost": "Per API call"
        },
        "local_llm": {
            "available": False,  # Would need proper setup
            "description": "Local transformer model parsing", 
            "accuracy": "Medium-High",
            "cost": "Free (compute intensive)"
        },
        "rule_based": {
            "available": True,
            "description": "Enhanced rule-based parsing with intelligent filtering",
            "accuracy": "Medium",
            "cost": "Free"
        }
    }
    
    # Check transformers availability
    try:
        from transformers import pipeline
        methods["local_llm"]["available"] = True
    except ImportError:
        pass
    
    return {
        "success": True,
        "methods": methods
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
