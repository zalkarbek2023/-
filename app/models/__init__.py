"""
Инициализация пакета models
"""
from .schemas import (
    RawOCRResult,
    CharacterDifference,
    DiffSegment,
    ComparisonResult,
    OCRStatistics,
    ComparisonResponse,
    UploadResponse,
    StatusResponse
)

__all__ = [
    "RawOCRResult",
    "CharacterDifference",
    "DiffSegment",
    "ComparisonResult",
    "OCRStatistics",
    "ComparisonResponse",
    "UploadResponse",
    "StatusResponse"
]
