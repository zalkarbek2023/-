"""
Базовый абстрактный класс для всех OCR-провайдеров
"""
from abc import ABC, abstractmethod
from typing import Tuple
import time
import logging

logger = logging.getLogger(__name__)


class BaseOCRProvider(ABC):
    """
    Абстрактный базовый класс для OCR-провайдеров.
    Все конкретные реализации должны наследоваться от этого класса.
    """
    
    def __init__(self, provider_name: str):
        """
        Инициализация провайдера
        
        Args:
            provider_name: Название провайдера для идентификации
        """
        self.provider_name = provider_name
        self.is_initialized = False
        logger.info(f"Создан провайдер: {provider_name}")
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Инициализация модели OCR.
        Вызывается один раз при старте приложения.
        Может включать загрузку моделей, настройку параметров и т.д.
        """
        pass
    
    @abstractmethod
    async def extract_text(self, file_path: str) -> str:
        """
        Извлекает текст из документа.
        
        Args:
            file_path: Путь к файлу для обработки (PDF или изображение)
            
        Returns:
            str: Распознанный текст
            
        Raises:
            Exception: При ошибках обработки
        """
        pass
    
    async def process(self, file_path: str) -> Tuple[str, float]:
        """
        Обрабатывает файл и возвращает результат с метриками.
        Обертка над extract_text с замером времени.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Tuple[str, float]: (распознанный текст, время обработки в секундах)
        """
        if not self.is_initialized:
            await self.initialize()
            self.is_initialized = True
        
        start_time = time.time()
        try:
            logger.info(f"{self.provider_name}: Начало обработки {file_path}")
            text = await self.extract_text(file_path)
            processing_time = time.time() - start_time
            
            logger.info(
                f"{self.provider_name}: Обработка завершена. "
                f"Символов: {len(text)}, Время: {processing_time:.2f}с"
            )
            
            return text, processing_time
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"{self.provider_name}: Ошибка при обработке {file_path}: {str(e)}",
                exc_info=True
            )
            raise
    
    def cleanup(self) -> None:
        """
        Освобождение ресурсов провайдера.
        Вызывается при завершении работы приложения.
        """
        logger.info(f"{self.provider_name}: Очистка ресурсов")
        self.is_initialized = False
    
    def get_supported_formats(self) -> list[str]:
        """
        Возвращает список поддерживаемых форматов файлов.
        
        Returns:
            list[str]: Список расширений (например, ['pdf', 'png', 'jpg'])
        """
        return ['pdf', 'png', 'jpg', 'jpeg', 'tiff']
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.provider_name}', initialized={self.is_initialized})>"
