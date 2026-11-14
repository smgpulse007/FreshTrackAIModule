"""Exercise real Tesseract and HTTP upload using only generated pixels."""
import io
import json
import urllib.request
from PIL import Image, ImageDraw, ImageFont


def main():
    image = Image.new("RGB", (700, 350), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=32)
    draw.multiline_text((30, 30), "SYNTHETIC RECEIPT\nAPPLES 2.00\nBREAD 3.00\nMILK 4.00\nTOTAL 9.00", font=font, fill="black", spacing=16)
    output = io.BytesIO()
    image.save(output, format="PNG")
    boundary = "FreshTrackSyntheticFixture"
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="synthetic.png"\r\nContent-Type: image/png\r\n\r\n'.encode()
            + output.getvalue() + f"\r\n--{boundary}--\r\n".encode())
    request = urllib.request.Request("http://127.0.0.1:8000/api/v1/receipt/process", data=body,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(request, timeout=45) as response:
        result = json.load(response)
    names = {item["food_name"] for item in result["items"]}
    assert {"Apples", "Bread, commercial", "Milk"} <= names, result
    assert result["processing_info"]["mode"] == "uploaded_image"
    print("Real OCR upload smoke passed: generated receipt matched apples, bread, milk.")


if __name__ == "__main__":
    main()
