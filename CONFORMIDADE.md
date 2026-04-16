# Plano de Conformidade com CLAUDE.md

Cada passo descreve **o que precisa ser feito**, **por que** viola o CLAUDE.md, e **como será implementado**.
Os passos estão ordenados do menor para o maior impacto/risco.

---

## Passo 1 — Models incompletos

**Violação:** Seção 6 — "Models sempre com `__str__`, `Meta.ordering` e `Meta.verbose_name`."

| Model | Falta |
|---|---|
| `Player` | `Meta` inteiro (ordering, verbose_name) |
| `PlayerStats` | `__str__` e `Meta` inteiro |
| `CollectionLog` | `__str__` e `Meta.verbose_name` |
| `DiscordPostedMessage` | `Meta` inteiro (ordering, verbose_name) |
| `WikiPage` | `Meta.verbose_name` |

**Como será feito:**
- `apps/players/models.py` — adicionar `Meta` em `Player` e `PlayerStats`; adicionar `__str__` em `PlayerStats`
- `apps/collector/models.py` — adicionar `__str__` e `verbose_name` ao `Meta` de `CollectionLog`
- `apps/discord_notifier/models.py` — adicionar `Meta` completa a `DiscordPostedMessage`
- `apps/wiki/models.py` — adicionar `verbose_name` ao `Meta` existente de `WikiPage`

**Dependências novas:** nenhuma
**Risco:** baixo — sem mudança de comportamento, apenas metadados.

---

## Passo 2 — `app_name` ausente nas URLs

**Violação:** Seção 6 — "URLs sempre com `app_name` para namespacing e nomes descritivos."

`rankings/urls.py` e `dashboard/urls.py` não declaram `app_name`, o que impede usar `{% url 'rankings:home' %}` nos templates. Só `wiki` está correto hoje.

**Como será feito:**
- `apps/rankings/urls.py` — adicionar `app_name = 'rankings'`
- `apps/dashboard/urls.py` — adicionar `app_name = 'dashboard'`
- Atualizar todas as referências a `reverse()`/`{% url %}` nos templates e views que usam os nomes sem namespace (ex: `'home'` → `'rankings:home'`, `'dashboard-home'` → `'dashboard:home'`)
- Atualizar os `reverse_lazy(...)` nas views do dashboard

**Dependências novas:** nenhuma
**Risco:** médio — qualquer `reverse()` ou `{% url %}` não atualizado quebra em runtime. Os testes existentes vão pegar a maioria dos casos.

---

## Passo 3 — `SECRET_KEY` com fallback hardcoded em dev

**Violação:** Seção 7 — "Nunca hardcode credenciais, secrets ou chaves."

`config/settings/dev.py` usa `os.environ.get('SECRET_KEY', 'dev-insecure-key')`. O CLAUDE.md determina falha ruidosa se a variável não estiver definida — o fallback existe para conveniência mas viola a regra.

**Como será feito:**
- `config/settings/dev.py` — trocar `os.environ.get('SECRET_KEY', 'dev-insecure-key')` por `os.environ['SECRET_KEY']`
- Garantir que `.env.example` documenta que `SECRET_KEY` é obrigatório mesmo em dev

**Dependências novas:** nenhuma
**Risco:** baixo — quem não tiver `SECRET_KEY` no `.env` vai receber `KeyError` claro na inicialização, que é o comportamento esperado.

---

## Passo 4 — Type hints nas funções públicas

**Violação:** Seção 6 — "Type hints nas assinaturas de funções públicas."

Nenhuma função no projeto tem type hints. Os candidatos mais impactantes são:

| Arquivo | Funções |
|---|---|
| `apps/collector/sftp.py` | `get_sftp_client`, `read_json_file`, `read_nbt_file`, `read_usercache`, `collect_player_data` |
| `apps/rankings/formatters.py` | `format_value` |
| `apps/collector/tasks.py` | `run_collection`, `start_scheduler` |
| `apps/discord_notifier/tasks.py` | `post_all_rankings`, `schedule_discord_posts` |
| `apps/discord_notifier/webhook.py` | `send_ranking_image`, `delete_discord_message` |
| `apps/discord_notifier/screenshot.py` | `render_ranking_screenshot` |

**Como será feito:**
- Adicionar anotações de tipo nas assinaturas (parâmetros + retorno)
- Usar `dict[str, Any]` para dicts heterogêneos, `str | None` onde aplicável
- Não forçar em variáveis locais triviais

**Dependências novas:** nenhuma (Python 3.14 já tem tudo nativo)
**Risco:** nenhum — puramente anotações, sem mudança de comportamento.

---

## Passo 5 — Camada de Repositório

**Violação:** Seção 5.2 — "Repositories são a única camada que importa models Django e faz queries ORM." e "Views não conhecem repositories. Só chamam services."

Atualmente views e tasks fazem queries ORM diretamente:

