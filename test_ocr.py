#!/usr/bin/env python3
"""
Быстрый тест всех OCR провайдеров
"""
import asyncio
import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from app.models.paddle_ocr import PaddleOCRProvider
from app.models.marker_ocr import TesseractOCRProvider
from app.models.mineru_ocr import EasyOCRProvider


async def test_provider(provider, test_file: str):
    """Тест одного провайдера"""
    print(f"\n{'='*60}")
    print(f"Тестируем: {provider.provider_name}")
    print(f"{'='*60}")
    
    try:
        # Инициализация
        print("  [1/3] Инициализация...", end=" ", flush=True)
        await provider.initialize()
        print("✅")
        
        # Извлечение текста
        print("  [2/3] Распознавание текста...", end=" ", flush=True)
        text = await provider.extract_text(test_file)
        print("✅")
        
        # Результаты
        print("  [3/3] Результат:")
        print(f"    - Символов: {len(text)}")
        print(f"    - Строк: {len(text.splitlines())}")
        print(f"    - Первые 200 символов:")
        print(f"      {text[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА")
        print(f"    {type(e).__name__}: {e}")
        return False


async def main():
    """Главная функция теста"""
    print("🧪 OCR Comparison Service - Тест провайдеров")
    print("=" * 60)
    
    # Проверяем тестовый файл
    test_files = list(Path("uploads").glob("*.pdf"))
    if not test_files:
        print("❌ Нет PDF файлов в папке uploads/")
        print("   Загрузите тестовый файл через веб-интерфейс")
        return
    
    test_file = str(test_files[0])
    print(f"📄 Тестовый файл: {test_file}")
    
    # Тестируем провайдеры
    providers = [
        PaddleOCRProvider(),
        TesseractOCRProvider(),
        EasyOCRProvider()
    ]
    
    results = {}
    for provider in providers:
        success = await test_provider(provider, test_file)
        results[provider.provider_name] = success
    
    # Итоги
    print(f"\n{'='*60}")
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print(f"{'='*60}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for name, success in results.items():
        status = "✅ Работает" if success else "❌ Ошибка"
        print(f"  {name:15} {status}")
    
    print(f"\n  Успешно: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n✅ Все провайдеры работают корректно!")
        return 0
    else:
        print("\n⚠️  Некоторые провайдеры не работают")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
