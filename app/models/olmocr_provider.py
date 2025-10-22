"""
OLMoCR провайдер (AllenAI)
"""
from .base_provider import BaseOCRProvider
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class OLMoCRProvider(BaseOCRProvider):
    """
    Провайдер для OLMoCR от AllenAI.
    Использует Vision Language Model для высококачественного OCR.
    
    ВНИМАНИЕ: Требует GPU с 15GB+ VRAM или использование внешнего API.
    """
    
    def __init__(self):
        super().__init__("OLMoCR")
        self.use_api = False
        self.api_server = None
    
    async def initialize(self) -> None:
        """Инициализация OLMoCR"""
        import os
        
        # Проверяем конфигурацию
        api_server = os.getenv('OLMOCR_API_SERVER', '').strip()
        
        if api_server:
            # Используем внешний API сервер
            self.use_api = True
            self.api_server = api_server
            logger.info(f"{self.provider_name}: Подключен к API {api_server}")
        else:
            # API не настроен - отключаем провайдер
            logger.warning(f"{self.provider_name}: API сервер не настроен (OLMOCR_API_SERVER пуст)")
            self.use_api = False
            self.api_server = None
    
    async def extract_text(self, file_path: str) -> str:
        """
        Извлекает текст из PDF используя OLMoCR
        
        Args:
            file_path: Путь к PDF файлу
            
        Returns:
            str: Распознанный текст в Markdown формате
        """
        # Если API сервер не настроен, возвращаем пустую строку
        if not self.api_server or not self.use_api:
            return ""
        
        path = Path(file_path)
        
        if path.suffix.lower() != '.pdf':
            raise ValueError(f"{self.provider_name}: Поддерживает только PDF файлы")
        
        if self.use_api:
            return await self._extract_via_api(file_path)
        else:
            return await self._extract_local(file_path)
    
    async def _extract_local(self, pdf_path: str) -> str:
        """Локальная обработка с GPU"""
        try:
            import subprocess
            import tempfile
            import json
            
            # Создаём временную директорию для результатов
            with tempfile.TemporaryDirectory() as tmpdir:
                # Запускаем olmocr pipeline
                cmd = [
                    'python', '-m', 'olmocr.pipeline',
                    tmpdir,
                    '--markdown',
                    '--pdfs', pdf_path
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 минут таймаут
                )
                
                if result.returncode != 0:
                    raise RuntimeError(f"OLMoCR failed: {result.stderr}")
                
                # Читаем результат из markdown файла
                pdf_name = Path(pdf_path).stem
                md_file = Path(tmpdir) / 'markdown' / f'{pdf_name}.md'
                
                if md_file.exists():
                    return md_file.read_text()
                else:
                    logger.warning(f"{self.provider_name}: Файл результата не найден")
                    return ""
                    
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка локальной обработки: {e}")
            raise
    
    async def _extract_via_api(self, pdf_path: str) -> str:
        """Обработка через внешний API"""
        try:
            import httpx
            
            # Отправляем PDF на API сервер
            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(pdf_path, 'rb') as f:
                    files = {'file': f}
                    response = await client.post(
                        f"{self.api_server}/convert",
                        files=files
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    return result.get('text', '')
                    
        except Exception as e:
            logger.error(f"{self.provider_name}: Ошибка API: {e}")
            raise
