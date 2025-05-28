import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    # Создаем директорию для логов
    logs_dir = Path(__file__).resolve().parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Настраиваем форматтер
    formatter = logging.Formatter(
        '[%(levelname)s] %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем файловый обработчик
    file_handler = RotatingFileHandler(
        logs_dir / 'inventory.log',
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Настраиваем консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Настраиваем логгер Django
    django_logger = logging.getLogger('django')
    django_logger.setLevel(logging.INFO)
    
    # Настраиваем логгер приложения
    app_logger = logging.getLogger('employees')
    app_logger.setLevel(logging.DEBUG)
    
    # Тестовый лог
    root_logger.info("Логирование настроено") 