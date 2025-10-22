"""
API endpoints для сервиса сравнения OCR моделей
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pathlib import Path
import shutil
import uuid
import os
import logging

from app.models.schemas import (
    UploadResponse,
    StatusResponse,
    ComparisonResponse
)
from app.services.comparison import OCRComparisonService
from app.utils.visualizer import HTMLVisualizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["OCR Comparison"])

# Будет инициализирован в main.py
_ocr_service: OCRComparisonService = None


def get_ocr_service() -> OCRComparisonService:
    """Dependency для получения OCR сервиса"""
    if _ocr_service is None:
        raise HTTPException(
            status_code=500,
            detail="OCR сервис не инициализирован"
        )
    return _ocr_service


def set_ocr_service(service: OCRComparisonService):
    """Установка глобального OCR сервиса"""
    global _ocr_service
    _ocr_service = service


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    service: OCRComparisonService = Depends(get_ocr_service)
) -> UploadResponse:
    """
    Загрузка документа для обработки.
    
    Поддерживаемые форматы: PDF, PNG, JPG, JPEG, TIFF
    Максимальный размер: 10MB
    """
    # Проверка расширения файла
    allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Неподдерживаемый формат файла. Разрешены: {', '.join(allowed_extensions)}"
        )
    
    # Генерация ID задачи
    task_id = str(uuid.uuid4())
    
    # Сохранение файла
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    upload_dir.mkdir(exist_ok=True)
    
    file_path = upload_dir / f"{task_id}_{file.filename}"
    
    try:
        # Сохраняем файл на диск
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Файл {file.filename} загружен как {file_path}")
        
        return UploadResponse(
            task_id=task_id,
            filename=file.filename,
            message="Файл успешно загружен. Используйте /api/process/{task_id} для начала обработки."
        )
        
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        
        # Удаляем частично загруженный файл
        if file_path.exists():
            file_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )
    finally:
        file.file.close()


@router.post("/process/{task_id}", response_model=StatusResponse)
async def process_document(
    task_id: str,
    service: OCRComparisonService = Depends(get_ocr_service)
) -> StatusResponse:
    """
    Запуск обработки документа через все OCR модели.
    
    Обработка выполняется асинхронно.
    Используйте /api/status/{task_id} для проверки статуса.
    """
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    
    # Ищем файл по task_id
    files = list(upload_dir.glob(f"{task_id}_*"))
    
    if not files:
        raise HTTPException(
            status_code=404,
            detail=f"Файл для задачи {task_id} не найден"
        )
    
    file_path = files[0]
    filename = file_path.name.replace(f"{task_id}_", "")
    
    # Запускаем обработку в фоне
    # В продакшене лучше использовать Celery или похожий task queue
    import asyncio
    
    async def background_process():
        try:
            await service.process_document(
                str(file_path),
                filename,
                task_id
            )
        except Exception as e:
            logger.error(f"Ошибка обработки {task_id}: {e}")
    
    # Создаем задачу (не ждем завершения)
    asyncio.create_task(background_process())
    
    return StatusResponse(
        task_id=task_id,
        status="processing",
        progress=0,
        message="Обработка запущена"
    )


@router.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(
    task_id: str,
    service: OCRComparisonService = Depends(get_ocr_service)
) -> StatusResponse:
    """
    Получить статус обработки документа.
    """
    task_info = service.get_task_status(task_id)
    
    if task_info['status'] == 'not_found':
        raise HTTPException(
            status_code=404,
            detail=f"Задача {task_id} не найдена"
        )
    
    # Определяем прогресс
    progress_map = {
        'pending': 0,
        'processing': 50,
        'completed': 100,
        'failed': 0
    }
    
    return StatusResponse(
        task_id=task_id,
        status=task_info['status'],
        progress=progress_map.get(task_info['status'], 0),
        message=task_info.get('message')
    )


@router.get("/results/{task_id}", response_model=ComparisonResponse)
async def get_results(
    task_id: str,
    include_html: bool = True,
    service: OCRComparisonService = Depends(get_ocr_service)
) -> ComparisonResponse:
    """
    Получить результаты сравнения OCR моделей.
    
    Args:
        task_id: ID задачи
        include_html: Включить HTML визуализацию (по умолчанию True)
    """
    task_info = service.get_task_status(task_id)
    
    if task_info['status'] == 'not_found':
        raise HTTPException(
            status_code=404,
            detail=f"Задача {task_id} не найдена"
        )
    
    if task_info['status'] != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Обработка еще не завершена. Статус: {task_info['status']}"
        )
    
    # Получаем результат из кэша задачи
    result = service.tasks[task_id].get('result')
    
    if not result:
        raise HTTPException(
            status_code=500,
            detail="Результаты не найдены"
        )
    
    # Добавляем HTML визуализацию если нужно
    if include_html and not result.html_visualization:
        try:
            html = HTMLVisualizer.generate_html(
                result.comparison,
                result.filename
            )
            result.html_visualization = html
        except Exception as e:
            logger.error(f"Ошибка генерации HTML: {e}")
    
    return result


@router.get("/compare/{task_id}/html")
async def get_html_visualization(
    task_id: str,
    service: OCRComparisonService = Depends(get_ocr_service)
):
    """
    Получить HTML визуализацию сравнения.
    Возвращает готовую HTML страницу для отображения в браузере.
    """
    from fastapi.responses import HTMLResponse
    
    task_info = service.get_task_status(task_id)
    
    if task_info['status'] != 'completed':
        return HTMLResponse(
            content="<h1>Обработка еще не завершена</h1>",
            status_code=400
        )
    
    result = service.tasks[task_id].get('result')
    
    if not result:
        return HTMLResponse(
            content="<h1>Результаты не найдены</h1>",
            status_code=404
        )
    
    # Генерируем HTML
    html = HTMLVisualizer.generate_html(
        result.comparison,
        result.filename
    )
    
    return HTMLResponse(content=html)


@router.delete("/task/{task_id}")
async def delete_task(
    task_id: str,
    service: OCRComparisonService = Depends(get_ocr_service)
):
    """
    Удалить задачу и связанные файлы.
    """
    # Удаляем файл
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    files = list(upload_dir.glob(f"{task_id}_*"))
    
    for file_path in files:
        try:
            file_path.unlink()
            logger.info(f"Удален файл: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка удаления файла {file_path}: {e}")
    
    # Удаляем из кэша задач
    if task_id in service.tasks:
        del service.tasks[task_id]
    
    return {"message": f"Задача {task_id} удалена"}


@router.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "service": "OCR Comparison API",
        "version": "1.0.0"
    }
