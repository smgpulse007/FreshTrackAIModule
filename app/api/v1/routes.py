from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ocr_service import OCRService
from app.services.embedding_service import EmbeddingService
from app.services.matching_service import MatchingService
from app.services.shelf_life_service import ShelfLifeService
from app.models.schemas import ReceiptResponse, ItemResult
from app.core.config import settings
from PIL import Image
import io

router = APIRouter()

ocr_service = OCRService(engine=settings.ocr_engine)
shelf_life_service = ShelfLifeService(settings.foodkeeper_data_path)
embedding_service = EmbeddingService()
matching_service = MatchingService(embedding=embedding_service, shelf_life=shelf_life_service, threshold=0.8)

@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/process_receipt", response_model=ReceiptResponse)
async def process_receipt(file: UploadFile = File(...)):
    # Validate file is an image by mime-type and content sniff
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    content = await file.read()
    try:
        image = Image.open(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    try:
        ocr_text = ocr_service.extract_text(image)
        item_names = ocr_service.parse_items(ocr_text)
        results: list[ItemResult] = []
        for original in item_names:
            match = matching_service.match_item(original)
            if isinstance(match, tuple) and match[0] is None:
                suggestions = match[1]
                results.append(ItemResult(original_text=original, matched_item=None, shelf_life=None, suggestions=suggestions))
            else:
                matched_name = match
                shelf = shelf_life_service.get_shelf_life(matched_name) or {}
                results.append(ItemResult(original_text=original, matched_item=matched_name, shelf_life=shelf))
        return ReceiptResponse(items=results)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ocr_preview")
async def ocr_preview(file: UploadFile = File(...), max_lines: int = 20):
    # Quick debug endpoint to inspect raw OCR output lines
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    content = await file.read()
    try:
        image = Image.open(io.BytesIO(content))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    text = ocr_service.extract_text(image)
    lines = text.splitlines() if text else []
    return {"line_count": len(lines), "preview": lines[:max(1, max_lines)]}