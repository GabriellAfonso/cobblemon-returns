# CLAUDE.md — Django Base

> Este arquivo define como o Claude deve se comportar neste projeto.
> Adapte as seções marcadas com `[ADAPTAR]` para cada projeto específico.

---

## 1. Visão Geral do Projeto

- **Nome:** Cobblemon Returns
- **Objetivo:** Plataforma web para um servidor Cobblemon (mod Minecraft Fabric) — rankings de jogadores, wiki, notificações no Discord e painel administrativo.
- **Público-alvo:** ~30 jogadores do servidor, staff para gerenciamento.

---

## 2. Stack Principal

```
Python 3.14 / Django 5.2
Banco de dados: SQLite (dev e prod)
Frontend: Django Templates + CSS/JS estático
Fila/Scheduler: APScheduler 3.11
Renderização headless: Playwright 1.58 (Chromium) — discord card
Deploy: Docker (Gunicorn 25.3 na porta 8000) + Nginx externo (proxy reverso, subpath /cobblemon-returns/)
```

---

## 3. Fluxo de Trabalho — Plano Antes de Agir

**Para qualquer tarefa que envolva criar ou modificar código, o Claude DEVE:**

1. **Apresentar um plano** antes de escrever qualquer linha de código. O plano deve conter:
   - Quais arquivos serão criados ou modificados
   - O que cada arquivo fará (em uma frase)
   - Se alguma dependência nova será necessária
   - Riscos ou pontos de atenção identificados

2. **Aguardar confirmação** do usuário ("pode aplicar", "ok", "vai", ou similar).

3. **Só então implementar.**

Exemplo de formato de plano:
```
📋 Plano de implementação:

Criar:
  - features/orders/services/create_order.py — lógica de criação do pedido
  - features/orders/repositories/order_repository.py — acesso ao banco

Modificar:
  - features/orders/urls.py — adicionar rota POST /orders/

Dependências novas: nenhuma
Riscos: nenhum identificado

Posso aplicar?
```

---

## 4. Arquitetura — Feature-Based

O projeto é organizado por **feature** (domínio de negócio), não por tipo técnico.
Cada feature é autossuficiente: contém suas views, urls, models e testes.

### 4.2 Regras da Arquitetura Feature-Based

- **Features não importam umas das outras diretamente.** Se precisar de algo de outra feature, use código compartilhado ou um signal.
- **Cada feature é uma Django app** registrada no `INSTALLED_APPS` como `features.<nome>`.
- Não crie uma feature só porque um model existe — crie quando há um **domínio de negócio** coeso.
- Quando uma feature crescer demais, divida em sub-features; nunca misture responsabilidades.

---

## 5. Princípios de Design

### 5.1 SOLID

**S — Single Responsibility Principle**
Cada classe ou função tem uma única razão para mudar.
- View: receber request e retornar response. Nada mais.
- Service: executar um caso de uso. Nada mais.
- Repository: interagir com o banco. Nada mais.
- ❌ Errado: uma view que valida dados, faz query, envia email e retorna JSON.

**O — Open/Closed Principle**
Classes abertas para extensão, fechadas para modificação.
- Adicione comportamento via herança ou composição, não editando a classe original.
- Use classes base (`BaseRepository`, `BaseService`) como contratos que as implementações estendem.
- ❌ Errado: adicionar `if tipo == "email"` dentro de um `NotificationService` existente. Certo: criar `EmailNotificationService` que estende a base.

**L — Liskov Substitution Principle**
Subclasses devem substituir a classe base sem quebrar o comportamento esperado.
- Se `StripePaymentService` herda de `BasePaymentService`, qualquer código que use `BasePaymentService` deve funcionar com `StripePaymentService` sem adaptação.
- ❌ Errado: sobrescrever um método e mudar seu contrato — tipos de parâmetros, exceções lançadas ou valor retornado.

