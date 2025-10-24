"""
PP-Structure провайдер для структурного анализа документов

Режимы работы:
- GPU: официальный PPStructureV3 (формулы, графики, layout, таблицы, OCR)
- CPU: безопасный fallback на TableRecognitionPipelineV2 (layout, таблицы, OCR)

Требования для GPU режима:
- Установлен paddlepaddle-gpu==3.0.0 (под вашу версию CUDA)
- Драйвер NVIDIA и доступный GPU (проверка: nvidia-smi)

Переключатели через переменные окружения:
- PPOCR_USE_FORMULA=true|false (по умолчанию: true)
- PPOCR_USE_CHART=true|false (по умолчанию: true)
"""
from .base_provider import BaseOCRProvider
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class PaddleOCRProvider(BaseOCRProvider):
    """
    Провайдер для PP-Structure (структурный анализ документов).
    
    Функциональность PP-StructureV3:
    - Layout detection (анализ структуры документа)
    - Table recognition (таблицы в HTML)
    - Multi-language OCR (китайский, английский, русский)
    - Document orientation correction
    
    Реализация: TableRecognitionPipelineV2 (стабильная альтернатива для CPU)
    """
    
    def __init__(self):
        super().__init__("PP-StructureV3")
        self.pipeline = None
    
    async def initialize(self) -> None:
        """Инициализация PP-Structure pipeline (GPU: PPStructureV3, CPU: fallback)"""
        # Проверяем, не загружена ли уже модель
        if self.pipeline is not None:
            logger.debug(f"{self.provider_name}: Модель уже инициализирована, пропускаем загрузку")
            return

        # Переключатели формул/графиков
        use_formula = os.getenv("PPOCR_USE_FORMULA", "true").lower() == "true"
        use_chart = os.getenv("PPOCR_USE_CHART", "true").lower() == "true"

        # Пытаемся загрузить официальный PPStructureV3 (GPU)
        try:
            from paddleocr import PPStructureV3

            self.pipeline = PPStructureV3(
                use_doc_orientation_classify=True,
                use_textline_orientation=True,
                use_formula_recognition=use_formula,
                use_chart_recognition=use_chart,
            )
            logger.info(f"{self.provider_name}: PPStructureV3 инициализирована (GPU)")
            return
        except Exception as e:
            logger.warning(
                f"{self.provider_name}: PPStructureV3 недоступна ({e}). Переключаемся на CPU fallback (TableRecognitionPipelineV2)."
            )

        # CPU fallback: TableRecognitionPipelineV2
        try:
            from paddleocr import TableRecognitionPipelineV2
        except ImportError as e:
            logger.error(f"{self.provider_name}: TableRecognitionPipelineV2 не установлен")
            raise ImportError(
                'PP-Structure не установлен. Установите: pip install "paddleocr>=3.3.0"'
            ) from e

        try:
            self.pipeline = TableRecognitionPipelineV2(
                use_layout_detection=True,  # Анализ структуры документа
                use_ocr_model=True,         # OCR для распознавания текста
            )
            logger.info(f"{self.provider_name}: PP-Structure инициализирована (CPU fallback: TableRecognitionPipelineV2)")
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка инициализации PP-Structure: {e}")
            raise
    
    async def extract_text(self, file_path: str) -> str:
        """
        Извлекает текст с сохранением структуры используя PP-Structure
        
        Args:
            file_path: Путь к PDF или изображению
            
        Returns:
            str: Текст в Markdown формате с сохранением структуры
        """
        if self.pipeline is None:
            raise RuntimeError(f"{self.provider_name}: Модель не инициализирована")
        
        path = Path(file_path)
        logger.debug(f"{self.provider_name}: Обработка {file_path}")
        
        # Если PDF, конвертируем в изображения
        if path.suffix.lower() == '.pdf':
            return await self._process_pdf(file_path)
        else:
            return await self._process_image(file_path)
    
    async def _process_image(self, image_path: str) -> str:
        """Обработка одного изображения с PP-Structure pipeline"""
        try:
            # TableRecognitionPipelineV2.predict() возвращает список результатов
            results = self.pipeline.predict(image_path)
            
            if not results or len(results) == 0:
                logger.warning(f"{self.provider_name}: Пустой результат для {image_path}")
                return ""
            
            # Берём первый результат (для одного изображения)
            page_result = results[0]
            text_parts = []
            
            # 1) Извлекаем общий OCR текст (весь распознанный текст на странице)
            if 'overall_ocr_res' in page_result:
                ocr_res = page_result['overall_ocr_res']
                if 'rec_texts' in ocr_res and ocr_res['rec_texts']:
                    # Собираем все распознанные строки текста
                    text_lines = [text for text in ocr_res['rec_texts'] if text.strip()]
                    if text_lines:
                        text_parts.append('\n'.join(text_lines))
            
            # 2) Извлекаем таблицы (если есть)
            if 'table_res_list' in page_result and page_result['table_res_list']:
                for table in page_result['table_res_list']:
                    # Таблица в HTML формате
                    if 'pred_html' in table and table['pred_html']:
                        text_parts.append(f"\n\n[Таблица]\n{table['pred_html']}\n")
                    
                    # Текст вокруг таблицы
                    if 'neighbor_texts' in table and table['neighbor_texts']:
                        text_parts.append(table['neighbor_texts'])
            
            result_text = '\n\n'.join(text_parts)
            logger.debug(f"{self.provider_name}: Извлечено {len(result_text)} символов")
            return result_text
            
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка обработки изображения: {e}")
            raise
    
    async def _process_pdf(self, pdf_path: str) -> str:
        """Обработка PDF документа"""
        try:
            from pdf2image import convert_from_path
            
            # Конвертируем PDF в изображения (dpi=250 оптимально)
            images = convert_from_path(pdf_path, dpi=250)
            logger.info(f"{self.provider_name}: Конвертировано {len(images)} страниц")
            
            all_text = []
            for i, image in enumerate(images, 1):
                # Сохраняем временно изображение
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                    image.save(tmp.name, 'PNG')
                    page_text = await self._process_image(tmp.name)
                    
                    if page_text:
                        all_text.append(f"## Страница {i}\n\n{page_text}")
                    
                    logger.debug(f"{self.provider_name}: Страница {i}: {len(page_text)} символов")
                
                # Удаляем временный файл
                Path(tmp.name).unlink(missing_ok=True)
            
            result = '\n\n'.join(all_text)
            logger.info(f"{self.provider_name}: Всего {len(result)} символов")
            return result
            
        except ImportError:
            logger.error(f"{self.provider_name}: pdf2image не установлен")
            raise ImportError("Установите pdf2image: pip install pdf2image")
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка обработки PDF: {e}")
            raise
