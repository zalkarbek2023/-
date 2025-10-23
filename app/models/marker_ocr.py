"""
Tesseract OCR провайдер
"""
from .base_provider import BaseOCRProvider
import logging
from pathlib import Path
from typing import List
from PIL import Image
import io

logger = logging.getLogger(__name__)


class TesseractOCRProvider(BaseOCRProvider):
    """
    Провайдер для Tesseract OCR.
    Стабильная, проверенная временем библиотека для OCR.
    Поддерживает 100+ языков, работает на CPU.
    """
    
    def __init__(self):
        super().__init__("Tesseract")
        self.pytesseract = None
        self.pdf2image = None
    
    async def initialize(self) -> None:
        """Инициализация Tesseract"""
        try:
            import pytesseract
            from pdf2image import convert_from_path
            
            self.pytesseract = pytesseract
            self.pdf2image = convert_from_path
            
            # Проверяем доступность tesseract
            version = pytesseract.get_tesseract_version()
            logger.info(f"{self.provider_name}: Tesseract v{version} готов")
            
        except ImportError as e:
            logger.error(f"{self.provider_name}: pytesseract не установлен")
            raise ImportError(
                "Tesseract не установлен. Установите: sudo apt-get install tesseract-ocr && pip install pytesseract"
            ) from e
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка инициализации: {e}")
            raise
    
    async def extract_text(self, file_path: str) -> str:
        """
        Извлекает текст из PDF/изображений используя Tesseract
        
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
            # Конвертируем PDF в изображения (250 DPI для качества)
            images = self.pdf2image(
                str(pdf_path),
                dpi=250,
                fmt='png'
            )
            
            logger.info(f"{self.provider_name}: Конвертировано {len(images)} страниц")
            
            # OCR для каждой страницы
            texts = []
            for page_num, image in enumerate(images, 1):
                # Используем multi-language: английский + русский
                text = self.pytesseract.image_to_string(
                    image,
                    lang='eng+rus',
                    config='--psm 6'  # Assume uniform text block
                )
                
                if text.strip():
                    texts.append(text.strip())
                    logger.debug(f"{self.provider_name}: Страница {page_num}: {len(text)} символов")
            
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
            image = Image.open(image_path)
            
            text = self.pytesseract.image_to_string(
                image,
                lang='eng+rus',
                config='--psm 6'
            )
            
            if not text.strip():
                logger.warning(f"{self.provider_name}: Пустой результат для {image_path}")
                return ""
            
            logger.info(f"{self.provider_name}: {len(text)} символов")
            return text.strip()
            
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка image OCR: {e}")
            raise
