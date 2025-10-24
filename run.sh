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

# Базовая установка (CPU путь по умолчанию)
pip install paddlepaddle==3.0.0 || echo "⚠️  PaddlePaddle (CPU) не установлен"
pip install paddleocr || echo "⚠️  PaddleOCR не установлен"

# Если есть GPU и доступен nvidia-smi, пробуем переключиться на GPU Paddle
if command -v nvidia-smi &> /dev/null || [ "${FORCE_PADDLE_GPU,,}" = "true" ]; then
    echo "🧠 Обнаружен GPU (nvidia-smi). Пробуем установить paddlepaddle-gpu..."
    # Проверяем, собран ли Paddle с CUDA
    PY_HAS_CUDA=$(python3 - << 'EOF'
try:
        import paddle
        print('true' if paddle.is_compiled_with_cuda() else 'false')
except Exception:
        print('false')
EOF
)
    if [ "$PY_HAS_CUDA" != "true" ]; then
        echo "↪️  Текущая сборка Paddle без CUDA. Переключаемся на GPU-сборку..."
        pip uninstall -y paddlepaddle >/dev/null 2>&1 || true
        # Пытаемся установить универсальное колесо GPU 3.0.0 (может потребовать post-метку под вашу CUDA)
        if ! pip install paddlepaddle-gpu==3.0.0; then
            echo "⚠️  Не удалось автоматически установить paddlepaddle-gpu==3.0.0"
            echo "👉 Подсказка: выберите колесо под вашу CUDA версию (например, 11.8 → post118)"
            echo "   Примеры:
     pip install paddlepaddle-gpu==3.0.0.post118  # CUDA 11.8
     pip install paddlepaddle-gpu==3.0.0.post200  # CUDA 12.0/12.1"
        else
            echo "✅ Установлен paddlepaddle-gpu"
        fi
    else
        echo "✅ Paddle уже собран с CUDA"
    fi
fi

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
