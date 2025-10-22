# Настройка OLMoCR (Опционально)

OLMoCR - самая продвинутая модель, но требует GPU сервер с 15GB+ VRAM.

## Вариант 1: Использование внешнего API сервера

### На GPU сервере (172.181.23.132):

1. Подключитесь к VPN:
```bash
sudo openconnect https://212.112.104.124 --user=ArapbaevZ
# Пароль: 4asnmm33rv
```

2. SSH на GPU сервер:
```bash
ssh ArapbaevZ@172.181.23.132
# Пароль: 4asnmm33rv
```

3. Установите и запустите OLMoCR:
```bash
# Установка
pip install git+https://github.com/allenai/olmocr.git

# Запуск API сервера
python -m olmocr.pipeline --server-mode --port 8000
```

### На локальной машине:

Добавьте в `.env`:
```bash
OLMOCR_API_SERVER=http://172.181.23.132:8000/v1
```

Перезапустите сервер:
```bash
./run.sh
```

## Вариант 2: Локальная установка (требует GPU 15GB+)

Если у вас есть мощный GPU:

```bash
# Установка
pip install git+https://github.com/allenai/olmocr.git torch torchvision

# OLMoCR автоматически обнаружит GPU
```

В `.env` оставьте:
```bash
OLMOCR_API_SERVER=
```

## Проверка работы

После настройки протестируйте в Web UI:
- Откройте http://localhost:8000/static/index.html
- Загрузите PDF файл
- Должны работать все 4 модели: PaddleOCR, Marker, MinerU, OLMoCR
