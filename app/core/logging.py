from logging import getLogger, StreamHandler, Formatter, INFO, DEBUG, ERROR, FileHandler, basicConfig

_LOGGER_NAME = "grocery_receipt_service"

def setup_logging(level: str = "INFO") -> None:
	"""Configure application logging.

	Safe to call multiple times; handlers won't be duplicated.
	"""
	logger = getLogger(_LOGGER_NAME)
	if logger.handlers:
		# Already configured
		return

	numeric_level = INFO if level.upper() == "INFO" else DEBUG if level.upper() == "DEBUG" else ERROR
	logger.setLevel(numeric_level)

	console_handler = StreamHandler()
	console_handler.setLevel(numeric_level)
	console_formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	console_handler.setFormatter(console_formatter)

	file_handler = FileHandler("app.log")
	file_handler.setLevel(ERROR)
	file_formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	file_handler.setFormatter(file_formatter)

	logger.addHandler(console_handler)
	logger.addHandler(file_handler)

def get_logger():
	return getLogger(_LOGGER_NAME)