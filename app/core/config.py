import os


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "Grocery Receipt Shelf Life Service")
        self.version = os.getenv("VERSION", "1.0.0")
        self.ocr_engine = os.getenv("OCR_ENGINE", "PaddleOCR")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.foodkeeper_data_path = os.getenv("FOODKEEPER_DATA_PATH", "app/data/foodkeeper.json")
        self.canonical_items_path = os.getenv("CANONICAL_ITEMS_PATH", "app/data/canonical_items.json")


settings = Settings()