#!/bin/bash
# Production Quick Start Guide
# OCR Comparison Service v2.0

echo "🚀 OCR Comparison Service - Production Setup"
echo "================================================"
echo ""

# 1. Проверка системных зависимостей
echo "📋 Шаг 1/4: Проверка системных зависимостей..."

if ! command -v tesseract &> /dev/null; then
    echo "❌ Tesseract не установлен"
    echo "   Установите: sudo apt-get install tesseract-ocr tesseract-ocr-rus"
    exit 1
else
    echo "✅ Tesseract $(tesseract --version | head -n1)"
fi

if ! command -v pdftoppm &> /dev/null; then
    echo "❌ poppler-utils не установлен"
    echo "   Установите: sudo apt-get install poppler-utils"
    exit 1
else
    echo "✅ poppler-utils установлен"
fi

# 2. Python окружение
echo ""
echo "📋 Шаг 2/4: Проверка Python окружения..."

if [ ! -d "venv" ]; then
    echo "⚠️  Виртуальное окружение не найдено"
    echo "   Создаю venv..."
    python3.12 -m venv venv
fi

source venv/bin/activate
echo "✅ Python: $(python --version)"

# 3. Установка зависимостей
echo ""
echo "📋 Шаг 3/4: Установка зависимостей..."

if ! python -c "import easyocr" &> /dev/null; then
    echo "⚙️  Установка EasyOCR и зависимостей..."
    pip install -q pytesseract easyocr torch torchvision --index-url https://download.pytorch.org/whl/cpu
    echo "✅ Зависимости установлены"
else
    echo "✅ Все зависимости уже установлены"
fi

# 4. Тест
echo ""
echo "📋 Шаг 4/4: Быстрый тест..."

if [ -z "$(ls -A uploads/*.pdf 2>/dev/null)" ]; then
    echo "⚠️  Нет тестовых PDF файлов в uploads/"
    echo "   Загрузите тестовый файл через веб-интерфейс"
else
    echo "🧪 Запуск тестов..."
    python test_ocr.py
fi

echo ""
echo "================================================"
echo "✅ Настройка завершена!"
echo ""
echo "🌐 Запустить сервер:"
echo "   ./run.sh"
echo ""
echo "📖 Документация:"
echo "   - INSTALL.md - Подробная установка"
echo "   - CHANGELOG.md - История изменений"
echo "   - README.md - Общее описание"
echo ""
echo "🔗 GitHub: https://github.com/zalkarbek2023/-"
echo "================================================"