**I — Interface Segregation Principle**
Não force uma classe a depender de métodos que ela não usa.
- Prefira ABCs pequenas e focadas. Um repositório somente-leitura não deve herdar de uma classe que também escreve.
- ❌ Errado: um `FullCRUDRepository` com 10 métodos quando a feature só precisa de `get_by_id`.

**D — Dependency Inversion Principle**
Módulos de alto nível não dependem de módulos de baixo nível — ambos dependem de abstrações.
- Services dependem de interfaces de repositório, não da implementação concreta do ORM.
- Injete dependências via construtor.
- ❌ Errado: `OrderService` instancia `OrderRepository()` internamente. ✅ Certo: recebe o repositório como parâmetro.

---

### 5.2 Clean Architecture

O fluxo de dependências sempre aponta para dentro: **Views → Services → Repositories → Models**.
Camadas externas conhecem as internas; camadas internas **nunca** conhecem as externas.

```
┌─────────────────────────────────┐
│  Views / Serializers / Forms    │  ← entrada/saída (HTTP, JSON, HTML)
├─────────────────────────────────┤
│  Services (Casos de Uso)        │  ← regras de negócio da aplicação
├─────────────────────────────────┤
│  Domain / Models                │  ← entidades e regras de negócio puras
├─────────────────────────────────┤
│  Repositories                   │  ← persistência (ORM, cache, APIs externas)
└─────────────────────────────────┘
```

**Regras concretas:**

- **Views** não conhecem repositories. Só chamam services.
- **Services** não importam `request`, `HttpResponse` ou qualquer objeto HTTP.
- **Repositories** são a única camada que importa models Django e faz queries ORM.
- **Models** não importam services nem repositories — são entidades puras.
- Erros de domínio sobem como **exceções de domínio**, não como `Http404` ou `ValidationError` do DRF dentro do service.

Exemplo de fluxo correto:
```python
# views/order_views.py
def create_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    order = CreateOrderService(OrderRepository()).execute(serializer.validated_data)
    return Response(OrderSerializer(order).data, status=201)

# services/create_order.py
class CreateOrderService:
    def __init__(self, order_repo: OrderRepository):
        self.order_repo = order_repo

    def execute(self, data: dict) -> Order:
        # regras de negócio aqui
        return self.order_repo.create(data)

# repositories/order_repository.py
class OrderRepository:
    def create(self, data: dict) -> Order:
        return Order.objects.create(**data)
```

---

## 6. Regras de Código

- **Todo código em inglês.** Nomes de variáveis, funções, classes, arquivos, comentários e mensagens de commit. A única exceção é conteúdo visível ao usuário final (ex: strings em templates).
- **Seja conciso.** Prefira código simples e direto. Evite abstrações desnecessárias.
- **Não duplique lógica.** Se algo já existe no projeto, reutilize.
- **Sem comentários óbvios.** Comente apenas o que não é autoevidente.
- **Type hints** nas assinaturas de funções públicas. Não force em variáveis locais triviais.
- Siga **PEP 8**. Limite de linha: 100 caracteres.
- Models sempre com `__str__`, `Meta.ordering` e `Meta.verbose_name`.
- Prefira `select_related` / `prefetch_related` — nunca queries dentro de loops.
- URLs sempre com `app_name` para namespacing e nomes descritivos.

---

## 7. Segurança — Regras Inegociáveis

- **Nunca hardcode** credenciais, secrets ou chaves. Use sempre variáveis de ambiente.
- **Nunca** desabilite `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_SECURE` ou `SECURE_SSL_REDIRECT` em produção.
- Todo input de usuário que vai pro banco passa por form/serializer com validação.
- Use `get_object_or_404` em vez de `.get()` sem tratamento nas views.
- Permissões explícitas em toda view que exige autenticação.
- `DEBUG = False` em produção. Nunca exponha tracebacks.
- Nunca use `.raw()` ou `format()` em SQL com input do usuário. Use o ORM.

---

## 8. Variáveis de Ambiente

O projeto usa `.env` na raiz. **Nunca sugira colocar valores reais no código.**

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

