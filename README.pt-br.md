# Cobblemon Returns 🌿

> 🇺🇸 [Read in English](README.md)

Plataforma web feita para um servidor privado de Cobblemon — um mod de Pokémon para Minecraft Fabric.  
Um projeto feito por diversão para um grupo de amigos.

**Funcionalidades:** rankings de jogadores · wiki do servidor · cards diários no Discord · painel staff

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.14 + Django 6 |
| Banco de dados | SQLite |
| Agendador | APScheduler |
| Coleta de dados | Paramiko (SFTP) + nbtlib (NBT) |
| Discord | Playwright + Webhook |
| Servidor | Gunicorn + Docker |

---

## Como rodar

```bash
cp .env.example .env        # preencha os valores
docker compose up -d --build
docker compose exec cobblemon_returns python manage.py createsuperuser
```

Acesse http://localhost:8000/

---

## Estrutura do projeto

```
core/                 # Settings, URLs, WSGI, templates base
features/
├── players/          # Modelos Player + PlayerStats
├── rankings/         # Views + config de rankings
├── collector/        # Coleta via SFTP + APScheduler
├── discord_notifier/ # Screenshot com Playwright + webhook
├── wiki/             # Modelo WikiPage + views Markdown
├── home/             # Página inicial
├── mods/             # Página de mods
└── dashboard/        # Painel exclusivo para staff
```
