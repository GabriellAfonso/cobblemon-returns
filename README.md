# Cobblemon Returns

Django web platform for a Cobblemon (Minecraft Fabric mod) server. Displays player rankings, a wiki, and a staff dashboard. Collects stats from the Minecraft server via SFTP and posts daily ranking cards to Discord.

---

## Quick Start (local dev)

```bash
# 1. Create and activate a virtual environment
python3.12 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browser
playwright install chromium

# 4. Copy and edit environment variables
cp .env.example .env

# 5. Apply migrations
python manage.py migrate

# 6. (Optional) Load sample data
python manage.py loaddata fixtures/sample_data.json

# 7. Create a staff user for the dashboard
python manage.py createsuperuser

# 8. Run the dev server
python manage.py runserver
```

The site will be at http://127.0.0.1:8000/.

---

## Docker (production)

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f web

# Run a management command inside the container
docker-compose exec web python manage.py createsuperuser
```

The container listens on port **8000**. Nginx on the host proxies to it (see below).

### Environment variables

Copy `.env.example` to `.env` and fill in the values before deploying.
The SSH private key for SFTP must be readable at the path set in `SFTP_KEY_PATH`
(default `/run/secrets/sftp_key`). `docker-compose.yml` mounts `~/.ssh/id_rsa`
at that path read-only.

---

## Nginx snippet

The site runs under the subpath `/cobblemon-returns/` on a shared Nginx server.

```nginx
location /cobblemon-returns/ {
    proxy_pass         http://127.0.0.1:8000/;
    proxy_set_header   Host $host;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   SCRIPT_NAME /cobblemon-returns;
}
```

---

## Running Tests

```bash
# All tests with the in-memory test settings
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test

# A specific app
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test apps.rankings

# Integration tests only
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test tests.test_integration
```

The test settings use an in-memory SQLite database and set `TESTING = True`,
which prevents APScheduler from starting.

---

## Adding a New Ranking

Edit **`apps/rankings/config.py`** and append one dict to the `RANKINGS` list:

```python
{"id": "my_stat", "field": "my_stat_field", "label": "My Stat Label", "icon": "🏆", "format": "number"},
```

- `id` — URL-safe identifier used in templates and Discord tasks
- `field` — `PlayerStats` model field name
- `label` — human-readable name shown in the UI and Discord card
- `icon` — emoji prefix
- `format` — one of `"hours"`, `"number"`, `"currency"`

Then add the corresponding field to `apps/players/models.py` → `PlayerStats` and
write a new migration. The collector, views, and Discord notifier pick up the
change automatically — no other code changes needed.

---

## Cobblemon File Paths (SFTP)

These paths are estimates. Each one has a `# TODO: verify path` comment in
`apps/collector/sftp.py`. Confirm against your actual server layout before
deploying.

| Stat | Path | Key |
|------|------|-----|
| Play time | `{MINECRAFT_WORLD_PATH}/stats/{uuid}.json` | `minecraft:play_time` (ticks) |
| Pokémons caught | count files in `{COBBLEMON_DATA_PATH}/{uuid}/pokemon/` | — |
| Pokédex registered | `{COBBLEMON_DATA_PATH}/{uuid}/data.json` | `caughtPokemon` |
| Battles won | player data file | `battleWins` |
| CobbleDollars | `{COBBLE_ECONOMY_PATH}/{uuid}.json` | `balance` |
| CobbleTCG cards | count files in `{COBBLE_TCG_PATH}/{uuid}/` | — |

All path environment variables are set in `.env` / `docker-compose.yml`.

---

## Dashboard Access

The dashboard lives at `/dashboard/` and requires `is_staff = True`.

1. Create a superuser: `python manage.py createsuperuser`  
   (or promote an existing user: `python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='X').update(is_staff=True)"`)
2. Log in via `/admin/login/`
3. Navigate to `/dashboard/`

From the dashboard you can:
- Browse and sort players by any stat
- Create, edit, and delete wiki pages (with live Markdown preview)
- Trigger an SFTP collection run manually
- View the last 50 collection logs