```python
import os
SECRET_KEY = os.environ["SECRET_KEY"]           # falha ruidosa se ausente — intencional
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///db.sqlite3")  # default só em dev
```

---

## 9. Testes

- Use Django's `TestCase` com `unittest.mock` para chamadas SFTP.
- Teste o comportamento, não a implementação interna.
- Mínimo: **caminho feliz + 1 caso de erro** por caso de uso.
- Foco em: collector parsing, ranking ordering, discord payload, wiki rendering.
- Um `tests/` por app. Sem necessidade de 100% de cobertura.

---

## 10. Migrações

- Nunca edite uma migração já aplicada em produção.
- Migrações geradas pelo Django (`makemigrations`), não escritas à mão, salvo data migrations.
- Data migrations devem ter o motivo documentado no topo do arquivo.

---

## 11. Como o Claude Deve se Comportar

### Faça:
- **Sempre apresente o plano e aguarde confirmação antes de implementar** (ver seção 3).
- Pergunte antes de criar arquivos fora da estrutura definida.
- Reutilize o que já existe no projeto.
- Aponte ativamente riscos de segurança e violações de arquitetura que encontrar.
- Prefira o que o Django já oferece nativamente.

### Não faça:
- Não implemente nada sem o plano ter sido aprovado.
- Não crie features, models ou migrations sem confirmar.
- Não adicione dependências sem perguntar.
- Não escreva código verboso — concisão é uma virtude aqui.
- Não assuma stack sem verificar `.env` ou `settings/`.
- Não misture responsabilidades de camadas (ex: query ORM dentro de uma view).

---

## 12. Notas Específicas do Projeto

### Rankings Config Pattern
Adicionar um novo ranking = adicionar um dict à lista em `apps/rankings/config.py`. Nada mais.

```python
RANKINGS = [
    {"id": "hours",    "field": "play_time_ticks",    "label": "Hours Played",       "icon": "⏱️",  "format": "hours"},
    {"id": "catches",  "field": "pokemons_caught",    "label": "Pokémons Caught",    "icon": "🔴", "format": "number"},
    {"id": "pokedex",  "field": "pokedex_registered", "label": "Pokédex Registered", "icon": "📕", "format": "number"},
    {"id": "cards",    "field": "cobbletcg_cards",    "label": "CobbleTCG Cards",    "icon": "🃏", "format": "number"},
    {"id": "battles",  "field": "battles_won",        "label": "Battles Won",        "icon": "⚔️",  "format": "number"},
    {"id": "money",    "field": "cobbledollars",      "label": "CobbleDollars",      "icon": "💰", "format": "currency"},
]
```

### HTML References (htmls-gerados/)
Esses arquivos definem o design visual. Os templates Django devem segui-los fielmente. **Não modificar.**
- `home.html` → base para `templates/home.html`
- `rankings.html` → base para `templates/rankings/page.html`
- `discord_card.html` → base para `templates/rankings/discord_card.html`
  - Renderizado headlessly pelo Playwright. Deve ser self-contained (sem requests externos), 520px de largura.


### Docker
- Serviço único: `cobblemon_returns` (Django + Gunicorn na porta 8000)
- Entrypoint: migrate → collectstatic → gunicorn
- Healthcheck: GET /health/ a cada 30s
- SQLite e staticfiles em named volumes
- Chave SSH montada read-only: `~/.ssh/id_rsa:/run/secrets/sftp_key:ro`
- Nginx (externo, já configurado no VPS) faz proxy para a porta 8000

### Production Subpath
O site roda sob `/cobblemon-returns/` num servidor Nginx compartilhado.
Em `config/settings/prod.py`:
```python
FORCE_SCRIPT_NAME = '/cobblemon-returns'
USE_X_FORWARDED_HOST = True
STATIC_URL = '/cobblemon-returns/static/'
```
Nginx deve passar: `proxy_set_header SCRIPT_NAME /cobblemon-returns;`
