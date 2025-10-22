# Архитектура OCR Comparison Service

## Обзор системы

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web UI     │  │  REST API    │  │ Python SDK   │          │
│  │ (HTML/JS)    │  │   Client     │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Layer (routes.py)                  │  │
│  │  POST /upload  │ POST /process │ GET /status │ GET /results│
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                              │
│  ┌─────────────────────────┐  ┌────────────────────────────┐   │
│  │  OCRComparisonService   │  │  TextAlignmentService      │   │
│  │  - Оркестрация          │  │  - Посимвольное сравнение  │   │
│  │  - Параллелизация       │  │  - Алгоритмы выравнивания  │   │
│  │  - Кэширование          │  │  - Генерация метрик        │   │
│  └─────────────────────────┘  └────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OCR Provider Layer                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────┐│
│  │  PaddleOCR   │ │   Marker     │ │   MinerU     │ │  OLM   ││
│  │  Provider    │ │   Provider   │ │   Provider   │ │ (Mock) ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────┘│
└─────────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Utility Layer                            │
│  ┌────────────────────┐  ┌───────────────────────────────────┐ │
│  │  HTMLVisualizer    │  │  File Handler                     │ │
│  │  - HTML генерация  │  │  - Загрузка/сохранение            │ │
│  │  - CSS стилизация  │  │  - Конвертация форматов           │ │
│  └────────────────────┘  └───────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Компоненты системы

### 1. API Layer (`app/api/routes.py`)

**Ответственность:**
- Обработка HTTP запросов
- Валидация входных данных
- Маршрутизация запросов к сервисам
- Формирование HTTP ответов

**Endpoints:**
- `POST /api/upload` - загрузка файла
- `POST /api/process/{task_id}` - запуск обработки
- `GET /api/status/{task_id}` - проверка статуса
- `GET /api/results/{task_id}` - получение результатов
- `GET /api/compare/{task_id}/html` - HTML визуализация
- `DELETE /api/task/{task_id}` - удаление задачи
- `GET /api/health` - health check

### 2. Service Layer

#### OCRComparisonService (`app/services/comparison.py`)

**Ответственность:**
- Управление жизненным циклом задач
- Параллельный запуск OCR провайдеров
- Агрегация результатов
- Генерация статистики
- Кэширование результатов

**Ключевые методы:**
```python
async def initialize_providers() -> None
async def process_document(file_path, filename, task_id) -> ComparisonResponse
async def _run_all_ocr(file_path) -> List[RawOCRResult]
def get_task_status(task_id) -> dict
```

#### TextAlignmentService (`app/services/alignment.py`)

**Ответственность:**
- Посимвольное выравнивание текстов
- Определение типов расхождений
- Вычисление метрик точности
- Создание сегментов для визуализации

**Ключевые методы:**
```python
@staticmethod
def find_consensus_text(results) -> str
@staticmethod
def align_texts(reference, comparison, provider_name) -> List[DiffSegment]
@staticmethod
def merge_multiple_alignments(reference, all_results) -> List[DiffSegment]
@classmethod
def create_comparison_results(raw_results) -> List[ComparisonResult]
```

### 3. OCR Provider Layer (`app/models/`)

#### BaseOCRProvider (абстрактный)

**Интерфейс:**
```python
async def initialize() -> None
async def extract_text(file_path: str) -> str
async def process(file_path: str) -> Tuple[str, float]
def cleanup() -> None
def get_supported_formats() -> list[str]
```

#### Конкретные реализации:

1. **PaddleOCRProvider**
   - Универсальное распознавание
   - Поддержка PDF через конвертацию в изображения
   - Многоязычность

2. **MarkerOCRProvider**
   - Высокая скорость (25 стр/сек)
   - Конвертация в Markdown
   - Очистка разметки для сравнения

3. **MinerUOCRProvider**
   - Научные документы
   - Распознавание формул
   - Layout analysis

4. **OLMOCRProvider**
   - Mock реализация
   - Демонстрационные данные
   - Готов к замене на реальный API

### 4. Data Models (`app/models/schemas.py`)

**Pydantic модели для типобезопасности:**

