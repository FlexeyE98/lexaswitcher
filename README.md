# LEXA_SWITCHER_850k

`LEXA_SWITCHER_850k` - переключатель раскладки EN <-> RU.

## Что сделано
- Исправлен баг с лишними символами перед конвертированным текстом.
- Добавлен единый запуск из корня с автоопределением ОС.
- Проект разложен по платформенным папкам.

## Структура
- `START_LEXA_SWITCHER_850k.py` - единый запуск из корня.
- `app/lexa_switcher.py` - кроссплатформенная логика.
- `config/config.ini` - конфиг.
- `windows/START_LEXA_SWITCHER_850k.ps1` и `windows/START_LEXA_SWITCHER_850k.cmd` - Windows.
- `windows/LEXA_SWITCHER_850k.ahk` - legacy fallback.
- `ubuntu-macos/START_LEXA_SWITCHER_850k.sh` - Ubuntu/macOS.
- `requirements.txt` - зависимости Python.

## Универсальный запуск
```bash
python START_LEXA_SWITCHER_850k.py
```

Логика:
- Windows -> запускается `windows/START_LEXA_SWITCHER_850k.ps1`
- Ubuntu/macOS -> запускается `ubuntu-macos/START_LEXA_SWITCHER_850k.sh`

## Хоткеи
- `Right Shift` - конвертировать последнюю набранную фразу.
- `Ctrl+Alt+Pause` - включить/выключить (`Ctrl+Alt+P` fallback в Python-версии).

## Быстрая проверка конвертации
```bash
python app/lexa_switcher.py --self-test
```
Ожидаемый вывод:
```text
привет идиот
```

## Ограничения
- macOS: нужен доступ Terminal/IDE в `Privacy & Security -> Accessibility`.
- Linux: глобальные хуки зависят от X11/Wayland и окружения.
