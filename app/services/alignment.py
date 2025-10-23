"""
Сервис для посимвольного выравнивания и сравнения текстов от разных OCR моделей
"""
import difflib
from typing import List, Dict, Tuple
from collections import Counter
import logging

from app.models.schemas import RawOCRResult, DiffSegment, ComparisonResult

logger = logging.getLogger(__name__)


class TextAlignmentService:
    """
    Сервис для выравнивания и сравнения текстов от разных OCR провайдеров.
    Использует алгоритм Longest Common Subsequence (LCS) из difflib.
    """
    
    @staticmethod
    def find_consensus_text(results: List[RawOCRResult]) -> str:
        """
        Находит консенсусный текст (наиболее частую версию).
        Используется как референс для сравнения.
        
        Args:
            results: Список результатов от OCR провайдеров
            
        Returns:
            str: Консенсусный текст (самый длинный или наиболее частый)
        """
        if not results:
            return ""
        
        # Простая эвристика: берем самый длинный текст как референс
        # (обычно более полный)
        texts = [r.text for r in results if r.text]
        
        if not texts:
            return ""
        
        # Сортируем по длине и берем самый длинный
        reference = max(texts, key=len)
        
        logger.debug(f"Выбран референсный текст длиной {len(reference)} символов")
        
        return reference
    
    @staticmethod
    def align_texts(
        reference: str,
        comparison: str,
        provider_name: str
    ) -> List[DiffSegment]:
        """
        Выравнивает два текста и создает сегменты с разметкой различий.
        
        Args:
            reference: Референсный текст
            comparison: Текст для сравнения
            provider_name: Название провайдера
            
        Returns:
            List[DiffSegment]: Список сегментов с информацией о различиях
        """
        segments = []
        
        # Используем SequenceMatcher для посимвольного сравнения
        matcher = difflib.SequenceMatcher(None, reference, comparison)
        
        position = 0
        
        # Получаем операции выравнивания
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Совпадающий сегмент
                text = reference[i1:i2]
                segments.append(DiffSegment(
                    text=text,
                    segment_type='match',
                    start_position=position,
                    end_position=position + len(text),
                    providers_data={
                        'reference': text,
                        provider_name: comparison[j1:j2]
                    }
                ))
                position += len(text)
                
            elif tag == 'replace':
                # Замена символов - различие
                ref_text = reference[i1:i2]
                comp_text = comparison[j1:j2]
                
                segments.append(DiffSegment(
                    text=ref_text,
                    segment_type='major_diff',
                    start_position=position,
                    end_position=position + len(ref_text),
                    providers_data={
                        'reference': ref_text,
                        provider_name: comp_text
                    }
                ))
                position += len(ref_text)
                
            elif tag == 'delete':
                # Символы есть в reference, но нет в comparison
                ref_text = reference[i1:i2]
                
                segments.append(DiffSegment(
                    text=ref_text,
                    segment_type='minor_diff',
                    start_position=position,
                    end_position=position + len(ref_text),
                    providers_data={
                        'reference': ref_text,
                        provider_name: ''
                    }
                ))
                position += len(ref_text)
                
            elif tag == 'insert':
                # Символы есть в comparison, но нет в reference
                # Пропускаем или отмечаем как вставку
                comp_text = comparison[j1:j2]
                
                segments.append(DiffSegment(
                    text='',
                    segment_type='minor_diff',
                    start_position=position,
                    end_position=position,
                    providers_data={
                        'reference': '',
                        provider_name: comp_text
                    }
                ))
        
        return segments
    
    @staticmethod
    def merge_multiple_alignments(
        reference: str,
        all_results: List[RawOCRResult]
    ) -> List[DiffSegment]:
        """
        Объединяет выравнивания от всех провайдеров.
        Создает общие сегменты с данными от каждого провайдера.
        
        Args:
            reference: Референсный текст
            all_results: Результаты от всех провайдеров
            
        Returns:
            List[DiffSegment]: Объединенные сегменты
        """
        # Сначала создаем базовые сегменты на основе референсного текста
        # Затем для каждого провайдера добавляем его версию
        
        merged_segments = []
        
        # Для простоты: разбиваем на строки и сравниваем построчно
        ref_lines = reference.split('\n')
        
        for line_idx, ref_line in enumerate(ref_lines):
            # Собираем версии этой строки от всех провайдеров
            providers_data = {'reference': ref_line}
            
            # Определяем тип сегмента
            all_equal = True
            
            for result in all_results:
                text_lines = result.text.split('\n')
                
                if line_idx < len(text_lines):
                    comp_line = text_lines[line_idx]
                else:
                    comp_line = ''
                
                providers_data[result.provider_name] = comp_line
                
                if comp_line != ref_line:
                    all_equal = False
            
            # Определяем тип различия
            unique_versions = len(set(providers_data.values()))
            
            if all_equal or unique_versions == 1:
                segment_type = 'match'
            elif unique_versions <= 2:
                segment_type = 'minor_diff'
            else:
                segment_type = 'major_diff'
            
            merged_segments.append(DiffSegment(
                text=ref_line,
                segment_type=segment_type,
                start_position=line_idx,
                end_position=line_idx + 1,
                providers_data=providers_data
            ))
        
        return merged_segments
    
    @staticmethod
    def calculate_accuracy(
        segments: List[DiffSegment],
        total_chars: int
    ) -> Tuple[int, int, float]:
        """
        Вычисляет метрики точности.
        
        Args:
            segments: Список сегментов
            total_chars: Общее количество символов
            
        Returns:
            Tuple[int, int, float]: (совпадения, различия, процент точности)
        """
        match_count = 0
        diff_count = 0
        
        for segment in segments:
            if segment.segment_type == 'match':
                match_count += len(segment.text)
            else:
                diff_count += len(segment.text)
        
        if total_chars == 0:
            accuracy = 0.0
        else:
            accuracy = (match_count / total_chars) * 100
        
        return match_count, diff_count, accuracy
    
    @classmethod
    def create_comparison_results(
        cls,
        raw_results: List[RawOCRResult]
    ) -> List[ComparisonResult]:
        """
        Создает полные результаты сравнения для всех провайдеров.
        
        Args:
            raw_results: Сырые результаты от OCR провайдеров
            
        Returns:
            List[ComparisonResult]: Результаты с сегментами и метриками
        """
        if not raw_results:
            return []
        
        # Находим консенсусный текст (самый длинный)
        reference = cls.find_consensus_text(raw_results)
        
        # Создаем результаты для каждого провайдера ОТДЕЛЬНО
        comparison_results = []
        
        for result in raw_results:
            # ВАЖНО: создаем УНИКАЛЬНЫЕ segments для каждого провайдера
            provider_segments = cls.align_texts(
                reference=reference,
                comparison=result.text,
                provider_name=result.provider_name
            )
            
            # Вычисляем метрики на основе СОБСТВЕННЫХ сегментов провайдера
            total_chars = len(result.text)
            match_count, diff_count, accuracy = cls.calculate_accuracy(
                provider_segments,
                len(reference)  # Используем длину референса для корректного расчета
            )
            
            comparison_results.append(ComparisonResult(
                provider_name=result.provider_name,
                segments=provider_segments,  # УНИКАЛЬНЫЕ сегменты
                total_characters=total_chars,  # РЕАЛЬНОЕ количество символов
                match_count=match_count,
                diff_count=diff_count,
                accuracy_percent=accuracy
            ))
            
            logger.debug(
                f"{result.provider_name}: {total_chars} символов, "
                f"{match_count} совпадений, {diff_count} различий, "
                f"{accuracy:.2f}% точность"
            )
        
        logger.info(f"Создано {len(comparison_results)} результатов сравнения")
        
        return comparison_results
