from fastapi import UploadFile
from app.services.ocr_service import OCRService
from PIL import Image
import pytest
import io

@pytest.fixture
def ocr_service():
    return OCRService()

def test_ocr_extraction(ocr_service):
    # Test with a sample image of a grocery receipt
    with open("tests/sample_receipt.jpg", "rb") as image_file:
        image = Image.open(io.BytesIO(image_file.read()))
        extracted_text = ocr_service.extract_text(image)
        
        # Check if the extracted text is not empty
        assert extracted_text is not None
        assert len(extracted_text) > 0

def test_ocr_parsing(ocr_service):
    sample_text = "YELLOW ONION 3LB\n$2.99\nTOTAL: $2.99"
    items = ocr_service.parse_items(sample_text)
    
    # Check if the item is correctly parsed
    assert "YELLOW ONION" in items
    assert len(items) == 1  # Expecting one item to be parsed

def test_ocr_invalid_image(ocr_service):
    # Test with an invalid image input
    with pytest.raises(Exception):
        ocr_service.extract_text(None)  # Should raise an error for invalid input