"""
Главный файл FastAPI приложения для сравнения OCR моделей
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импорты приложения
from app.api.routes import router as api_router, set_ocr_service
from app.services.comparison import OCRComparisonService
from app.models.paddle_ocr import PaddleOCRProvider
from app.models.marker_ocr import MarkerOCRProvider
from app.models.mineru_ocr import MinerUOCRProvider
from app.models.deepseek_ocr import DeepSeekOCRProvider
from app.models.olmocr_provider import OLMoCRProvider


# Глобальный сервис
ocr_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения.
    Инициализация при старте, очистка при остановке.
    """
    global ocr_service
    
    logger.info("🚀 Запуск OCR Comparison Service...")
    
    # Создаем директории если не существуют
    upload_dir = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    upload_dir.mkdir(exist_ok=True)
    
    # Инициализация OCR провайдеров
    providers = []
    
    # Проверяем какие провайдеры включены
    if os.getenv("ENABLE_PADDLE", "true").lower() == "true":
        try:
            providers.append(PaddleOCRProvider())
            logger.info("✓ PaddleOCR включен")
        except Exception as e:
            logger.warning(f"✗ PaddleOCR не доступен: {e}")
    
    if os.getenv("ENABLE_MARKER", "true").lower() == "true":
        try:
            providers.append(MarkerOCRProvider())
            logger.info("✓ Marker OCR включен")
        except Exception as e:
            logger.warning(f"✗ Marker OCR не доступен: {e}")
    
    if os.getenv("ENABLE_MINERU", "true").lower() == "true":
        try:
            providers.append(MinerUOCRProvider())
            logger.info("✓ MinerU OCR включен")
        except Exception as e:
            logger.warning(f"✗ MinerU OCR не доступен: {e}")
    
    if os.getenv("ENABLE_DEEPSEEK", "false").lower() == "true":
        try:
            providers.append(DeepSeekOCRProvider())
            logger.info("✓ DeepSeek OCR включен")
        except Exception as e:
            logger.warning(f"✗ DeepSeek OCR не доступен: {e}")
    
    if os.getenv("ENABLE_OLM", "true").lower() == "true":
        try:
            providers.append(OLMoCRProvider())
            logger.info("✓ OLMoCR включен")
        except Exception as e:
            logger.warning(f"✗ OLMoCR не доступен: {e}")
    
    if not providers:
        logger.error("❌ Ни один OCR провайдер не доступен!")
        raise RuntimeError("Требуется хотя бы один OCR провайдер")
    
    # Создаем сервис сравнения
    ocr_service = OCRComparisonService(providers)
    
    # Инициализируем провайдеры
    try:
        await ocr_service.initialize_providers()
        logger.info(f"✓ Инициализировано {len(providers)} OCR провайдеров")
    except Exception as e:
        logger.error(f"Ошибка инициализации провайдеров: {e}")
    
    # Устанавливаем глобальный сервис для роутов
    set_ocr_service(ocr_service)
    
    logger.info("✓ Сервис готов к работе!")
    
    yield  # Приложение работает
    
    # Очистка при остановке
    logger.info("Остановка сервиса...")
    
    for provider in providers:
        try:
            provider.cleanup()
        except Exception as e:
            logger.error(f"Ошибка очистки {provider.provider_name}: {e}")
    
    logger.info("👋 Сервис остановлен")


# Создание FastAPI приложения
app = FastAPI(
    title="OCR Comparison Service",
    description="""
    Сервис для сравнения результатов распознавания текста 
    с использованием 5 различных OCR-моделей.
    
    ## Возможности:
    - Загрузка документов (PDF, изображения)
    - Обработка через 5 OCR моделей параллельно
    - Посимвольное выравнивание и сравнение
    - HTML визуализация с подсветкой расхождений
    - Детальная статистика по каждой модели
    
    ## OCR Модели:
    1. **PaddleOCR** - универсальная китайская модель
    2. **OLMoCR** - AllenAI Vision Language Model (GPU/API)
    3. **Marker** - быстрая конвертация PDF
    4. **MinerU** - документы с таблицами
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутов
app.include_router(api_router)

# Статические файлы (если есть)
static_dir = Path("./static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": "OCR Comparison API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "upload": "POST /api/upload",
            "process": "POST /api/process/{task_id}",
            "status": "GET /api/status/{task_id}",
            "results": "GET /api/results/{task_id}",
            "html": "GET /api/compare/{task_id}/html",
            "health": "GET /api/health"
        }
    }


@app.get("/info")
async def info():
    """Информация о сервисе и доступных провайдерах"""
    global ocr_service
    
    if not ocr_service:
        return {"error": "Сервис не инициализирован"}
    
    providers_info = []
    for provider in ocr_service.providers:
        providers_info.append({
            "name": provider.provider_name,
            "initialized": provider.is_initialized,
            "supported_formats": provider.get_supported_formats()
        })
    
    return {
        "service": "OCR Comparison Service",
        "version": "1.0.0",
        "providers": providers_info,
        "total_providers": len(ocr_service.providers),
        "upload_dir": os.getenv("UPLOAD_DIR", "./uploads"),
        "max_file_size": os.getenv("MAX_FILE_SIZE", "10MB"),
        "supported_formats": os.getenv("SUPPORTED_FORMATS", "pdf,png,jpg,jpeg,tiff")
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
