"""
Marker OCR провайдер
"""
from .base_provider import BaseOCRProvider
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MarkerOCRProvider(BaseOCRProvider):
    """
    Провайдер для Marker OCR.
    Оптимизирован для научных статей, PDF с формулами и таблицами.
    """
    
    def __init__(self):
        super().__init__("Marker")
    
    async def initialize(self) -> None:
        """Инициализация Marker"""
        try:
            # Проверяем доступность marker CLI
            import subprocess
            result = subprocess.run(
                ['marker_single', '--help'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"{self.provider_name}: CLI готов")
            else:
                raise ImportError("marker_single CLI не доступен")
            
        except Exception as e:
            logger.error(f"{self.provider_name}: Marker не установлен")
            raise ImportError(
                "Marker не установлен. Установите: pip install marker-pdf"
            ) from e
    
    async def extract_text(self, file_path: str) -> str:
        """
        Извлекает текст из PDF используя Marker CLI
        
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
                
                # Запускаем marker_single CLI
                cmd = [
                    'marker_single',
                    str(path),
                    '--output_dir', tmpdir,
                    '--disable_multiprocessing'
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 минут таймаут (первый запуск скачивает модели)
                )
                
                if result.returncode != 0:
                    logger.error(f"{self.provider_name}: Ошибка CLI: {result.stderr}")
                    raise RuntimeError(f"marker_single failed: {result.stderr}")
                
                # Ищем markdown файл в tmpdir
                md_files = list(tmpdir_path.glob('*.md'))
                if not md_files:
                    logger.warning(f"{self.provider_name}: Файл результата не найден")
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
