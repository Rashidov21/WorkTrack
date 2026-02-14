# WorkTrack

Production-ready employee attendance and lateness monitoring web application integrated with a Hikvision face recognition terminal (DS-K1T343 series).

## Tech stack

- **Backend:** Django (latest stable)
- **Database:** SQLite (structure ready to switch to PostgreSQL via `DATABASE_URL`)
- **Frontend:** HTML + TailwindCSS (CDN)
- **Task queue:** Celery + Redis
- **Realtime notifications:** Telegram Bot
- **Excel export:** openpyxl
- **Authentication:** Django auth with roles (Admin, Manager, Viewer)

## Quick start

### 1. Create virtual environment and install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 2. Configure environment

Copy `env.example` to `.env` and set at least `SECRET_KEY`. Leave `DATABASE_URL` empty for SQLite.

### 3. Run migrations (already done if you followed setup)

```bash
python manage.py migrate
```

### 4. Create superuser

```bash
python manage.py createsuperuser
```

Then open Django admin and set the user's **Role** to **Admin** (Admin → Users → your user → Role).

### 5. Run Redis (for Celery)

- **Windows:** Use WSL, Docker, or [Redis for Windows](https://github.com/microsoftarchive/redis/releases).
- **Linux/macOS:** `redis-server` or `sudo systemctl start redis`.

### 6. Run Celery worker (optional, for webhook and Telegram)

```bash
celery -A config worker -l info
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in.

## Project structure

- **config/** — Django project (settings, URLs, Celery app)
- **core/** — Dashboard, audit log, system settings, decorators
- **accounts/** — Custom user with role (admin, manager, viewer)
- **employees/** — Employee CRUD, work times, grace period, **work schedules** (ish grafiklari)
- **attendance/** — Logs, daily summary, lateness records, services
- **penalties/** — Rules and penalty records, manual adjustment
- **reports/** — Daily/weekly/monthly/yearly reports, Excel export
- **integrations/** — Device webhook endpoint, integration settings UI
- **notifications/** — Telegram settings and async send via Celery

## Work schedules (Ish grafiklari)

Admin can create **work schedules** (name, start/end time, grace period, working days). Assign a schedule to an employee in the employee form. Lateness and penalties are then computed from that schedule for each day; if the day is not a working day for the schedule, no lateness is applied. Employees without a schedule use their personal work start/end times (existing behaviour).

## Device webhook

POST JSON to `/integrations/webhook/`. If you set a **webhook secret** in Integration settings, the device must send it in the `X-Webhook-Secret` header (or `?secret=...`). Rate limit: configurable per IP per minute (default 120; set `WEBHOOK_RATE_LIMIT` in `.env`).

Each item can have:

- `employee_id` (or `person_id`, `card_no`) — required
- `event_type`: `"check_in"` or `"check_out"`
- `timestamp`: ISO datetime (e.g. `"2025-02-14T08:35:00Z"`)
- `event_id`: unique id for idempotency (optional but recommended)

Example (see `sample_webhook_payload.json`):

```json
{
  "employee_id": "EMP001",
  "event_type": "check_in",
  "timestamp": "2025-02-14T08:35:00Z",
  "event_id": "device-12345-67890"
}
```

Flow: Webhook → enqueue Celery task → save log → recompute daily summary → if late, apply penalty and send Telegram message.

## Tailwind

Templates use Tailwind via CDN (`https://cdn.tailwindcss.com`). For production you can switch to a built CSS pipeline (e.g. `django-tailwind` or npm).

## PostgreSQL

Set `DATABASE_URL` in `.env` and install `dj-database-url` and `psycopg`:

```bash
pip install dj-database-url "psycopg[binary]"
```

Example: `DATABASE_URL=postgres://user:pass@localhost:5432/worktrack`

## Roles

- **Admin:** Full access, settings (integration, platform, Telegram), penalty rules, manual penalties.
- **Manager:** View reports, employees, attendance, penalties (no edit on settings/penalty rules).
- **Viewer:** Read-only (same as manager in current UI; can be restricted further if needed).

## License

MIT.
