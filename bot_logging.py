import logging
from logging.handlers import RotatingFileHandler
import os

# === Имя логгера ===
logger = logging.getLogger("telegram_bot")
logger.setLevel(logging.DEBUG)

# === Формат логов ===
formatter = logging.Formatter(
    fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# === Консольный хендлер ===
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# === Файловый хендлер с ротацией ===
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
file_handler = RotatingFileHandler(
    filename=os.path.join(log_dir, "bot.log"),
    maxBytes=1_000_000,  # ~1MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# === Добавляем хендлеры, если ещё не добавлены (важно при импортах)
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

# === Отключаем повторное логгирование у родителя
logger.propagate = False