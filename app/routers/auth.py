import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# Define o formato dos dados que o JavaScript vai enviar
class LoginData(BaseModel):
    username: str
    password: str

@router.post("/login")
async def fazer_login(dados: LoginData):
    # Puxa as credenciais seguras do arquivo .env (ou usa um padrão temporário se falhar)
    usuario_correto = os.getenv("ADMIN_USER", "admin")
    senha_correta = os.getenv("ADMIN_PASS", "admin123")

    # Confere se o que foi digitado bate com o .env
    if dados.username == usuario_correto and dados.password == senha_correta:
        # Se estiver correto, devolve o token que o login.js está esperando
        return {"token": "token_autorizado_la_corte_pdv"}
    else:
        # Se errar, devolve o Erro 401 (Não Autorizado)
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")