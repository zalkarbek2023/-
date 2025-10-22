#!/bin/bash

# Скрипт быстрого запуска OCR Comparison Service

echo "🚀 Запуск OCR Comparison Service..."
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не установлен. Установите Python 3.9 или выше."
    exit 1
fi

echo "✓ Python найден: $(python3 --version)"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
echo "🔧 Активация виртуального окружения..."
source venv/bin/activate

# Установка зависимостей
echo "📥 Установка зависимостей..."
pip install --upgrade pip

# Сначала устанавливаем базовые зависимости
echo "📦 Установка базовых зависимостей..."
pip install -r requirements-minimal.txt

# Затем пытаемся установить OCR библиотеки
echo "🔧 Установка OCR библиотек (может занять время)..."
pip install paddlepaddle==3.0.0 || echo "⚠️  PaddlePaddle не установлен (не критично)"
pip install paddleocr || echo "⚠️  PaddleOCR не установлен (не критично)"

echo "✓ Базовые зависимости установлены"
echo "ℹ️  Marker, MinerU и OLMoCR можно установить позже при необходимости"
echo "   Запустите: ./install-ocr.sh"

# Создание необходимых директорий
echo "📁 Создание директорий..."
mkdir -p uploads static

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Создаю с настройками по умолчанию..."
    cat > .env << EOF
APP_HOST=0.0.0.0
APP_PORT=8000
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads
SUPPORTED_FORMATS=pdf,png,jpg,jpeg,tiff
OCR_TIMEOUT=300
ENABLE_PADDLE=true
ENABLE_MARKER=true
ENABLE_MINERU=true
ENABLE_OLM=false
LOG_LEVEL=INFO
EOF
fi

echo ""
echo "✅ Подготовка завершена!"
echo ""
echo "🌐 Запуск сервера..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   UI: http://localhost:8000/static/index.html"
echo ""
echo "Нажмите Ctrl+C для остановки"
echo ""

# Запуск приложения
uvicorn main:app --host 0.0.0.0 --port 8000
