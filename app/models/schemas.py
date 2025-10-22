"""
Pydantic модели для API запросов и ответов
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime


class RawOCRResult(BaseModel):
    """Необработанный результат от одного OCR-провайдера"""
    provider_name: str = Field(..., description="Название OCR-модели")
    text: str = Field(..., description="Распознанный текст")
    processing_time: float = Field(..., description="Время обработки в секундах")
    error: Optional[str] = Field(None, description="Сообщение об ошибке, если есть")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider_name": "PaddleOCR",
                "text": "Распознанный текст документа",
                "processing_time": 1.234,
                "error": None
            }
        }


class CharacterDifference(BaseModel):
    """Информация о символе на определенной позиции"""
    position: int = Field(..., description="Позиция символа в выровненном тексте")
    char: str = Field(..., description="Символ")
    diff_type: Literal["match", "mismatch", "insertion", "deletion"] = Field(
        ..., 
        description="Тип различия"
    )


class DiffSegment(BaseModel):
    """Сегмент текста с информацией о расхождениях"""
    text: str = Field(..., description="Текстовый сегмент")
    segment_type: Literal["match", "minor_diff", "major_diff"] = Field(
        ...,
        description="Тип сегмента: match - все совпадают, minor_diff - 1-2 различия, major_diff - 3+ различия"
    )
    start_position: int = Field(..., description="Начальная позиция сегмента")
    end_position: int = Field(..., description="Конечная позиция сегмента")
    providers_data: Dict[str, str] = Field(
        ...,
        description="Данные от каждого провайдера для этого сегмента"
    )


class ComparisonResult(BaseModel):
    """Результат сравнения для одного провайдера"""
    provider_name: str = Field(..., description="Название провайдера")
    segments: List[DiffSegment] = Field(..., description="Список сегментов с разметкой")
    total_characters: int = Field(..., description="Общее количество символов")
    match_count: int = Field(..., description="Количество совпадающих символов")
    diff_count: int = Field(..., description="Количество различающихся символов")
    accuracy_percent: float = Field(..., description="Процент точности относительно консенсуса")


class OCRStatistics(BaseModel):
    """Статистика для одного провайдера"""
    provider_name: str
    total_chars: int
    differences: int
    accuracy: float = Field(..., description="Процент точности")
    processing_time: float = Field(..., description="Время обработки в секундах")


class ComparisonResponse(BaseModel):
    """Полный ответ API с результатами сравнения"""
    task_id: str = Field(..., description="Уникальный идентификатор задачи")
    filename: str = Field(..., description="Имя загруженного файла")
    status: Literal["completed", "processing", "failed"] = Field(
        ...,
        description="Статус обработки"
    )
    created_at: datetime = Field(..., description="Время создания задачи")
    
    # Сырые результаты
    raw_results: List[RawOCRResult] = Field(
        ...,
        description="Необработанные результаты от каждой OCR-модели"
    )
    
    # Детальное сравнение
    comparison: List[ComparisonResult] = Field(
        ...,
        description="Посимвольное сравнение результатов"
    )
    
    # Статистика
    statistics: List[OCRStatistics] = Field(
        ...,
        description="Статистика по каждой модели"
    )
    
    # HTML визуализация (опционально)
    html_visualization: Optional[str] = Field(
        None,
        description="HTML-разметка с подсветкой различий"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "document.pdf",
                "status": "completed",
                "created_at": "2025-10-22T10:30:00",
                "raw_results": [],
                "comparison": [],
                "statistics": []
            }
        }


class UploadResponse(BaseModel):
    """Ответ при загрузке файла"""
    task_id: str = Field(..., description="ID задачи для отслеживания")
    filename: str = Field(..., description="Имя файла")
    message: str = Field(..., description="Статусное сообщение")


class StatusResponse(BaseModel):
    """Ответ о статусе обработки"""
    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: int = Field(..., ge=0, le=100, description="Прогресс обработки в процентах")
    message: Optional[str] = None
