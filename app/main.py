from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import agendamentos, barbeiros, financeiro, servicos, auth

app = FastAPI(title="La Corte Barber Shop API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agendamentos.router, prefix="/api/agendamentos", tags=["Agendamentos"])
app.include_router(barbeiros.router, prefix="/api/barbeiros", tags=["Barbeiros"])
app.include_router(servicos.router, prefix="/api/servicos", tags=["Serviços"])
app.include_router(financeiro.router, prefix="/api/financeiro", tags=["Financeiro"])
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticação"])


@app.get("/api/health", tags=["Sistema"])
def health():
    return {"status": "ok", "ambiente": settings.ENV}
