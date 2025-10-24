"""
Утилита для генерации HTML визуализации с подсветкой расхождений
"""
from typing import List
from app.models.schemas import DiffSegment, ComparisonResult
import html
import re


class HTMLVisualizer:
    """
    Генератор HTML разметки для визуализации расхождений между OCR моделями.
    """
    
    # CSS стили для подсветки
    CSS_STYLES = """
    <style>
        .ocr-comparison {
            font-family: 'Courier New', monospace;
            line-height: 1.6;
            padding: 20px;
            background: #f5f5f5;
        }
        .provider-section {
            margin-bottom: 30px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .provider-name {
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 5px;
        }
        .segment {
            display: inline;
            padding: 2px 4px;
            border-radius: 3px;
        }
        .match {
            background-color: #28a745;
            color: #ffffff;
            font-weight: 500;
        }
        .minor-diff {
            background-color: #ffc107;
            color: #000000;
        }
        .major-diff {
            background-color: #dc3545;
            color: #ffffff;
        }
        .legend {
            margin: 20px 0;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .legend-item {
            display: inline-block;
            margin-right: 20px;
        }
        .legend-box {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 5px;
            vertical-align: middle;
            border-radius: 3px;
        }
        .stats {
            margin-top: 10px;
            font-size: 12px;
            color: #666;
        }
        /* Таблицы из PP-Structure */
        .table-block { margin: 10px 0; overflow-x: auto; }
        .table-block table { border-collapse: collapse; width: 100%; background: #fff; }
        .table-block th, .table-block td { border: 1px solid #ddd; padding: 6px 8px; font-family: system-ui, sans-serif; }
        .table-block thead th { background: #f0f0f0; font-weight: 600; }
        .table-caption { font-size: 13px; color: #333; margin: 6px 0; font-weight: 600; }
    </style>
    """
    
    @classmethod
    def generate_html(
        cls,
        comparison_results: List[ComparisonResult],
        filename: str
    ) -> str:
        """
        Генерирует полную HTML страницу с визуализацией.
        
        Args:
            comparison_results: Результаты сравнения от всех провайдеров
            filename: Имя обработанного файла
            
        Returns:
            str: HTML разметка
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='ru'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"<title>OCR Сравнение: {html.escape(filename)}</title>",
            cls.CSS_STYLES,
            "</head>",
            "<body>",
            "<div class='ocr-comparison'>",
            f"<h1>Сравнение OCR моделей</h1>",
            f"<p><strong>Документ:</strong> {html.escape(filename)}</p>",
            cls._generate_legend(),
        ]
        
        # Добавляем секции для каждого провайдера
        for result in comparison_results:
            html_parts.append(cls._generate_provider_section(result))
        
        html_parts.extend([
            "</div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)
    
    @classmethod
    def _generate_legend(cls) -> str:
        """Генерирует легенду с объяснением цветов"""
        return """
        <div class='legend'>
            <strong>Легенда:</strong>
            <div class='legend-item'>
                <span class='legend-box match'></span>
                <span>Совпадение (все модели согласны)</span>
            </div>
            <div class='legend-item'>
                <span class='legend-box minor-diff'></span>
                <span>Малое расхождение (1-2 модели отличаются)</span>
            </div>
            <div class='legend-item'>
                <span class='legend-box major-diff'></span>
                <span>Большое расхождение (3+ модели отличаются)</span>
            </div>
        </div>
        """
    
    @classmethod
    def _generate_provider_section(cls, result: ComparisonResult) -> str:
        """
        Генерирует секцию для одного провайдера.
        
        Args:
            result: Результат сравнения провайдера
            
        Returns:
            str: HTML разметка секции
        """
        # Заголовок секции
        html_parts = [
            "<div class='provider-section'>",
            f"<div class='provider-name'>{html.escape(result.provider_name)}</div>",
        ]
        
        # Текст с подсветкой
        html_parts.append("<div class='text-content'>")
        
        for segment in result.segments:
            cls_name = segment.segment_type.replace('_', '-')

            # Разбиваем текст на обычные части и HTML-таблицы, чтобы таблицы отрендерить, а текст экранировать
            html_parts.append(cls._render_segment_with_tables(segment, cls_name))
        
        html_parts.append("</div>")
        
        # Статистика
        stats_html = f"""
        <div class='stats'>
            Всего символов: {result.total_characters} | 
            Совпадений: {result.match_count} | 
            Различий: {result.diff_count} | 
            Точность: {result.accuracy_percent:.2f}%
        </div>
        """
        html_parts.append(stats_html)
        
        html_parts.append("</div>")
        
        return "\n".join(html_parts)

    @classmethod
    def _sanitize_table_html(cls, table_html: str) -> str:
        """Минимальная санитизация HTML таблицы: удаляем script/iframe и on* обработчики.
        Источник HTML — наш пайплайн, но дополнительная защита не повредит.
        """
        # Удаляем потенциально опасные теги
        table_html = re.sub(r"</?(script|iframe|object|embed)[^>]*>", "", table_html, flags=re.IGNORECASE)
        # Удаляем inline-обработчики событий вроде onclick="..."
        table_html = re.sub(r"\s+on[a-zA-Z]+\s*=\s*\"[^\"]*\"", "", table_html)
        table_html = re.sub(r"\s+on[a-zA-Z]+\s*=\s*'[^']*'", "", table_html)
        # Часто PP-Structure оборачивает <table> внутри <html><body> — убираем оболочку
        # Оставляем только первый <table>...</table>
        m = re.search(r"<table[\s\S]*?</table>", table_html, flags=re.IGNORECASE)
        if m:
            table_html = m.group(0)
        return table_html

    @classmethod
    def _render_segment_with_tables(cls, segment: DiffSegment, cls_name: str) -> str:
        """Рендер сегмента так, чтобы таблицы отображались, а обычный текст подсвечивался и экранировался."""
        text = segment.text or ""
        tooltip = cls._generate_tooltip(segment)

        parts: List[str] = []
        pattern = re.compile(r"<table[\s\S]*?</table>|<html[\s\S]*?<table[\s\S]*?</table>[\s\S]*?</html>", re.IGNORECASE)
        last = 0
        for m in pattern.finditer(text):
            # Обычный текст до таблицы
            if m.start() > last:
                plain = text[last:m.start()]
                # Заменяем маркер [Таблица] на подпись
                plain = plain.replace("[Таблица]", "")
                escaped = html.escape(plain)
                if escaped:
                    parts.append(
                        f"<span class='segment {cls_name}' title='{tooltip}'>" f"{escaped}" f"</span>"
                    )
            # Вставляем таблицу (санитизируем и без экранирования)
            table_html = cls._sanitize_table_html(m.group(0))
            if table_html:
                parts.append("<div class='table-caption'>Таблица</div>")
                parts.append(f"<div class='table-block'>{table_html}</div>")
            last = m.end()

        # Хвост после последней таблицы
        if last < len(text):
            tail = text[last:]
            tail = tail.replace("[Таблица]", "")
            escaped_tail = html.escape(tail)
            if escaped_tail:
                parts.append(
                    f"<span class='segment {cls_name}' title='{tooltip}'>" f"{escaped_tail}" f"</span>"
                )

        # Если таблиц не было вовсе — обычная логика
        if not parts:
            escaped_text = html.escape(text)
            return (
                f"<span class='segment {cls_name}' title='{tooltip}'>"
                f"{escaped_text}"
                f"</span>"
            )

        return "".join(parts)
    
    @classmethod
    def _generate_tooltip(cls, segment: DiffSegment) -> str:
        """
        Генерирует текст tooltip для сегмента.
        
        Args:
            segment: Сегмент текста
            
        Returns:
            str: Текст tooltip
        """
        if segment.segment_type == 'match':
            return "Все модели согласны"
        
        # Показываем различия между провайдерами
        providers_info = []
        for provider, text in segment.providers_data.items():
            escaped = html.escape(text or '[пусто]')
            providers_info.append(f"{provider}: {escaped}")
        
        return " | ".join(providers_info)
    
    @classmethod
    def generate_simple_comparison_table(
        cls,
        comparison_results: List[ComparisonResult]
    ) -> str:
        """
        Генерирует простую таблицу сравнения (альтернативный вид).
        
        Args:
            comparison_results: Результаты сравнения
            
        Returns:
            str: HTML таблица
        """
        html_parts = [
            "<table border='1' style='border-collapse: collapse; width: 100%;'>",
            "<thead>",
            "<tr>",
            "<th>Провайдер</th>",
            "<th>Символов</th>",
            "<th>Совпадений</th>",
            "<th>Различий</th>",
            "<th>Точность</th>",
            "</tr>",
            "</thead>",
            "<tbody>"
        ]
        
        for result in comparison_results:
            html_parts.append(f"""
            <tr>
                <td>{html.escape(result.provider_name)}</td>
                <td>{result.total_characters}</td>
                <td>{result.match_count}</td>
                <td>{result.diff_count}</td>
                <td>{result.accuracy_percent:.2f}%</td>
            </tr>
            """)
        
        html_parts.append("</tbody></table>")
        
        return "\n".join(html_parts)
