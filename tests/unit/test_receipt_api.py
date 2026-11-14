"""Offline contract tests for the documented app.api_main entrypoint."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import api_main as api


@pytest.fixture
def client():
    with TestClient(api.app) as value:
        yield value


@pytest.fixture
def png():
    buffer = io.BytesIO()
    with Image.new("RGBA", (8, 12), "white") as image:
        image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_demo_is_explicit_and_does_not_call_ocr(client, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("The synthetic text fixture must not call OCR")
    monkeypatch.setattr(api.pytesseract, "image_to_string", unexpected)
    response = client.post("/api/v1/receipt/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["processing_info"]["mode"] == "synthetic_fixture"
    assert "no OCR" in data["processing_info"]["ocr_engine"]
    assert [item["food_name"] for item in data["items"]] == ["Apples", "Bread, commercial", "Milk"]
    assert data["items_found"] == 3
    assert data["items"][0]["raw_text"] == "APPLES 2.00"


def test_upload_decodes_rgb_preserves_evidence_and_deduplicates(client, png, monkeypatch):
    def ocr(image, **kwargs):
        assert image.mode == "RGB"
        assert image.size == (8, 12)
        assert kwargs["timeout"] == 30
        return "RECEIPT\nMILK 4.00\nMILK 4.00\nBREAD 3.00\nTOTAL 11.00"
    monkeypatch.setattr(api.pytesseract, "image_to_string", ocr)
    response = client.post("/api/v1/receipt/process", files={"file": ("synthetic.png", png, "image/png")})
    assert response.status_code == 200
    data = response.json()
    assert [item["food_name"] for item in data["items"]] == ["Milk", "Bread, commercial"]
    assert data["processing_info"]["mode"] == "uploaded_image"
    assert data["processing_info"]["raw_items_found"] == 3
    assert data["items"][0]["raw_text"] == "MILK 4.00"


@pytest.mark.parametrize("content,mime,expected", [
    (b"text", "text/plain", 400),
    (b"", "image/png", 400),
    (b"not an image", "image/jpeg", 400),
    (b"x" * (api.MAX_UPLOAD_BYTES + 1), "image/png", 413),
])
def test_invalid_uploads_are_client_errors(client, content, mime, expected, monkeypatch):
    def unexpected(*args, **kwargs):
        pytest.fail("Invalid uploads must not reach OCR")
    monkeypatch.setattr(api.pytesseract, "image_to_string", unexpected)
    response = client.post("/api/v1/receipt/process", files={"file": ("input", content, mime)})
    assert response.status_code == expected
    assert isinstance(response.json()["detail"], str)


def test_missing_upload_is_validation_error(client):
    assert client.post("/api/v1/receipt/process").status_code == 422


def test_decoded_pixel_limit_is_checked_before_ocr(client, png, monkeypatch):
    monkeypatch.setattr(api, "MAX_IMAGE_PIXELS", 50)
    response = client.post("/api/v1/receipt/process", files={"file": ("test.png", png, "image/png")})
    assert response.status_code == 413
    assert "megapixel" in response.json()["detail"]


def test_svg_is_rejected_as_unsupported_image(client):
    response = client.post("/api/v1/receipt/process", files={"file": ("test.svg", b'<svg xmlns="http://www.w3.org/2000/svg"/>', "image/svg+xml")})
    assert response.status_code == 400


def test_api_does_not_enable_cross_origin_browser_access(client):
    response = client.post("/api/v1/receipt/demo", headers={"Origin": "https://unrelated.example"})
    assert "access-control-allow-origin" not in response.headers
    assert "access-control-allow-credentials" not in response.headers


def test_missing_tesseract_has_actionable_response(client, png, monkeypatch):
    def unavailable(*args, **kwargs):
        raise api.pytesseract.TesseractNotFoundError()
    monkeypatch.setattr(api.pytesseract, "image_to_string", unavailable)
    response = client.post("/api/v1/receipt/process", files={"file": ("test.png", png, "image/png")})
    assert response.status_code == 503
    assert "synthetic demo" in response.json()["detail"]


def test_unexpected_ocr_failure_does_not_disclose_internal_exception(client, png, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("PRIVATE_SENTINEL internal path and receipt contents")
    monkeypatch.setattr(api.pytesseract, "image_to_string", fail)
    response = client.post("/api/v1/receipt/process", files={"file": ("test.png", png, "image/png")})
    assert response.status_code == 500
    assert "PRIVATE_SENTINEL" not in response.text
    assert response.json()["success"] is False


@pytest.mark.parametrize("line,expected", [
    ("GV BUTTER 3.00", "Butter"),
    ("GV PNT BUTTR 4.00", "Peanut Butter"),
    ("WHOLE MILK 4.00", "Milk"),
    ("PEANUT BUTTER 4.00", "Peanut Butter"),
    ("ORGANIC MILK 4.00", "Milk"),
    ("PINEAPPLE 3.00", "PINEAPPLE 3.00"),
    ("EGGPLANT 2.00", "EGGPLANT 2.00"),
])
def test_matching_requires_complete_alias_and_prefers_longest(line, expected):
    assert api.match_food_item(line)[0] == expected


def test_unknown_items_and_totals_are_not_reported_as_matches():
    result = api.build_receipt_result("RECEIPT\nUNKNOWN ITEM\nTOTAL 4.00\n123.45", (1, 1), "RGB")
    assert result.items == []
    assert result.raw_text_preview.startswith("RECEIPT")


def test_metadata_words_inside_an_item_do_not_discard_it():
    result = api.build_receipt_result("STORE BRAND MILK 4.00\nTOTAL MILK 4.00", (1, 1), "RGB")
    assert len(result.items) == 1
    assert result.items[0].raw_text == "STORE BRAND MILK 4.00"


def test_static_page_uses_module_relative_path(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Try the synthetic example" in response.text


def test_reference_endpoints_and_missing_food(client):
    assert client.get("/api/v1/health").json()["status"] == "healthy"
    assert len(client.get("/api/v1/food-database").json()) > 0
    assert client.get("/api/v1/food-database/Milk").json()["name"] == "Milk"
    assert client.get("/api/v1/food-database/unknown").status_code == 404
