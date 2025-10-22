"""
DeepSeek OCR провайдер
"""
from .base_provider import BaseOCRProvider
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DeepSeekOCRProvider(BaseOCRProvider):
    """
    Провайдер для DeepSeek OCR.
    Использует vLLM для инференса модели deepseek-ai/DeepSeek-OCR.
    Оптимизирован для высокоточного распознавания текста.
    """
    
    def __init__(self):
        super().__init__("DeepSeek")
        self.llm = None
        self.processor = None
    
    async def initialize(self) -> None:
        """Инициализация DeepSeek OCR"""
        try:
            from transformers import AutoProcessor
            from vllm import LLM
            
            model_name = "deepseek-ai/DeepSeek-OCR"
            
            logger.info(f"{self.provider_name}: Загрузка модели {model_name}...")
            
            # Загружаем процессор для обработки изображений
            self.processor = AutoProcessor.from_pretrained(model_name)
            
            # Загружаем модель через vLLM для быстрого инференса
            self.llm = LLM(
                model=model_name,
                trust_remote_code=True,
                max_model_len=8192,
                gpu_memory_utilization=0.5,  # Используем 50% GPU памяти
            )
            
            logger.info(f"{self.provider_name}: Модель готова")
            
        except ImportError as e:
            logger.error(f"{self.provider_name}: Не установлены зависимости")
            raise ImportError(
                "DeepSeek OCR требует: pip install vllm transformers"
            ) from e
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка инициализации: {e}")
            raise
    
    async def extract_text(self, file_path: str) -> str:
        """
        Извлекает текст из изображения/PDF используя DeepSeek OCR
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            str: Распознанный текст
        """
        from PIL import Image
        import fitz  # PyMuPDF для PDF
        
        path = Path(file_path)
        
        try:
            # Обрабатываем PDF или изображение
            if path.suffix.lower() == '.pdf':
                # Конвертируем PDF в изображения
                images = self._pdf_to_images(file_path)
                if not images:
                    logger.warning(f"{self.provider_name}: PDF не содержит изображений")
                    return ""
                
                # Обрабатываем первую страницу (можно расширить на все страницы)
                image = images[0]
            else:
                # Загружаем изображение
                image = Image.open(file_path).convert('RGB')
            
            # Подготавливаем входные данные
            inputs = self.processor(images=image, return_tensors="pt")
            
            # Генерируем текст с помощью модели
            from vllm import SamplingParams
            
            sampling_params = SamplingParams(
                temperature=0.0,  # Детерминированный вывод
                max_tokens=4096,
                stop=["</s>"]
            )
            
            # Выполняем инференс
            outputs = self.llm.generate(
                prompt_token_ids=[inputs.input_ids[0].tolist()],
                sampling_params=sampling_params
            )
            
            # Извлекаем текст из результата
            generated_text = outputs[0].outputs[0].text
            
            if not generated_text.strip():
                logger.warning(f"{self.provider_name}: Пустой результат для {file_path}")
                return ""
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка обработки: {e}")
            raise
    
    def _pdf_to_images(self, pdf_path: str) -> list:
        """Конвертирует PDF страницы в изображения"""
        import fitz
        from PIL import Image
        import io
        
        images = []
        doc = fitz.open(pdf_path)
        
        for page_num in range(min(5, len(doc))):  # Макс 5 страниц
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x увеличение качества
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append(img)
        
        doc.close()
        return images
    
    def cleanup(self) -> None:
        """Очистка ресурсов"""
        if self.llm:
            del self.llm
            self.llm = None
        if self.processor:
            del self.processor
            self.processor = None
        
        logger.info(f"{self.provider_name}: Ресурсы освобождены")
