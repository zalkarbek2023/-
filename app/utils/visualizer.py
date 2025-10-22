"""
Утилита для генерации HTML визуализации с подсветкой расхождений
"""
from typing import List
from app.models.schemas import DiffSegment, ComparisonResult
import html


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
            escaped_text = html.escape(segment.text)
            
            # Добавляем tooltip с информацией от разных провайдеров
            tooltip = cls._generate_tooltip(segment)
            
            html_parts.append(
                f"<span class='segment {cls_name}' title='{tooltip}'>"
                f"{escaped_text}"
                f"</span>"
            )
        
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
