# OCR Comparison Service

Веб-сервис для сравнения результатов распознавания текста с использованием 4 различных OCR-моделей с посимвольным выравниванием и визуализацией расхождений.

## 🎯 Возможности

- ✅ Загрузка документов (PDF, PNG, JPG, JPEG, TIFF)
- ✅ Параллельная обработка через 4 OCR модели
- ✅ Посимвольное выравнивание результатов
- ✅ HTML визуализация с цветовой подсветкой расхождений
- ✅ Детальная статистика по каждой модели
- ✅ REST API для интеграции

## 🤖 OCR Модели

1. **PaddleOCR** (59.2k ⭐) - универсальная китайская модель
2. **OLMoCR** (~1.5k ⭐) - AllenAI Vision Language Model (GPU/API)
3. **Marker** (29.3k ⭐) - быстрая конвертация PDF (25 стр/сек)
4. **MinerU** (46.9k ⭐) - документы с таблицами и формулами

## 📦 Быстрый старт

```bash
# 1. Запустить сервер (автоматическая установка зависимостей)
./run.sh

# 2. Открыть в браузере
http://localhost:8000/static/index.html

# 3. Загрузить PDF и получить результаты от всех 4 моделей
```

Сервер будет доступен по адресу: `http://localhost:8000`

## 🚀 Использование

### Web UI

Откройте в браузере: `http://localhost:8000/static/index.html`

### API Документация

Swagger UI: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

### Примеры API запросов

#### 1. Загрузка файла

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

Ответ:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "document.pdf",
  "message": "Файл успешно загружен..."
}
```

#### 2. Запуск обработки

```bash
curl -X POST "http://localhost:8000/api/process/{task_id}"
```

#### 3. Проверка статуса

```bash
curl -X GET "http://localhost:8000/api/status/{task_id}"
```

#### 4. Получение результатов

```bash
curl -X GET "http://localhost:8000/api/results/{task_id}"
```

#### 5. HTML визуализация

Откройте в браузере: `http://localhost:8000/api/compare/{task_id}/html`

## 📊 Формат ответа

```json
{
  "task_id": "uuid",
  "filename": "document.pdf",
  "status": "completed",
  "created_at": "2025-10-22T10:30:00",
  "raw_results": [
    {
      "provider_name": "PaddleOCR",
      "text": "Распознанный текст...",
      "processing_time": 1.234,
      "error": null
    }
  ],
  "comparison": [
    {
      "provider_name": "PaddleOCR",
      "segments": [...],
      "total_characters": 1000,
      "match_count": 950,
      "diff_count": 50,
      "accuracy_percent": 95.0
    }
  ],
  "statistics": [
    {
      "provider_name": "PaddleOCR",
      "total_chars": 1000,
      "differences": 50,
      "accuracy": 95.0,
      "processing_time": 1.234
    }
  ]
}
```

## 🎨 Цветовая подсветка

- 🟢 **Зеленый** - все модели согласны (match)
- 🟡 **Желтый** - минорные расхождения (1-2 модели)
- 🔴 **Красный** - мажорные расхождения (3+ модели)

## ⚙️ Конфигурация

Файл `.env`:

```env
# Сервер
APP_HOST=0.0.0.0
APP_PORT=8000

# Файлы
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIR=./uploads

# OCR модели (включить/выключить)
ENABLE_PADDLE=true
ENABLE_MARKER=true
ENABLE_MINERU=true
ENABLE_OLM=false

# Логирование
LOG_LEVEL=INFO
```

## 🔧 Разработка

### Структура проекта

```
TASK-1/
├── app/
│   ├── models/          # OCR провайдеры
│   │   ├── base_provider.py
│   │   ├── paddle_ocr.py
│   │   ├── marker_ocr.py
│   │   ├── mineru_ocr.py
│   │   └── olm_ocr.py
│   ├── services/        # Бизнес-логика
│   │   ├── alignment.py
│   │   └── comparison.py
│   ├── api/             # API endpoints
│   │   └── routes.py
│   └── utils/           # Утилиты
│       └── visualizer.py
├── static/              # Фронтенд
├── uploads/             # Загруженные файлы
├── main.py              # Точка входа
├── requirements.txt     # Зависимости
└── .env                 # Конфигурация
```

### Добавление нового OCR провайдера

1. Создать класс наследник `BaseOCRProvider`
2. Реализовать методы `initialize()` и `extract_text()`
3. Добавить в `main.py` при инициализации
4. Включить в `.env`

## 📝 Лицензии OCR моделей

- **PaddleOCR**: Apache 2.0
- **Marker**: Custom (<$2M revenue OK)
- **MinerU**: AGPL-3.0

## 🐛 Известные ограничения

- OLM OCR работает в режиме заглушки (требуется API)
- Максимальный размер файла: 10MB
- PDF обрабатываются последовательно (страница за страницей)
- В памяти хранятся только текущие задачи (не персистентно)

## 🤝 Вклад в проект

Приветствуются pull requests и issues!

## 📧 Контакты

Для вопросов и предложений создавайте issue в репозитории.

---

**Версия**: 1.0.0  
**Дата**: Октябрь 2025
