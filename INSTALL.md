# Установка OCR Comparison Service

## Production-Ready установка

### 1. Системные зависимости

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    poppler-utils \
    python3.12 \
    python3.12-venv \
    python3-pip

# Проверка установки
tesseract --version  # Должно быть 4.x или 5.x
tesseract --list-langs  # Должно показать: eng, rus, chi_sim, chi_tra
```

### 2. Python окружение

```bash
# Создание виртуального окружения
python3.12 -m venv venv
source venv/bin/activate

# Обновление pip
pip install --upgrade pip
```

### 3. Установка зависимостей

```bash
# Установка всех OCR библиотек
pip install -r requirements-minimal.txt

# Это установит:
# - PaddleOCR (универсальная модель)
# - Tesseract Python wrapper
# - EasyOCR (PyTorch модель)
# - FastAPI и все зависимости
```

### 4. Проверка установки

```bash
# Проверка PaddleOCR
python -c "import paddleocr; print('PaddleOCR OK')"

# Проверка Tesseract
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"

# Проверка EasyOCR
python -c "import easyocr; print('EasyOCR OK')"
```

### 5. Запуск сервера

```bash
# Простой запуск
./run.sh

# Или напрямую
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Размеры моделей

- **PaddleOCR**: ~200MB (автоматически загружается)
- **Tesseract**: ~10MB (уже установлен системно)
- **EasyOCR**: ~140MB для en+ru (загружается при первом использовании)

Общий размер: **~350MB**

## Минимальные требования

- **RAM**: 4GB (рекомендуется 8GB)
- **Диск**: 2GB свободного места
- **CPU**: 2 ядра (рекомендуется 4)
- **GPU**: Не требуется (все работает на CPU)

## Troubleshooting

### Tesseract не найден
```bash
# Проверьте путь
which tesseract

# Если не найден, установите:
sudo apt-get install tesseract-ocr
```

### EasyOCR ошибка PyTorch
```bash
# Установите CPU версию PyTorch
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### PaddlePaddle ошибки
```bash
# Переустановите CPU версию
pip uninstall paddlepaddle
pip install paddlepaddle==3.0.0
```