```python
# rankings/views.py — ORM na view
PlayerStats.objects.order_by(f'-{r["field"]}').select_related('player')[:10]

# dashboard/views.py — ORM na view
Player.objects.count()
CollectionLog.objects.first()

# collector/tasks.py — ORM na task
Player.objects.get_or_create(uuid=uuid, ...)
PlayerStats.objects.update_or_create(player=player, ...)
```

**Como será feito:**

Criar os seguintes repositórios:

- `apps/players/repositories/player_repository.py` — `PlayerRepository`: `get_or_create`, `update_username`, `count`
- `apps/players/repositories/stats_repository.py` — `PlayerStatsRepository`: `get_top_n`, `get_last_updated`, `update_or_create`
- `apps/collector/repositories/log_repository.py` — `CollectionLogRepository`: `create`, `get_latest`, `get_last_n`
- `apps/discord_notifier/repositories/message_repository.py` — `DiscordMessageRepository`: `get_by_ranking`, `update_or_create`

Cada repositório recebe o model como dependência (DIP) e expõe métodos nomeados pelo caso de uso, não pelo ORM.

As views e tasks passam a instanciar e chamar os repositórios diretamente (sem service por enquanto — ver Passo 6).

**Dependências novas:** nenhuma
**Risco:** médio — refatoração significativa, mas sem mudança de lógica. Os testes existentes validam o comportamento.

---

## Passo 6 — Camada de Service

**Violação:** Seção 5.2 — "Views → Services → Repositories → Models." e SRP — views que orquestram múltiplas queries estão acumulando responsabilidade.

Após o Passo 5, views ainda orquestram chamadas a múltiplos repositórios. O service extrai essa lógica:

```python
# Hoje na view (rankings/views.py)
for r in RANKINGS:
    top10 = stats_repo.get_top_n(r['field'], 10)
    max_val = ...
    players = [...]   # ← lógica de negócio dentro da view
```

**Como será feito:**

Criar:

- `apps/rankings/services/ranking_service.py` — `RankingService`: `get_home_leaders`, `get_full_rankings` — recebe `PlayerStatsRepository` no construtor
- `apps/collector/services/collection_service.py` — `CollectionService`: `run` — recebe `PlayerRepository`, `PlayerStatsRepository`, `CollectionLogRepository` e o cliente SFTP
- `apps/dashboard/services/dashboard_service.py` — `DashboardService`: `get_summary` — recebe `PlayerRepository`, `CollectionLogRepository`

Views passam a instanciar o service com seus repositórios e chamam o método adequado.

**Dependências novas:** nenhuma
**Risco:** médio-alto — maior refatoração. Recomendado fazer após o Passo 5 estar validado pelos testes.

---

## Passo 7 — Cross-feature imports

**Violação:** Seção 4.2 — "Features não importam umas das outras diretamente."

Imports diretos entre features hoje:

| De | Importa |
|---|---|
| `dashboard/views.py` | `apps.players.models`, `apps.collector.models`, `apps.wiki.models` |
| `collector/tasks.py` | `apps.players.models` |
| `discord_notifier/tasks.py` | `apps.rankings.config`, `apps.players.models`, `apps.rankings.formatters` |

**Como será feito:**

O CLAUDE.md permite duas saídas: código compartilhado ou signals. Para este projeto:

- `collector` precisa de `Player`/`PlayerStats` → o collector **cria** esses dados, então o correto é o `players` app expor uma interface no `apps/players/services/` que o collector chama. Ou: mover a persistência de players para dentro do próprio collector (mas ai viola SRP). Solução pragmática: extrair um módulo `shared/` com as interfaces que múltiplos apps precisam.

- `dashboard` agrega dados de vários domínios → por natureza é um agregador. A solução correta é o `dashboard` depender de **services** expostos por cada app em uma interface pública (`apps/<app>/services/`) em vez de acessar models diretamente. Assim continua havendo dependência, mas de contratos (services), não de implementação (models/ORM).

- `discord_notifier` usa `RANKINGS` config e `format_value` de `rankings` → mover `config.py` e `formatters.py` para um módulo compartilhado `apps/shared/rankings_config.py` que ambos importam.

Este passo depende dos Passos 5 e 6 estarem concluídos.

**Dependências novas:** nenhuma
**Risco:** alto — o maior refatoração do projeto. Requer atenção nos testes de integração.

---

## Resumo dos Passos

| # | Passo | Impacto | Risco | Depende de |
|---|---|---|---|---|
| 1 | Models completos (Meta + `__str__`) | Baixo | Baixo | — |
| 2 | `app_name` nas URLs | Baixo | Médio | — |
| 3 | `SECRET_KEY` sem fallback | Baixo | Baixo | — |
| 4 | Type hints | Baixo | Nenhum | — |
| 5 | Camada de Repositório | Alto | Médio | — |
| 6 | Camada de Service | Alto | Médio-Alto | Passo 5 |
| 7 | Eliminar cross-feature imports | Alto | Alto | Passos 5 e 6 |

**Passos 1–4** são independentes entre si e podem ser feitos em qualquer ordem.
**Passos 5–7** devem ser feitos em sequência.
