# Changelog - OCR Comparison Service

## [2.0.0] - 2025-10-23 - MAJOR REFACTOR ✅

### 🔧 Критические изменения

**Замена нерабочих моделей на production-ready:**

1. **Marker → Tesseract OCR**
   - ❌ Проблема: Marker возвращал пустые результаты (CLI не работал)
   - ✅ Решение: Tesseract 5.3.4 - стабильная библиотека
   - Результат: **1465 символов** распознано корректно

2. **MinerU → EasyOCR**
   - ❌ Проблема: MinerU не мог найти выходные файлы
   - ✅ Решение: EasyOCR 1.7.2 - современная PyTorch модель
   - Результат: **1417 символов** распознано корректно

3. **Исправлен критический баг в alignment.py**
   - ❌ Проблема: Все провайдеры получали одинаковые `merged_segments`
   - ✅ Решение: Каждый провайдер получает уникальные segments
   - Результат: Корректная статистика и визуализация

### 📦 Технические детали

**Новые зависимости:**
```
pytesseract>=0.3.10
easyocr>=1.7.0
torch>=2.0.0 (CPU version)
```

**Конфигурация (.env):**
```bash
ENABLE_PADDLE=true      # PaddleOCR - 1014 chars
ENABLE_TESSERACT=true   # Tesseract - 1465 chars
ENABLE_EASYOCR=true     # EasyOCR - 1417 chars
```

**Размеры моделей:**
- PaddleOCR: ~200MB
- Tesseract: ~10MB (системная библиотека)
- EasyOCR: ~140MB (en+ru модели)
- **Итого: ~350MB**

### ✅ Тестирование

Все 3 провайдера успешно протестированы:
```bash
python test_ocr.py

📊 ИТОГИ:
  PaddleOCR       ✅ Работает (1014 chars)
  Tesseract       ✅ Работает (1465 chars)
  EasyOCR         ✅ Работает (1417 chars)
  
  Успешно: 3/3
```

### 🚀 Deployment

```bash
# Установка системных зависимостей
sudo apt-get install tesseract-ocr tesseract-ocr-rus poppler-utils

# Установка Python зависимостей
pip install -r requirements-minimal.txt

# Запуск сервера
./run.sh
```

### 📚 Документация

- `INSTALL.md` - Production-ready установка
- `test_ocr.py` - Быстрый тест всех провайдеров
- `README.md` - Обновлено описание моделей

### 🔗 Git

- Commit: `5d6cd95`
- Branch: `main`
- Repository: https://github.com/zalkarbek2023/-

---

## [1.0.0] - 2025-10-23 - Initial Release

### Первая версия

- PaddleOCR интеграция
- Marker CLI (не работал)
- MinerU CLI (не работал)
- Базовая HTML визуализация
- FastAPI сервер

### Проблемы

- Marker: 0 символов (таймауты)
- MinerU: 0 символов (файлы не найдены)
- Статистика показывала одинаковые данные
- DPI оптимизация для PaddleOCR
