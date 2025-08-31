"""
Enhanced LLM-powered OCR service for intelligent grocery receipt processing.
Uses OpenAI GPT or local LLM to intelligently parse and categorize receipt items.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from PIL import Image
import pytesseract
import json
import re
from dataclasses import dataclass

# Optional LLM integrations
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

@dataclass
class ExtractedItem:
    """Structured representation of an extracted grocery item"""
    raw_text: str
    normalized_name: str
    confidence: float
    category: str
    price: Optional[float] = None
    quantity: Optional[str] = None
    brand: Optional[str] = None
    is_food_item: bool = True

class LLMReceiptParser:
    """LLM-powered receipt parser for intelligent item extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_llm()
        
        # Load USDA food database
        with open('/app/data/enhanced_food_database.json', 'r') as f:
            self.food_database = json.load(f)
            
        # Common receipt patterns to ignore
        self.ignore_patterns = [
            r'^\d{4,}$',  # Long numbers (SKUs, barcodes)
            r'ST#|OP#|TE#|TR#',  # Store transaction codes
            r'^\d{1,2}/\d{1,2}/\d{2,4}',  # Dates
            r'^\d{1,2}:\d{2}',  # Times
            r'MANAGER|CASHIER',  # Staff info
            r'^\d+\s+[A-Z]\s+\w+\s+AVE|ST|BLVD|RD',  # Addresses
            r'DEBIT|CREDIT|CASH|TEND',  # Payment methods
            r'SUBTOTAL|TOTAL|TAX',  # Transaction totals
            r'REF\s*#|APPR\s*CODE',  # Reference numbers
            r'THANK\s*YOU|VISIT',  # Thank you messages
        ]
    
    def setup_llm(self):
        """Initialize LLM (OpenAI or local model)"""
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            self.llm_type = 'openai'
            openai.api_key = os.getenv('OPENAI_API_KEY')
            self.logger.info("Using OpenAI GPT for intelligent parsing")
        elif TRANSFORMERS_AVAILABLE:
            self.llm_type = 'local'
            # Use a smaller, efficient model for local inference
            model_name = "microsoft/DialoGPT-small"  # Lightweight option
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            self.logger.info("Using local transformer model for parsing")
        else:
            self.llm_type = 'rule_based'
            self.logger.warning("No LLM available, falling back to rule-based parsing")
    
    def extract_receipt_items(self, image: Image.Image) -> List[ExtractedItem]:
        """Extract and intelligently parse items from receipt image"""
        # Step 1: OCR extraction
        ocr_text = pytesseract.image_to_string(image)
        self.logger.info(f"OCR extracted {len(ocr_text)} characters")
        
        # Step 2: Pre-process and filter lines
        lines = self.preprocess_ocr_text(ocr_text)
        
        # Step 3: LLM-powered intelligent parsing
        if self.llm_type == 'openai':
            items = self.parse_with_openai(lines)
        elif self.llm_type == 'local':
            items = self.parse_with_local_llm(lines)
        else:
            items = self.parse_with_rules(lines)
        
        # Step 4: Enrich with shelf life data
        enriched_items = self.enrich_with_shelf_life(items)
        
        return enriched_items
    
    def preprocess_ocr_text(self, text: str) -> List[str]:
        """Clean and filter OCR text to relevant lines"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Filter out obvious non-food lines
        filtered_lines = []
        for line in lines:
            # Skip if matches ignore patterns
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.ignore_patterns):
                continue
            
            # Skip very short lines (likely fragments)
            if len(line) < 3:
                continue
                
            # Skip lines with only numbers/special chars
            if re.match(r'^[\d\s\-\.\$\(\)]+$', line):
                continue
                
            filtered_lines.append(line)
        
        self.logger.info(f"Filtered to {len(filtered_lines)} relevant lines from {len(lines)} total")
        return filtered_lines
    
    def parse_with_openai(self, lines: List[str]) -> List[ExtractedItem]:
        """Use OpenAI GPT to intelligently parse receipt lines"""
        prompt = f"""
        Analyze this grocery receipt text and extract only actual food/grocery items.
        Ignore store info, addresses, payment details, staff names, etc.
        
        Receipt lines:
        {chr(10).join(lines)}
        
        For each actual grocery item found, provide:
        - raw_text: exact text from receipt
        - normalized_name: clean product name
        - confidence: 0.0-1.0 how confident this is a food item
        - category: food category (dairy, produce, meat, etc.)
        - price: if extractable from line
        - brand: if identifiable
        
        Return as JSON array. Only include actual grocery products, not store metadata.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return [ExtractedItem(**item) for item in result]
            
        except Exception as e:
            self.logger.error(f"OpenAI parsing failed: {e}")
            return self.parse_with_rules(lines)
    
    def parse_with_local_llm(self, lines: List[str]) -> List[ExtractedItem]:
        """Use local transformer model for parsing"""
        # For now, implement rule-based with local LLM enhancement
        # This would need a more sophisticated local model setup
        return self.parse_with_rules(lines)
    
    def parse_with_rules(self, lines: List[str]) -> List[ExtractedItem]:
        """Enhanced rule-based parsing with better filtering"""
        items = []
        
        for line in lines:
            # Look for patterns that indicate food items
            item = self.extract_item_from_line(line)
            if item and item.is_food_item:
                items.append(item)
        
        # Deduplicate similar items
        items = self.deduplicate_items(items)
        
        self.logger.info(f"Extracted {len(items)} food items using rule-based parsing")
        return items
    
    def extract_item_from_line(self, line: str) -> Optional[ExtractedItem]:
        """Extract item details from a single receipt line"""
        # Common grocery item patterns
        food_keywords = [
            'BREAD', 'MILK', 'EGGS', 'BUTTER', 'CHEESE', 'MEAT', 'CHICKEN', 'BEEF',
            'PORK', 'FISH', 'FRUIT', 'BANANA', 'APPLE', 'ORANGE', 'VEGETABLE',
            'TOMATO', 'ONION', 'POTATO', 'RICE', 'PASTA', 'CEREAL', 'COFFEE',
            'TEA', 'JUICE', 'SODA', 'YOGURT', 'CREAM', 'BAGEL', 'MUFFIN',
            'PIZZA', 'SANDWICH', 'SOUP', 'SAUCE', 'OIL', 'SUGAR', 'FLOUR',
            'SALT', 'PEPPER', 'SPICE', 'CONDIMENT', 'PEANUT', 'NUT', 'COOKIE',
            'CAKE', 'ICE CREAM', 'FROZEN', 'CANNED', 'ORGANIC', 'FRESH'
        ]
        
        # Extract price if present
        price_match = re.search(r'(\d+\.\d{2})', line)
        price = float(price_match.group(1)) if price_match else None
        
        # Check for food keywords
        line_upper = line.upper()
        food_score = sum(1 for keyword in food_keywords if keyword in line_upper)
        
        # Store brand recognition
        brand = None
        if 'GV ' in line_upper:
            brand = 'Great Value'
        elif 'KROGER' in line_upper:
            brand = 'Kroger'
        elif 'FOLGERS' in line_upper:
            brand = 'Folgers'
        
        # Determine if this looks like a food item
        is_food = food_score > 0 or any(pattern in line_upper for pattern in [
            'GV ', 'ORGANIC', 'FRESH', 'FROZEN', 'CANNED'
        ])
        
        if not is_food:
            return None
        
        # Normalize the name
        normalized = self.normalize_product_name(line)
        
        # Estimate confidence
        confidence = min(0.9, 0.3 + (food_score * 0.2))
        if brand:
            confidence += 0.1
        if price:
            confidence += 0.1
        
        return ExtractedItem(
            raw_text=line,
            normalized_name=normalized,
            confidence=confidence,
            category=self.categorize_item(normalized),
            price=price,
            brand=brand,
            is_food_item=True
        )
    
    def normalize_product_name(self, raw_text: str) -> str:
        """Clean and normalize product names"""
        # Remove SKU/barcode numbers
        text = re.sub(r'\d{10,}', '', raw_text)
        
        # Remove transaction codes
        text = re.sub(r'[FNX]\s*\d+\.\d{2}', '', text)
        text = re.sub(r'ST#.*|OP#.*|TE#.*|TR#.*', '', text)
        
        # Clean up common abbreviations
        replacements = {
            'GV ': 'Great Value ',
            'PNT BUTTR': 'Peanut Butter',
            'CHNK CHKN': 'Chunk Chicken',
            'PARM': 'Parmesan',
            'WHL MLK': 'Whole Milk',
            'ORG': 'Organic',
        }
        
        for abbrev, full in replacements.items():
            text = text.replace(abbrev, full)
        
        # Remove extra whitespace and clean
        text = ' '.join(text.split())
        text = text.strip()
        
        return text
    
    def categorize_item(self, item_name: str) -> str:
        """Categorize food items"""
        item_upper = item_name.upper()
        
        if any(word in item_upper for word in ['BREAD', 'BAGEL', 'MUFFIN', 'ROLL']):
            return 'Bakery'
        elif any(word in item_upper for word in ['MILK', 'CHEESE', 'BUTTER', 'YOGURT', 'CREAM']):
            return 'Dairy'
        elif any(word in item_upper for word in ['CHICKEN', 'BEEF', 'PORK', 'FISH', 'MEAT']):
            return 'Meat & Seafood'
        elif any(word in item_upper for word in ['FRUIT', 'VEGETABLE', 'BANANA', 'APPLE', 'TOMATO']):
            return 'Produce'
        elif any(word in item_upper for word in ['FROZEN', 'ICE CREAM']):
            return 'Frozen'
        elif any(word in item_upper for word in ['COFFEE', 'TEA', 'JUICE', 'SODA']):
            return 'Beverages'
        elif any(word in item_upper for word in ['PEANUT', 'NUT', 'BUTTER']):
            return 'Pantry'
        else:
            return 'Grocery'
    
    def deduplicate_items(self, items: List[ExtractedItem]) -> List[ExtractedItem]:
        """Remove duplicate items based on normalized names"""
        seen = {}
        unique_items = []
        
        for item in items:
            key = item.normalized_name.lower()
            if key not in seen or item.confidence > seen[key].confidence:
                seen[key] = item
        
        return list(seen.values())
    
    def enrich_with_shelf_life(self, items: List[ExtractedItem]) -> List[ExtractedItem]:
        """Add shelf life information from USDA database"""
        for item in items:
            # Try to match with food database
            best_match = self.find_best_food_match(item.normalized_name)
            if best_match:
                item.shelf_life_data = best_match
        
        return items
    
    def find_best_food_match(self, item_name: str) -> Optional[Dict[str, Any]]:
        """Find best matching food item in USDA database"""
        item_lower = item_name.lower()
        
        # Direct name matches first
        for food_item in self.food_database:
            if food_item['name'].lower() in item_lower or item_lower in food_item['name'].lower():
                return food_item
        
        # Keyword matching
        best_score = 0
        best_match = None
        
        for food_item in self.food_database:
            food_keywords = food_item['name'].lower().split()
            item_keywords = item_lower.split()
            
            score = len(set(food_keywords) & set(item_keywords))
            if score > best_score:
                best_score = score
                best_match = food_item
        
        return best_match if best_score > 0 else None

# Enhanced API endpoint function
def process_receipt_with_llm(image: Image.Image) -> Dict[str, Any]:
    """Process receipt with LLM-enhanced parsing"""
    parser = LLMReceiptParser()
    
    try:
        items = parser.extract_receipt_items(image)
        
        # Convert to API response format
        processed_items = []
        for item in items:
            processed_item = {
                "raw_text": item.raw_text,
                "normalized_name": item.normalized_name,
                "confidence": item.confidence,
                "category": item.category,
                "price": item.price,
                "brand": item.brand,
                "is_food_item": item.is_food_item
            }
            
            if hasattr(item, 'shelf_life_data') and item.shelf_life_data:
                processed_item["shelf_life"] = item.shelf_life_data
            
            processed_items.append(processed_item)
        
        return {
            "success": True,
            "total_items": len(processed_items),
            "items": processed_items,
            "parsing_method": parser.llm_type,
            "message": f"Successfully extracted {len(processed_items)} grocery items"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to process receipt"
        }
