# Cobblemon Returns 🌿

> 🇧🇷 [Leia em Português](README.pt-br.md)

A web platform built for a private Cobblemon server — a Pokémon mod for Minecraft Fabric.  
A fun side project made for a small group of friends.

**Features:** player rankings · server wiki · Discord daily cards · staff dashboard

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.14 + Django 6 |
| Database | SQLite |
| Scheduler | APScheduler |
| Data collection | Paramiko (SFTP) + nbtlib (NBT) |
| Discord | Playwright + Webhook |
| Server | Gunicorn + Docker |

---

## Getting Started

```bash
cp .env.example .env        # fill in the values
docker compose up -d --build
docker compose exec cobblemon_returns python manage.py createsuperuser
```

Open http://localhost:8000/

---

## Project Structure

```
core/                 # Settings, URLs, WSGI, base templates
features/
├── players/          # Player + PlayerStats models
├── rankings/         # Views + RANKINGS config
├── collector/        # SFTP collection + APScheduler
├── discord_notifier/ # Playwright screenshot + webhook
├── wiki/             # WikiPage model + Markdown views
├── home/             # Home page
├── mods/             # Mods page
└── dashboard/        # Staff panel
```
