# La Corte Barber Shop

Sistema de agendamento online + painel financeiro para a barbearia La Corte.

## Stack

- **Front-end:** HTML + Tailwind (via CDN) + JS puro, em `public/`
- **Back-end:** FastAPI (Python 3.12), rodando como Serverless Function na Vercel
- **Banco:** PostgreSQL no Supabase (free tier)

## Setup local

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env.local
# edite .env.local com a connection string do Supabase (pooler, porta 6543)

# carregue as variáveis e suba a API
export $(cat .env.local | xargs)   # Windows: use um pacote como python-dotenv-cli
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`. Teste em `http://localhost:8000/api/health`.

Para servir o front-end localmente, abra `public/index.html` num Live Server
(ou `python -m http.server` dentro de `public/`), mas lembre que as chamadas
`fetch("/api/...")` só vão funcionar de fato depois do deploy na Vercel — ou
se você rodar um proxy reverso local apontando `/api` para o Uvicorn.

## Banco de dados

1. Crie um projeto em [supabase.com](https://supabase.com).
2. Abra o **SQL Editor** e rode o arquivo `schema.sql` deste projeto inteiro,
   de uma vez.
3. Em **Project Settings → Database**, copie a connection string do modo
   **Transaction Pooler** (porta `6543`) — é ela que vai em `DATABASE_URL`.

## Deploy na Vercel

1. Suba este projeto para um repositório no GitHub.
2. Na Vercel, **Add New Project** → importe o repositório.
3. Em **Settings → Environment Variables**, cadastre `DATABASE_URL` (e
   `ALLOWED_ORIGINS`, com a URL final do seu domínio Vercel).
4. Deploy. A Vercel lê o `vercel.json` e expõe:
   - `/api/*` → a função Python (FastAPI)
   - `/` e demais rotas → os arquivos estáticos de `public/`

## Estrutura

```
la-corte-barbershop/
├── api/index.py            # entrypoint da Serverless Function
├── app/
│   ├── core/                # config + pool de conexão
│   ├── models/schemas.py    # modelos Pydantic
│   ├── routers/              # agendamentos, barbeiros, servicos, financeiro
│   └── main.py
├── public/
│   ├── index.html            # agendamento do cliente
│   ├── admin.html             # painel administrativo
│   └── assets/{css,js}/
├── schema.sql
├── requirements.txt
└── vercel.json
```

## Próximos passos sugeridos

- Autenticação no `admin.html` (o Supabase Auth resolve isso de graça).
- Notificação por WhatsApp/e-mail ao confirmar um agendamento.
- Tela de gestão de barbeiros e serviços (os endpoints já existem, falta a UI).
- Gráfico de faturamento por período no dashboard (dados já vêm de `/api/financeiro/resumo`).
