# Cobblemon Returns 🌿

> A web platform built for a private Cobblemon server — a Pokémon mod for Minecraft Fabric.  
> This is a fun side project made for a small group of friends. Don't expect enterprise-grade anything.

**Live features:**
- Player rankings updated automatically via SFTP from the Minecraft server
- Daily ranking cards posted to Discord via webhook
- Server wiki with Markdown support
- Staff dashboard for managing content and monitoring data collection

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + Django 5 |
| Database | SQLite |
| Scheduler | APScheduler (background jobs) |
| Data collection | Paramiko (SFTP) + nbtlib (NBT parsing) |
| Discord | Playwright (screenshot) + Webhook |
| Markdown | mistune |
| Server | Gunicorn + Docker |

---

## Getting Started (local dev)

```bash
# 1. Create and activate a virtual environment
python3.12 -m venv .venv && source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install Playwright browser
playwright install chromium

# 4. Copy and fill in environment variables
cp .env.example .env

# 5. Apply migrations
python manage.py migrate

# 6. (Optional) Load sample data
python manage.py loaddata fixtures/sample_data.json

# 7. Create a staff user for the dashboard
python manage.py createsuperuser

# 8. Start the dev server
python manage.py runserver
```

Open http://127.0.0.1:8000/

---

## Docker

```bash
# Build and start
docker compose up -d --build

# View logs
docker compose logs -f

# Run a management command inside the container
docker compose exec cobblemon_returns python manage.py createsuperuser
```

The container listens on **port 8000**. An external Nginx proxies to it.

### Environment variables

Copy `.env.example` to `.env` and fill in the values. The SSH private key for SFTP
must be readable at `SFTP_KEY_PATH` (default `/run/secrets/sftp_key`).  
`docker-compose.yml` mounts `~/.ssh/id_rsa` at that path read-only.

---

## Nginx

The site runs under `/cobblemon-returns/` on a shared Nginx server:

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
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test
```

Test settings use in-memory SQLite and `TESTING = True`, which prevents APScheduler from starting.

---

## Adding a New Ranking

Edit `apps/rankings/config.py` and append one dict to `RANKINGS`:

```python
{"id": "my_stat", "field": "my_stat_field", "label": "My Label", "icon": "🏆", "format": "number"},
```

Then add the field to `PlayerStats` in `apps/players/models.py` and run `makemigrations`.  
The views, collector, and Discord notifier pick it up automatically — no other changes needed.

`format` options: `"hours"` · `"number"` · `"currency"`

---

## Minecraft File Paths (SFTP)

Data is collected from the Minecraft server over SFTP. Paths are configured via `.env`:

| Stat | Source |
|---|---|
| Play time | `{MINECRAFT_WORLD_PATH}/stats/{uuid}.json` → `minecraft:play_time` |
| Pokémons caught | `{COBBLEMON_DATA_PATH}/{shard}/{uuid}.json` → `advancementData.totalCaptureCount` |
| Pokédex | `{MINECRAFT_WORLD_PATH}/pokedex/{shard}/{uuid}.nbt` → count of `speciesRecords` |
| Battles won | `{COBBLEMON_DATA_PATH}/{shard}/{uuid}.json` → `advancementData.totalBattleVictoryCount` |
| CobbleDollars | `{COBBLE_ECONOMY_PATH}/{uuid}.json` → `cobbledollars` |
| CobbleTCG cards | not implemented yet (addon pending) |

---

## Dashboard

The dashboard is at `/dashboard/` and requires `is_staff = True`.

```bash
# Promote an existing user to staff
python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.filter(username='your_username').update(is_staff=True)
"
```

From the dashboard you can browse players, manage wiki pages, trigger a manual collection run, and view the last 50 collection logs.

---

## Project Structure

```
cobblemon_returns/
├── apps/
│   ├── players/          # Player + PlayerStats models
│   ├── rankings/         # Views + RANKINGS config
│   ├── collector/        # SFTP collection + APScheduler
│   ├── discord_notifier/ # Playwright screenshot + webhook
│   ├── wiki/             # WikiPage model + Markdown views
│   └── dashboard/        # Staff panel
├── config/
│   └── settings/         # base / dev / prod / test
├── static/
│   └── css/              # base, home, rankings, wiki, dashboard
├── templates/
└── fixtures/
```

---

*Built with way too much attention to detail for a server with 30 players. We had fun.*
