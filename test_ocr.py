#!/usr/bin/env python3
"""
Быстрый тест всех OCR провайдеров
"""
import asyncio
import sys
from pathlib import Path
import re

try:
    import pandas as pd  # Используем для парсинга HTML-таблиц
except Exception:  # не критично для других частей
    pd = None

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from app.models.paddle_ocr import PaddleOCRProvider
from app.models.marker_ocr import TesseractOCRProvider
from app.models.mineru_ocr import EasyOCRProvider


def _df_to_markdown(df) -> str:
    """Конвертация pandas.DataFrame в Markdown-таблицу без зависимости от tabulate.

    Формирует простую таблицу: заголовок из имен колонок, затем строки.
    """
    # Преобразуем все значения к строкам и заменяем переносы строк пробелами
    cols = [str(c).strip() for c in df.columns]
    rows = [[str(x).replace('\n', ' ').strip() for x in row] for row in df.astype(str).values.tolist()]

    # Ширина колонок = max(длина заголовка, длина любого значения)
    widths = [len(col) for col in cols]
    for r in rows:
        for i, cell in enumerate(r):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    def fmt_row(values):
        return "| " + " | ".join(v.ljust(widths[i]) for i, v in enumerate(values)) + " |"

    header = fmt_row(cols)
    separator = "| " + " | ".join("-" * w for w in widths) + " |"
    body = "\n".join(fmt_row(r) for r in rows)
    return "\n".join([header, separator, body])


def _html_table_to_markdown(html: str) -> str:
    """Парсит HTML с одной таблицей и возвращает Markdown-таблицу.

    Пытаемся использовать pandas.read_html (требует lxml). Если pandas недоступен
    или парсинг не удался — возвращаем исходный HTML как fallback.
    """
    if pd is None:
        return html
    try:
        # read_html вернет список таблиц; берем первую
        dfs = pd.read_html(html, header=0)
        if not dfs:
            return html
        df = dfs[0]
        # Если после парсинга колонок нет (редкий случай), пробуем без header
        if df.columns.tolist() == [0]:
            dfs2 = pd.read_html(html, header=None)
            if dfs2:
                df = dfs2[0]
                # Сформируем заголовки из первой строки
                if len(df) > 0:
                    df.columns = [str(x) for x in df.iloc[0].tolist()]
                    df = df.iloc[1:].reset_index(drop=True)
        return _df_to_markdown(df)
    except Exception:
        return html


def convert_tables_to_markdown(text: str) -> str:
    """Находит HTML-таблицы в тексте и преобразует их в Markdown-таблицы.

    Ищем теги <table ...>...</table> и точечно конвертируем содержимое.
    Сохраняем маркер [Таблица] перед блоком, если он уже есть в тексте.
    """
    # Поиск блоков <table>...</table> (включая переносы строк)
    pattern = re.compile(r"<table[\s\S]*?</table>", re.IGNORECASE)

    def repl(match):
        html_table = match.group(0)
        md = _html_table_to_markdown(html_table)
        return "\n" + md + "\n"

    # Иногда таблица обернута в <html><body>... — не страшно, pattern поймает <table>...
    return pattern.sub(repl, text)


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
        # Пост-обработка: конвертируем HTML-таблицы в Markdown для вывода в консоль
        text = convert_tables_to_markdown(text)
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
