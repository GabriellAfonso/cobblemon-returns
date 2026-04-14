# Cobblemon Returns — Claude Code Guide

## Project Overview
Django web platform for a Cobblemon (Minecraft Fabric mod) server.
Public site (~30 players), feature-based architecture, SQLite, no Celery.

## Tech Stack
- Python 3.12 + Django 5.x
- SQLite (single DB file)
- APScheduler (scheduled tasks)
- Paramiko (SFTP file collection)
- Playwright (ranking screenshot for Discord)
- Discord Webhooks (no bot library)
- mistune (Markdown rendering)
- Gunicorn (production server)
- Docker + docker-compose

## Project Structure
```
cobblemon_returns/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── players/          # Player + PlayerStats models
│   ├── rankings/         # Ranking views + RANKING_CONFIG
│   ├── collector/        # SFTP collection + APScheduler
│   ├── discord_notifier/ # Playwright screenshot + webhook
│   ├── wiki/             # WikiPage model + markdown views
│   └── dashboard/        # Custom staff-only admin panel
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── rankings/
│   │   ├── page.html
│   │   └── discord_card.html   # screenshot target (no navbar, 520px wide)
│   ├── wiki/
│   └── dashboard/
├── static/
├── htmls-gerados/        # Pre-built HTML references (DO NOT modify)
│   ├── home.html
│   ├── rankings.html
│   └── discord_card.html
├── fixtures/
│   └── sample_data.json
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── manage.py
```

## Key Conventions
- All code and comments in English
- Comments only where logic is non-obvious — no over-commenting
- Feature-based: each app is self-contained with its own models, views, urls, tests
- Settings split: base / dev / prod. Use DJANGO_SETTINGS_MODULE env var to switch.
- RANKING_CONFIG in `apps/rankings/config.py` — adding a new ranking = adding one dict to the list, nothing else

## Rankings Config Pattern
```python
# apps/rankings/config.py
RANKINGS = [
    {"id": "hours",    "field": "play_time_ticks", "label": "Hours Played",      "icon": "⏱️",  "format": "hours"},
    {"id": "catches",  "field": "pokemons_caught",  "label": "Pokémons Caught",   "icon": "🔴", "format": "number"},
    {"id": "pokedex",  "field": "pokedex_registered","label": "Pokédex Registered","icon": "📕", "format": "number"},
    {"id": "cards",    "field": "cobbletcg_cards",  "label": "CobbleTCG Cards",   "icon": "🃏", "format": "number"},
    {"id": "battles",  "field": "battles_won",      "label": "Battles Won",       "icon": "⚔️",  "format": "number"},
    {"id": "money",    "field": "cobbledollars",     "label": "CobbleDollars",     "icon": "💰", "format": "currency"},
]
```

## HTML References (htmls-gerados/)
These files define the visual design. Django templates must match them faithfully.
- `home.html` → base for `templates/home.html`
- `rankings.html` → base for `templates/rankings/page.html`
- `discord_card.html` → base for `templates/rankings/discord_card.html`
  - This template is rendered headlessly by Playwright. Keep it self-contained (no external requests), 520px wide.

## Cobblemon File Paths (SFTP)
Paths are estimates — add a TODO comment if uncertain:
- Vanilla stats: `{world}/stats/{uuid}.json` → key `minecraft:play_time` (ticks)
- Pokémons caught: count files in `{cobblemon_data}/{uuid}/pokemon/` (TODO: verify)
- Pokédex: field in `{cobblemon_data}/{uuid}/data.json` → `caughtPokemon` (TODO: verify)
- Battles won: field `battleWins` in player data file (TODO: verify)
- CobbleDollars: `{cobble_economy}/{uuid}.json` → field `balance` (TODO: verify)
- CobbleTCG cards: `{cobble_tcg}/{uuid}/` → count card files (TODO: verify)

## Environment Variables (.env)
```
DJANGO_SETTINGS_MODULE=config.settings.dev
SECRET_KEY=
DEBUG=True
SERVER_HOST=play.gabrielafonso.com.br
SFTP_HOST=
SFTP_PORT=22
SFTP_USER=
SFTP_KEY_PATH=/run/secrets/sftp_key
MINECRAFT_WORLD_PATH=/path/to/world
COBBLEMON_DATA_PATH=/path/to/cobblemon
COBBLE_ECONOMY_PATH=/path/to/cobbleeconomy
COBBLE_TCG_PATH=/path/to/cobbletcg
COLLECTOR_INTERVAL_MINUTES=15
DISCORD_WEBHOOK_URL=
DISCORD_INVITE_URL=https://discord.gg/cyx2d2Vtey
DISCORD_RANKING_HOUR=20
```

## Docker Notes
- Single service: `web` (Django + Gunicorn on port 8000)
- Entrypoint runs: migrate → collectstatic → gunicorn
- Healthcheck: GET /health/ every 30s
- SQLite and staticfiles on named volumes
- SSH private key mounted read-only: `~/.ssh/id_rsa:/run/secrets/sftp_key:ro`
- Nginx (external, already configured on VPS) proxies to port 8000

## Production Subpath
The site runs under `/cobblemon-returns/` on a shared Nginx server.
In `config/settings/prod.py`:
```python
FORCE_SCRIPT_NAME = '/cobblemon-returns'
USE_X_FORWARDED_HOST = True
STATIC_URL = '/cobblemon-returns/static/'
```
Nginx must pass: `proxy_set_header SCRIPT_NAME /cobblemon-returns;`

## Testing
- One `tests/` folder per app
- Use Django's `TestCase`
- Mock SFTP calls with `unittest.mock`
- No need for 100% coverage — focus on: collector parsing, ranking ordering, discord payload, wiki rendering
