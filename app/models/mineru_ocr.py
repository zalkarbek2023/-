"""
MinerU OCR провайдер
"""
from .base_provider import BaseOCRProvider
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MinerUOCRProvider(BaseOCRProvider):
    """
    Провайдер для MinerU OCR.
    Оптимизирован для документов с таблицами и сложной структурой.
    """
    
    def __init__(self):
        super().__init__("MinerU")
    
    async def initialize(self) -> None:
        """Инициализация MinerU"""
        try:
            # Проверяем доступность magic-pdf CLI
            import subprocess
            result = subprocess.run(
                ['magic-pdf', '--help'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"{self.provider_name}: CLI готов")
            else:
                raise ImportError("magic-pdf CLI не доступен")
            
        except Exception as e:
            logger.error(f"{self.provider_name}: MinerU не установлен")
            raise ImportError(
                "MinerU не установлен. Установите: pip install magic-pdf[full]"
            ) from e
    
    async def extract_text(self, file_path: str) -> str:
        """
        Извлекает текст из PDF используя MinerU CLI
        
        Args:
            file_path: Путь к PDF файлу
            
        Returns:
            str: Распознанный текст в Markdown формате
        """
        import subprocess
        import tempfile
        
        path = Path(file_path)
        
        if path.suffix.lower() != '.pdf':
            raise ValueError(f"{self.provider_name}: Поддерживает только PDF файлы")
        
        try:
            # Создаём временную директорию для результатов
            with tempfile.TemporaryDirectory() as tmpdir:
                tmpdir_path = Path(tmpdir)
                
                # Запускаем magic-pdf CLI
                cmd = [
                    'magic-pdf',
                    '-p', str(path),
                    '-o', tmpdir,
                    '-m', 'auto'  # auto выбирает лучший метод (ocr/txt)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 минут таймаут
                )
                
                if result.returncode != 0:
                    logger.error(f"{self.provider_name}: Ошибка CLI: {result.stderr}")
                    # Не падаем сразу, пробуем найти результат
                
                # MinerU создаёт структуру: tmpdir/filename_without_ext/auto/*.md
                pdf_name = path.stem
                
                # Пробуем разные варианты путей
                possible_paths = [
                    tmpdir_path / pdf_name / 'auto',
                    tmpdir_path / 'auto',
                    tmpdir_path
                ]
                
                md_files = []
                for search_path in possible_paths:
                    if search_path.exists():
                        md_files = list(search_path.glob('**/*.md'))
                        if md_files:
                            logger.info(f"{self.provider_name}: Найдено {len(md_files)} файлов в {search_path}")
                            break
                if not md_files:
                    # Логируем структуру директории для отладки
                    logger.warning(f"{self.provider_name}: Markdown файл не найден")
                    logger.info(f"{self.provider_name}: Содержимое {tmpdir}:")
                    for item in tmpdir_path.rglob('*'):
                        logger.info(f"  {item.relative_to(tmpdir_path)}")
                    logger.info(f"{self.provider_name}: stdout: {result.stdout[-500:]}")
                    logger.info(f"{self.provider_name}: stderr: {result.stderr[-500:]}")
                    return ""
                
                # Читаем первый найденный файл
                full_text = md_files[0].read_text()
                
                if not full_text.strip():
                    logger.warning(f"{self.provider_name}: Пустой результат для {file_path}")
                    return ""
                
                return full_text.strip()
            
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка обработки: {e}")
            raise
