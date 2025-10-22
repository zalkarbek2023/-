"""
Сервис оркестрации OCR обработки и генерации статистики
"""
import asyncio
import logging
from typing import List, Dict
from datetime import datetime
import uuid

from app.models.schemas import (
    RawOCRResult,
    OCRStatistics,
    ComparisonResponse,
    ComparisonResult
)
from app.models.base_provider import BaseOCRProvider
from app.services.alignment import TextAlignmentService

logger = logging.getLogger(__name__)


class OCRComparisonService:
    """
    Основной сервис для управления процессом сравнения OCR моделей.
    """
    
    def __init__(self, providers: List[BaseOCRProvider]):
        """
        Инициализация сервиса
        
        Args:
            providers: Список OCR провайдеров для использования
        """
        self.providers = providers
        self.alignment_service = TextAlignmentService()
        self.tasks: Dict[str, dict] = {}  # Хранилище задач
        
        logger.info(f"OCRComparisonService инициализирован с {len(providers)} провайдерами")
    
    async def initialize_providers(self) -> None:
        """Инициализация всех провайдеров"""
        logger.info("Инициализация OCR провайдеров...")
        
        init_tasks = [
            provider.initialize() 
            for provider in self.providers
        ]
        
        results = await asyncio.gather(*init_tasks, return_exceptions=True)
        
        for provider, result in zip(self.providers, results):
            if isinstance(result, Exception):
                logger.error(f"Ошибка инициализации {provider.provider_name}: {result}")
            else:
                logger.info(f"✓ {provider.provider_name} инициализирован")
    
    async def process_document(
        self,
        file_path: str,
        filename: str,
        task_id: str = None
    ) -> ComparisonResponse:
        """
        Обрабатывает документ через все OCR модели и создает сравнение.
        
        Args:
            file_path: Путь к файлу
            filename: Имя файла
            task_id: ID задачи (опционально)
            
        Returns:
            ComparisonResponse: Полный результат сравнения
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        logger.info(f"Обработка документа {filename} (task_id: {task_id})")
        
        # Обновляем статус задачи
        self.tasks[task_id] = {
            'status': 'processing',
            'filename': filename,
            'started_at': datetime.now()
        }
        
        try:
            # Шаг 1: Параллельная обработка через все OCR
            raw_results = await self._run_all_ocr(file_path)
            
            # Шаг 2: Сравнение и выравнивание
            comparison_results = self.alignment_service.create_comparison_results(raw_results)
            
            # Шаг 3: Генерация статистики
            statistics = self._generate_statistics(raw_results, comparison_results)
            
            # Шаг 4: Формирование ответа
            response = ComparisonResponse(
                task_id=task_id,
                filename=filename,
                status='completed',
                created_at=self.tasks[task_id]['started_at'],
                raw_results=raw_results,
                comparison=comparison_results,
                statistics=statistics,
                html_visualization=None  # Будет добавлено позже
            )
            
            # Обновляем статус
            self.tasks[task_id]['status'] = 'completed'
            self.tasks[task_id]['result'] = response
            
            logger.info(f"Обработка {task_id} завершена успешно")
            
            return response
            
        except Exception as e:
            logger.error(f"Ошибка обработки {task_id}: {e}", exc_info=True)
            
            self.tasks[task_id]['status'] = 'failed'
            self.tasks[task_id]['error'] = str(e)
            
            raise
    
    async def _run_all_ocr(self, file_path: str) -> List[RawOCRResult]:
        """
        Запускает все OCR провайдеры параллельно.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            List[RawOCRResult]: Результаты от всех провайдеров
        """
        logger.info(f"Запуск {len(self.providers)} OCR провайдеров...")
        
        # Создаем задачи для всех провайдеров
        tasks = [
            self._run_single_ocr(provider, file_path)
            for provider in self.providers
        ]
        
        # Выполняем параллельно с обработкой исключений
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Обрабатываем результаты
        raw_results = []
        
        for provider, result in zip(self.providers, results):
            if isinstance(result, Exception):
                # Если провайдер упал, добавляем результат с ошибкой
                logger.error(f"{provider.provider_name} завершился с ошибкой: {result}")
                
                raw_results.append(RawOCRResult(
                    provider_name=provider.provider_name,
                    text="",
                    processing_time=0.0,
                    error=str(result)
                ))
            else:
                raw_results.append(result)
        
        # Фильтруем успешные результаты
        successful = [r for r in raw_results if r.error is None]
        logger.info(f"Успешно обработано: {len(successful)}/{len(self.providers)}")
        
        return raw_results
    
    async def _run_single_ocr(
        self,
        provider: BaseOCRProvider,
        file_path: str
    ) -> RawOCRResult:
        """
        Запускает один OCR провайдер.
        
        Args:
            provider: OCR провайдер
            file_path: Путь к файлу
            
        Returns:
            RawOCRResult: Результат обработки
        """
        try:
            text, processing_time = await provider.process(file_path)
            
            return RawOCRResult(
                provider_name=provider.provider_name,
                text=text,
                processing_time=processing_time,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Ошибка в {provider.provider_name}: {e}")
            
            return RawOCRResult(
                provider_name=provider.provider_name,
                text="",
                processing_time=0.0,
                error=str(e)
            )
    
    def _generate_statistics(
        self,
        raw_results: List[RawOCRResult],
        comparison_results: List[ComparisonResult]
    ) -> List[OCRStatistics]:
        """
        Генерирует статистику для каждого провайдера.
        
        Args:
            raw_results: Сырые результаты
            comparison_results: Результаты сравнения
            
        Returns:
            List[OCRStatistics]: Статистика по каждому провайдеру
        """
        statistics = []
        
        # Создаем словарь для быстрого поиска
        comparison_map = {
            cr.provider_name: cr 
            for cr in comparison_results
        }
        
        for raw in raw_results:
            comp = comparison_map.get(raw.provider_name)
            
            if comp:
                statistics.append(OCRStatistics(
                    provider_name=raw.provider_name,
                    total_chars=comp.total_characters,
                    differences=comp.diff_count,
                    accuracy=comp.accuracy_percent,
                    processing_time=raw.processing_time
                ))
            else:
                # Если нет результата сравнения (ошибка)
                statistics.append(OCRStatistics(
                    provider_name=raw.provider_name,
                    total_chars=0,
                    differences=0,
                    accuracy=0.0,
                    processing_time=raw.processing_time
                ))
        
        return statistics
    
    def get_task_status(self, task_id: str) -> dict:
        """
        Получить статус задачи.
        
        Args:
            task_id: ID задачи
            
        Returns:
            dict: Информация о статусе
        """
        task = self.tasks.get(task_id)
        
        if not task:
            return {
                'task_id': task_id,
                'status': 'not_found',
                'message': 'Задача не найдена'
            }
        
        return {
            'task_id': task_id,
            'status': task['status'],
            'filename': task.get('filename'),
            'started_at': task.get('started_at')
        }
