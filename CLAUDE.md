# CLAUDE.md — Cobblemon Returns

Plataforma web para servidor Cobblemon: rankings, wiki, mods, notificações Discord, painel admin.

---

## Arquitetura

Feature-based: cada feature = Django app em `features.<nome>`. Features não importam umas das outras.

Fluxo: `Views → Services → Repositories → Models`. Nunca pular camadas.

---

## Código

- Inglês (exceto strings visíveis ao usuário).
- Conciso. Sem abstrações desnecessárias. Sem duplicação.
- Type hints em funções públicas. PEP 8. Linha ≤ 100 chars.
- `select_related`/`prefetch_related` — nunca queries em loops.

---

## Testes

```bash
wsl_venv/bin/python manage.py test .
wsl_venv/bin/python manage.py test . --tag=unit
wsl_venv/bin/python manage.py test . --tag=integration
```

Todo `TestCase` novo deve ter `@tag('unit')` ou `@tag('integration')`.

---

## Notas Não-Óbvias

**Rankings:** adicionar = novo dict em `features/rankings/config.py`. Nada mais.

**`htmls-gerados/`:** definem o design visual. Templates devem segui-los. **Não modificar.**  
`discord_card.html` é renderizado pelo Playwright — self-contained, 520px de largura.

**Production subpath** (`core/settings/prod.py`):
```python
FORCE_SCRIPT_NAME = '/cobblemon-returns'
USE_X_FORWARDED_HOST = True
```

**SECRET_KEY no `.env`:** `$` deve ser escapado como `$$` para o docker-compose não interpolar.
