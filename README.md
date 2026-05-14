# monitoring_uvao

Внутренний сервис мониторинга репостов ВК по сеткам районов ЮВАО.

## Запуск

1. Заполнить `VK_SERVICE_TOKEN` в `.env`.
2. Поднять БД и приложение:

```bash
docker compose up -d --build
```

3. Прогнать миграции и сидер:

```bash
docker compose exec web alembic upgrade head
docker compose exec web python scripts/seed.py
```

4. Открыть `http://localhost:8000`.

## Аккаунты после сидера

Пароль для всех первичных аккаунтов берётся из `BOOTSTRAP_ADMIN_PASSWORD`.

- `admin` — администратор, видит все сетки.
- `lublino` — Люблино.
- `kapotnya` — Капотня.
- `maryino` — Марьино.
- `vykhino` — Выхино-Жулебино.
- `kuzminki` — Кузьминки.

Районный пользователь видит и использует только свою сетку.

## Локальные проверки

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/ruff check .
.venv/bin/pytest
```
