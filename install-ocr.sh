#!/bin/bash

# Скрипт установки опциональных OCR библиотек
# Marker, MinerU и OLMoCR - тяжёлые библиотеки

echo "🔧 Установка OCR библиотек..."
echo ""

# Активация виртуального окружения
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Виртуальное окружение не найдено. Запустите сначала ./run.sh"
    exit 1
fi

echo "Выберите библиотеку для установки:"
echo "1) Marker OCR (~2GB) - быстрая конвертация PDF"
echo "2) MinerU (~1GB) - документы с таблицами"
echo "3) OLMoCR (требует GPU 15GB+) - Vision Language Model"
echo "4) Все библиотеки"
echo "5) Выход"
echo ""
read -p "Ваш выбор (1-5): " choice

case $choice in
    1)
        echo "📦 Установка Marker OCR..."
        pip install marker-pdf
        echo "✓ Marker установлен"
        ;;
    2)
        echo "📦 Установка MinerU..."
        pip install "magic-pdf[full]"
        echo "✓ MinerU установлен"
        ;;
    3)
        echo "📦 Установка OLMoCR (GPU версия)..."
        echo "⚠️  Требуется CUDA 12.8+ и GPU 15GB+"
        read -p "Продолжить? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            pip install "olmocr[gpu]" --extra-index-url https://download.pytorch.org/whl/cu128
            echo "✓ OLMoCR установлен"
        else
            echo "Отменено"
        fi
        ;;
    4)
        echo "📦 Установка всех библиотек..."
        echo "Это займёт ~5-10 минут и ~4GB места"
        read -p "Продолжить? (y/n): " confirm
        if [ "$confirm" = "y" ]; then
            pip install marker-pdf
            pip install "magic-pdf[full]"
            echo "✓ Marker и MinerU установлены"
            echo ""
            echo "OLMoCR не установлен (требует GPU)"
            echo "Для установки запустите: pip install 'olmocr[gpu]'"
        else
            echo "Отменено"
        fi
        ;;
    5)
        echo "Выход"
        exit 0
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac

echo ""
echo "✅ Установка завершена!"
echo ""
echo "Обновите .env чтобы включить установленные модели:"
echo "  ENABLE_MARKER=true"
echo "  ENABLE_MINERU=true"
echo "  ENABLE_OLM=true"
echo ""
echo "Перезапустите сервер: ./run.sh"
