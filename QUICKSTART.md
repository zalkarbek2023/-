# 🚀 Быстрый старт

## Минимальные требования

- Python 3.9+
- 4GB RAM
- 2GB свободного места на диске

## Установка и запуск

### Вариант 1: Автоматический запуск (Linux/Mac)

```bash
./run.sh
```

### Вариант 2: Ручная установка

```bash
# 1. Создать виртуальное окружение
python3 -m venv venv

# 2. Активировать
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Запустить
python main.py
```

### Вариант 3: Docker

```bash
# Собрать и запустить
docker-compose up --build

# Остановить
docker-compose down
```

## Использование

После запуска откройте в браузере:

- **Web UI**: http://localhost:8000/static/index.html
- **API Docs**: http://localhost:8000/docs
- **API**: http://localhost:8000/api/

## Первый тест

### Через Web UI:

1. Откройте http://localhost:8000/static/index.html
2. Нажмите "Выбрать файл"
3. Загрузите PDF или изображение
4. Нажмите "Начать обработку"
5. Дождитесь результатов
6. Нажмите "Открыть HTML визуализацию"

### Через API:

```bash
# 1. Загрузить файл
curl -X POST "http://localhost:8000/api/upload" \
  -F "file=@test.pdf"

# Ответ содержит task_id

# 2. Запустить обработку
curl -X POST "http://localhost:8000/api/process/{task_id}"

# 3. Проверить статус
curl "http://localhost:8000/api/status/{task_id}"

# 4. Получить результаты
curl "http://localhost:8000/api/results/{task_id}"

# 5. Открыть HTML визуализацию
open "http://localhost:8000/api/compare/{task_id}/html"
```

## Включение/отключение OCR моделей

Отредактируйте `.env`:

```env
ENABLE_PADDLE=true   # PaddleOCR
ENABLE_MARKER=true   # Marker
ENABLE_MINERU=true   # MinerU
ENABLE_OLM=false     # OLM (mock)
```

## Решение проблем

### Ошибка импорта библиотек

```bash
# Переустановить зависимости
pip install -r requirements.txt --force-reinstall
```

### Недостаточно памяти

Уменьшите количество активных моделей в `.env`

### Медленная обработка

- Используйте GPU если доступен
- Уменьшите разрешение изображений
- Отключите неиспользуемые модели

## Дополнительная информация

См. полную документацию в `README.md`
