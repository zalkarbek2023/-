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
        self.reader_ch = None  # Китайский + английский
        self.reader_ru = None  # Русский + английский
        self.pdf2image = None
    
    async def initialize(self) -> None:
        """Инициализация EasyOCR"""
        # Проверяем, не загружены ли уже ридеры
        if self.reader_ch is not None and self.reader_ru is not None:
            logger.debug(f"{self.provider_name}: Ридеры уже загружены, пропускаем")
            return
        
        try:
            import easyocr
            from pdf2image import convert_from_path
            
            self.pdf2image = convert_from_path
            
            # EasyOCR требует особых комбинаций языков
            # Китайский упрощенный совместим только с английским
            # Для многоязычного OCR используем 2 reader'а
            self.reader_ch = easyocr.Reader(
                ['ch_sim', 'en'],  # Китайский + английский
                gpu=False,
                verbose=False
            )
            self.reader_ru = easyocr.Reader(
                ['ru', 'en'],  # Русский + английский
                gpu=False,
                verbose=False
            )
            
            logger.info(f"{self.provider_name}: EasyOCR готов (ch+en+ru dual-reader, CPU)")
            
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
                
                # Используем оба reader'а для максимального покрытия языков
                # 1. Китайский + английский
                results_ch = self.reader_ch.readtext(img_array)
                # 2. Русский + английский
                results_ru = self.reader_ru.readtext(img_array)
                
                # Объединяем результаты (удаляем дубликаты английского)
                all_texts = []
                
                # Добавляем китайский + английский
                for detection in results_ch:
                    bbox, text, confidence = detection
                    if confidence > 0.3:
                        all_texts.append(text)
                
                # Добавляем только русский (английский уже есть)
                for detection in results_ru:
                    bbox, text, confidence = detection
                    if confidence > 0.3 and not text.isascii():  # Только не-ASCII (русский)
                        all_texts.append(text)
                
                if all_texts:
                    page_text = ' '.join(all_texts)
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
            # Используем оба reader'а
            results_ch = self.reader_ch.readtext(str(image_path))
            results_ru = self.reader_ru.readtext(str(image_path))
            
            # Объединяем результаты
            all_texts = []
            
            for detection in results_ch:
                bbox, text, confidence = detection
                if confidence > 0.3:
                    all_texts.append(text)
            
            for detection in results_ru:
                bbox, text, confidence = detection
                if confidence > 0.3 and not text.isascii():
                    all_texts.append(text)
            
            full_text = ' '.join(all_texts)
            
            if not full_text.strip():
                logger.warning(f"{self.provider_name}: Пустой результат для {image_path}")
                return ""
            
            logger.info(f"{self.provider_name}: {len(full_text)} символов")
            return full_text
            
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка image OCR: {e}")
            raise
