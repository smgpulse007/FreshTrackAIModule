# 🚀 Grocery Receipt OCR & Shelf Life API v2.1.0

## 📋 **Production-Ready API for Supabase & Frontend Integration**

### 🌐 **Base URL:** `http://localhost:8004`

---

## 🎯 **API Endpoints Overview**

### 🏥 **Health & Status**

#### `GET /health` or `GET /api/v1/health`
```json
{
  "status": "healthy",
  "service": "Grocery Receipt OCR & Shelf Life API", 
  "version": "2.1.0",
  "timestamp": "2025-08-30T21:22:25.759141"
}
```

---

### 📷 **Receipt Processing**

#### `POST /api/v1/receipt/process`
**Main endpoint for processing grocery receipts**

**Request:** Multipart form data with image file
```bash
curl -F "file=@receipt.jpg" http://localhost:8004/api/v1/receipt/process
```

**Response:** Enhanced structured data
```json
{
  "success": true,
  "timestamp": "2025-08-30T21:22:31.036679",
  "items_found": 5,
  "items": [
    {
      "id": "item_001",
      "raw_text": "BREAD 007225003712 F 2.88 N",
      "food_name": "Bread, commercial",
      "confidence": "high",
      "shelf_life": {
        "pantry": "14-18 days",
        "fridge": "2-3 weeks", 
        "freezer": "3-5 months"
      },
      "category": "Bakery"
    },
    {
      "id": "item_002", 
      "raw_text": "GV PNT BUTTR 007874237003 F 3.84 N",
      "food_name": "Peanut Butter",
      "confidence": "high",
      "shelf_life": {
        "pantry": "6-24 months",
        "fridge": "2-3 months after opening",
        "freezer": "Not recommended"
      },
      "category": "Pantry Staples"
    }
  ],
  "raw_text_preview": "OCR text preview...",
  "processing_info": {
    "ocr_engine": "Tesseract",
    "total_lines_processed": 41,
    "raw_items_found": 13,
    "unique_items_found": 5,
    "image_size": "600x1343",
    "image_mode": "RGB"
  }
}
```

---

### 🗄️ **Food Database**

#### `GET /api/v1/food-database`
**Get complete food database with shelf life information**

**Response:** Array of all food items
```json
[
  {
    "name": "Bread, commercial",
    "shelf_life": {
      "pantry": "14-18 days",
      "fridge": "2-3 weeks",
      "freezer": "3-5 months"
    },
    "aliases": ["bread", "brd", "loaf", "white bread", "gv bread"],
    "category": "Bakery"
  }
]
```

#### `GET /api/v1/food-database/{food_name}`
**Get specific food item information**

**Example:** `/api/v1/food-database/Peanut%20Butter`
```json
{
  "name": "Peanut Butter",
  "shelf_life": {
    "pantry": "6-24 months",
    "fridge": "2-3 months after opening", 
    "freezer": "Not recommended"
  },
  "aliases": ["gv pnt buttr", "jif", "skippy", "peanut butter"],
  "category": "Pantry Staples"
}
```

#### `GET /api/v1/categories`
**Get all available food categories**

```json
{
  "categories": [
    "Bakery",
    "Dairy & Eggs", 
    "Meat & Poultry",
    "Pantry Staples",
    "Produce"
  ],
  "total_count": 5
}
```

---

## 🔧 **Technical Features**

### ✅ **Production Ready Features:**
- **CORS enabled** for frontend integration
- **Comprehensive error handling** with proper HTTP status codes
- **Pydantic models** for request/response validation
- **Structured logging** for monitoring
- **Detailed API documentation** at `/docs`
- **Unique item IDs** for frontend tracking
- **Confidence scoring** for match quality
- **Category classification** for organization
- **Deduplication** removes duplicate items
- **Enhanced filtering** removes non-food items

### 🛡️ **Error Handling:**
- `400 Bad Request` - Invalid file format
- `404 Not Found` - Food item not in database  
- `500 Internal Server Error` - Processing failures

### 📊 **Data Quality:**
- **USDA FoodKeeper database** - Official government data
- **80+ food items** with comprehensive shelf life info
- **Store brand recognition** (Great Value, etc.)
- **Smart deduplication** prevents duplicate entries
- **Confidence scoring** helps prioritize results

---

## 🔗 **Integration with Supabase**

### **Recommended Supabase Table Structure:**

```sql
-- Receipt processing records
CREATE TABLE receipt_scans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id),
  image_url TEXT,
  processing_timestamp TIMESTAMPTZ,
  items_found INTEGER,
  raw_ocr_text TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Individual food items from receipts
CREATE TABLE receipt_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  receipt_scan_id UUID REFERENCES receipt_scans(id),
  item_id TEXT, -- From API response
  raw_text TEXT,
  food_name TEXT,
  confidence TEXT,
  category TEXT,
  pantry_life TEXT,
  fridge_life TEXT,
  freezer_life TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🎨 **Frontend Integration Examples**

### **React/Next.js Example:**
```javascript
// Upload receipt
const uploadReceipt = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8004/api/v1/receipt/process', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  return result;
};

// Get food database
const getFoodDatabase = async () => {
  const response = await fetch('http://localhost:8004/api/v1/food-database');
  return await response.json();
};
```

---

## 🚀 **Deployment Ports**

- **Port 8000:** Simple service (legacy)
- **Port 8003:** Enhanced service (testing)
- **Port 8004:** **Production API** (recommended for integration)

---

## 📈 **Current Test Results**

✅ **Successfully Processes Walmart Receipt:**
- **BREAD** → Bread, commercial (high confidence)
- **GV PNT BUTTR** → Peanut Butter (high confidence) 
- **FOLGERS** → Coffee, ground (high confidence)
- **EGGS** → Eggs, fresh (high confidence)

**Processing Speed:** ~2-3 seconds per receipt
**Accuracy:** High confidence matches for major grocery items
**False Positives:** Filtered out (store info, payment details, etc.)

---

## 🔍 **API Documentation**

Full interactive documentation available at:
- **Swagger UI:** `http://localhost:8004/docs`
- **ReDoc:** `http://localhost:8004/redoc`
- **OpenAPI JSON:** `http://localhost:8004/openapi.json`

---

## 🎯 **Perfect for Frontend Integration!**

This API is now **production-ready** for integration with:
- **React/Next.js frontends**
- **Supabase databases** 
- **Mobile applications**
- **Third-party services**

The structured response format, comprehensive error handling, and detailed documentation make it ideal for building robust grocery management applications! 🛒✨
