# KINOLINK BOT

Telegram-бот для поиска фильмов и сериалов. Данные о фильмах берутся из TMDB, просмотр открывается через Vibix/Rendex player в Mini App или браузере.

## Запуск

Создай `.env` по примеру `.env.example` и заполни токены.

### Бэкенд
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Бот
```bash
python -B -m bot.main
```
