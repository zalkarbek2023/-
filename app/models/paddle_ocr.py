"""
PaddleOCR провайдер для распознавания текста
"""
from .base_provider import BaseOCRProvider
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PaddleOCRProvider(BaseOCRProvider):
    """
    Провайдер для PaddleOCR/PP-Structure.
    Поддерживает распознавание текста из документов с сохранением структуры.
    """
    
    def __init__(self):
        super().__init__("PaddleOCR")
        self.ocr = None
    
    async def initialize(self) -> None:
        """Инициализация PaddleOCR модели"""
        try:
            from paddleocr import PaddleOCR
            
            # PaddleOCR 3.0+ автоматически определяет GPU
            # use_gpu больше не используется как параметр
            # lang='ch' поддерживает: китайский + английский + цифры
            self.ocr = PaddleOCR(
                use_angle_cls=True,  # Определение угла поворота
                lang='ch'  # Китайский + английский (multi-language)
            )
            
            logger.info(f"{self.provider_name}: Модель успешно инициализирована")
            
        except ImportError as e:
            logger.error(f"{self.provider_name}: Не установлена библиотека PaddleOCR")
            raise ImportError(
                "PaddleOCR не установлен. Установите: pip install paddleocr paddlepaddle"
            ) from e
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка инициализации: {e}")
            raise
    
    async def extract_text(self, file_path: str) -> str:
        """
        Извлекает текст из документа используя PaddleOCR
        
        Args:
            file_path: Путь к PDF или изображению
            
        Returns:
            str: Распознанный текст
        """
        if self.ocr is None:
            raise RuntimeError(f"{self.provider_name}: Модель не инициализирована")
        
        path = Path(file_path)
        logger.debug(f"{self.provider_name}: extract_text для {file_path}, suffix: {path.suffix.lower()}")
        
        # Если PDF, конвертируем в изображения
        if path.suffix.lower() == '.pdf':
            logger.debug(f"{self.provider_name}: Обработка как PDF")
            return await self._process_pdf(file_path)
        else:
            logger.debug(f"{self.provider_name}: Обработка как изображение")
            return await self._process_image(file_path)
    
    async def _process_image(self, image_path: str) -> str:
        """Обработка одного изображения"""
        # PaddleOCR 3.0 не использует параметр cls
        result = self.ocr.ocr(image_path)
        
        logger.debug(f"{self.provider_name}: result type: {type(result)}, len: {len(result) if result else 0}")
        
        if not result or not result[0]:
            logger.warning(f"{self.provider_name}: Пустой результат для {image_path}")
            return ""
        
        text_lines = []
        
        # Обработка каждой страницы (PaddleOCR 3.x возвращает OCRResult объекты)
        for page_result in result:
            if page_result is None:
                continue
            
            logger.debug(f"{self.provider_name}: page_result type: {type(page_result)}")
            
            # Получаем JSON данные из OCRResult
            data = page_result.json['res']
            
            # Извлекаем распознанный текст
            if 'rec_texts' in data:
                texts = data['rec_texts']
                logger.debug(f"{self.provider_name}: Найдено {len(texts)} строк текста")
                text_lines.extend(texts)
            else:
                logger.warning(f"{self.provider_name}: rec_texts не найден в data, ключи: {list(data.keys())}")
        
        return '\n'.join(text_lines)
    
    async def _process_pdf(self, pdf_path: str) -> str:
        """Обработка PDF документа"""
        logger.debug(f"{self.provider_name}: Начало обработки PDF {pdf_path}")
        try:
            from pdf2image import convert_from_path
            
            # Конвертируем PDF в изображения (dpi=250 для оптимального качества OCR)
            # dpi=200 работает, но dpi=250 дает лучшее распознавание мелкого текста
            # dpi=300 приводит к пустым результатам в PaddleOCR 3.x
            logger.debug(f"{self.provider_name}: Конвертация PDF в изображения...")
            images = convert_from_path(pdf_path, dpi=250)
            logger.debug(f"{self.provider_name}: Получено {len(images)} страниц")
            
            all_text = []
            for i, image in enumerate(images):
                logger.debug(f"{self.provider_name}: Обработка страницы {i+1}/{len(images)}")
                
                # Сохраняем временно изображение
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    image.save(tmp.name, 'PNG')
                    logger.debug(f"{self.provider_name}: Временный файл: {tmp.name}")
                    page_text = await self._process_image(tmp.name)
                    logger.debug(f"{self.provider_name}: Получено {len(page_text)} символов со страницы {i+1}")
                    all_text.append(page_text)
                
                # Удаляем временный файл
                Path(tmp.name).unlink(missing_ok=True)
            
            result = '\n\n'.join(all_text)
            logger.debug(f"{self.provider_name}: Итого текста: {len(result)} символов")
            return result
            
        except ImportError:
            logger.error(f"{self.provider_name}: pdf2image не установлен")
            raise ImportError("Установите pdf2image: pip install pdf2image")
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка обработки PDF: {e}")
            raise
