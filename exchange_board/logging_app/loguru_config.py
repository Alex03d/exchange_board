import os

from loguru import logger

logger.remove()

# Определение базового каталога, который будет указывать на директорию logging_app
base_directory = os.path.dirname(os.path.abspath(__file__))

# Создание пути к папке logs внутри директории logging_app
log_directory = os.path.join(base_directory, "logs")

# Создание папки logs, если она еще не существует
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Настройка логгера для сохранения логов в папку logs
logger.add(
    f"{log_directory}/file_{{time}}.log",
    rotation="5 MB",
    compression="zip",
    format="{time} {level} {message}",
    level="DEBUG"
)
