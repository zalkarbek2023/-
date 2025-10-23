"""
EasyOCR провайдер
"""
from .base_provider import BaseOCRProvider
import logging
from pathlib import Path
from typing import List
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class EasyOCRProvider(BaseOCRProvider):
    """
    Провайдер для EasyOCR.
    Поддерживает 80+ языков, точная детекция текста.
    Работает на CPU и GPU (при наличии CUDA).
    """
    
    def __init__(self):
        super().__init__("EasyOCR")
        self.reader = None
        self.pdf2image = None
    
    async def initialize(self) -> None:
        """Инициализация EasyOCR"""
        try:
            import easyocr
            from pdf2image import convert_from_path
            
            self.pdf2image = convert_from_path
            
            # Создаем reader для английского и русского языков
            # gpu=False для работы на CPU (production-ready)
            self.reader = easyocr.Reader(
                ['en', 'ru'],
                gpu=False,  # CPU режим для стабильности
                verbose=False
            )
            
            logger.info(f"{self.provider_name}: EasyOCR готов (CPU режим)")
            
        except ImportError as e:
            logger.error(f"{self.provider_name}: EasyOCR не установлен")
            raise ImportError(
                "EasyOCR не установлен. Установите: pip install easyocr"
            ) from e
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка инициализации: {e}")
            raise
    
    async def extract_text(self, file_path: str) -> str:
        """
        Извлекает текст из PDF/изображений используя EasyOCR
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            str: Распознанный текст
        """
        path = Path(file_path)
        
        try:
            if path.suffix.lower() == '.pdf':
                return await self._extract_from_pdf(path)
            elif path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                return await self._extract_from_image(path)
            else:
                raise ValueError(f"{self.provider_name}: Неподдерживаемый формат: {path.suffix}")
            
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка обработки {file_path}: {e}")
            raise
    
    async def _extract_from_pdf(self, pdf_path: Path) -> str:
        """Извлекает текст из PDF конвертируя в изображения"""
        try:
            # Конвертируем PDF в изображения (250 DPI)
            images = self.pdf2image(
                str(pdf_path),
                dpi=250,
                fmt='png'
            )
            
            logger.info(f"{self.provider_name}: Конвертировано {len(images)} страниц")
            
            # OCR для каждой страницы
            texts = []
            for page_num, image in enumerate(images, 1):
                # Конвертируем PIL Image в numpy array
                img_array = np.array(image)
                
                # EasyOCR возвращает список: [[bbox, text, confidence], ...]
                results = self.reader.readtext(img_array)
                
                # Извлекаем только текст, сортируя по позиции (top-to-bottom, left-to-right)
                page_texts = []
                for detection in results:
                    bbox, text, confidence = detection
                    if confidence > 0.3:  # Фильтруем низкую уверенность
                        page_texts.append(text)
                
                if page_texts:
                    page_text = ' '.join(page_texts)
                    texts.append(page_text)
                    logger.debug(f"{self.provider_name}: Страница {page_num}: {len(page_text)} символов")
            
            full_text = '\n\n'.join(texts)
            
            if not full_text.strip():
                logger.warning(f"{self.provider_name}: Пустой результат для {pdf_path}")
                return ""
            
            logger.info(f"{self.provider_name}: Всего {len(full_text)} символов")
            return full_text
            
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка PDF OCR: {e}")
            raise
    
    async def _extract_from_image(self, image_path: Path) -> str:
        """Извлекает текст из изображения"""
        try:
            # EasyOCR работает напрямую с путями к файлам
            results = self.reader.readtext(str(image_path))
            
            # Извлекаем текст
            texts = []
            for detection in results:
                bbox, text, confidence = detection
                if confidence > 0.3:
                    texts.append(text)
            
            full_text = ' '.join(texts)
            
            if not full_text.strip():
                logger.warning(f"{self.provider_name}: Пустой результат для {image_path}")
                return ""
            
            logger.info(f"{self.provider_name}: {len(full_text)} символов")
            return full_text
            
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка image OCR: {e}")
            raise