```python
class RawOCRResult(BaseModel):
    provider_name: str
    text: str
    processing_time: float
    error: Optional[str]

class DiffSegment(BaseModel):
    text: str
    segment_type: Literal["match", "minor_diff", "major_diff"]
    start_position: int
    end_position: int
    providers_data: Dict[str, str]

class ComparisonResult(BaseModel):
    provider_name: str
    segments: List[DiffSegment]
    total_characters: int
    match_count: int
    diff_count: int
    accuracy_percent: float

class ComparisonResponse(BaseModel):
    task_id: str
    filename: str
    status: Literal["completed", "processing", "failed"]
    created_at: datetime
    raw_results: List[RawOCRResult]
    comparison: List[ComparisonResult]
    statistics: List[OCRStatistics]
    html_visualization: Optional[str]
```

### 5. Utility Layer

#### HTMLVisualizer (`app/utils/visualizer.py`)

**Ответственность:**
- Генерация HTML разметки
- CSS стилизация
- Цветовая подсветка расхождений
- Интерактивные tooltips

**Цветовая схема:**
- 🟢 Зеленый (`match`) - все модели согласны
- 🟡 Желтый (`minor_diff`) - 1-2 расхождения
- 🔴 Красный (`major_diff`) - 3+ расхождения

## Паттерны и принципы

### 1. Dependency Injection
```python
# FastAPI Depends для внедрения сервиса
def get_ocr_service() -> OCRComparisonService:
    return _ocr_service

@router.post("/process/{task_id}")
async def process(
    task_id: str,
    service: OCRComparisonService = Depends(get_ocr_service)
):
    ...
```

### 2. Abstract Factory
```python
class BaseOCRProvider(ABC):
    @abstractmethod
    async def extract_text(file_path: str) -> str:
        pass

# Конкретные фабрики
class PaddleOCRProvider(BaseOCRProvider):
    ...
```

### 3. Strategy Pattern
Каждый OCR провайдер - отдельная стратегия распознавания

### 4. Repository Pattern
`OCRComparisonService.tasks` - in-memory хранилище задач

### 5. Async/Await
Асинхронная обработка для параллелизма:
```python
tasks = [provider.process(file_path) for provider in self.providers]
results = await asyncio.gather(*tasks, return_exceptions=True)
```

## Обработка ошибок

### Уровни обработки:

1. **Provider Level**
   - Каждый провайдер ловит свои исключения
   - Возвращает `RawOCRResult` с `error` полем

2. **Service Level**
   - `asyncio.gather(..., return_exceptions=True)`
   - Продолжает работу даже если один провайдер упал

3. **API Level**
   - HTTP 400/404/500 статус коды
   - Структурированные сообщения об ошибках

## Масштабирование

### Текущие ограничения:
- In-memory хранилище задач (не персистентно)
- Синхронная обработка файлов
- Один воркер

### Пути улучшения:
1. **Task Queue**: Celery + Redis
2. **Persistent Storage**: PostgreSQL/MongoDB
3. **Object Storage**: S3/MinIO для файлов
4. **Horizontal Scaling**: Kubernetes + LoadBalancer
5. **Caching**: Redis для результатов

## Конфигурация

### Environment Variables:
```env
APP_HOST=0.0.0.0
APP_PORT=8000
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads
ENABLE_PADDLE=true
ENABLE_MARKER=true
ENABLE_MINERU=true
ENABLE_OLM=false
LOG_LEVEL=INFO
```

### Feature Flags:
Каждый OCR провайдер можно включить/выключить через `ENABLE_*`

## Мониторинг и логирование

### Логирование:
```python
logger = logging.getLogger(__name__)
logger.info(f"Обработка {task_id} завершена успешно")
logger.error(f"Ошибка обработки: {e}", exc_info=True)
```

### Метрики (будущее):
- Время обработки на провайдер
- Количество успешных/неуспешных задач
- Размер очереди задач
- Использование памяти/CPU

## Безопасность

### Текущие меры:
- Валидация типов файлов
- Ограничение размера файла (10MB)
- Временные файлы с уникальными ID
- Очистка временных файлов

### TODO:
- Rate limiting
- Authentication/Authorization
- File scanning (антивирус)
- Input sanitization
- HTTPS only в продакшене

## Производительность

### Оптимизации:
- Параллельная обработка OCR моделей
- Асинхронный I/O
- Lazy loading моделей
- Streaming для больших файлов (TODO)

### Бенчмарки (примерные):
- PaddleOCR: 1-3 сек/страница
- Marker: 0.04 сек/страница (25 стр/сек)
- MinerU: 2-5 сек/страница
- Общее время: max(провайдеры) + overhead (~10%)
