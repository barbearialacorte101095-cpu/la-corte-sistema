from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import get_pool
from uuid import UUID

router = APIRouter()

# Contrato corrigido: servico_id agora aceita UUID
class AgendamentoCliente(BaseModel):
    cliente_nome: str
    cliente_telefone: str
    servico_id: UUID 
    data_hora_inicio: datetime

@router.get("")
async def listar_agendamentos(data: str = None):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            if data:
                await cur.execute(
                    "SELECT id, servico_id, data_hora_inicio, status, cliente_nome, cliente_telefone FROM agendamentos WHERE DATE(data_hora_inicio) = %s ORDER BY data_hora_inicio",
                    (data,)
                )
            else:
                await cur.execute("SELECT id, servico_id, data_hora_inicio, status, cliente_nome, cliente_telefone FROM agendamentos ORDER BY data_hora_inicio")
            
            rows = await cur.fetchall()
            agendamentos = []
            for r in rows:
                agendamentos.append({
                    "id": r[0],
                    "servico_id": r[1],
                    "data_hora_inicio": r[2].isoformat() if r[2] else None,
                    "status": r[3],
                    "cliente_nome": r[4] if r[4] else "Cliente",
                    "cliente_telefone": r[5] if r[5] else ""
                })
            return agendamentos

@router.get("/disponibilidade")
async def verificar_disponibilidade(data: str):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT data_hora_inicio FROM agendamentos WHERE DATE(data_hora_inicio) = %s AND status != 'cancelado'",
                (data,)
            )
            rows = await cur.fetchall()
            horarios_ocupados = [r[0].strftime("%H:%M") for r in rows if r[0]]
            
            horarios_disponiveis = []
            hora_atual = datetime.strptime("09:00", "%H:%M")
            hora_fim = datetime.strptime("19:30", "%H:%M")
            
            while hora_atual <= hora_fim:
                str_hora = hora_atual.strftime("%H:%M")
                if str_hora not in horarios_ocupados:
                    horarios_disponiveis.append(str_hora)
                hora_atual += timedelta(minutes=30)
                
            return horarios_disponiveis

@router.post("")
async def criar_agendamento(dados: AgendamentoCliente):
    try:
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id FROM agendamentos WHERE data_hora_inicio = %s AND status != 'cancelado'",
                    (dados.data_hora_inicio,)
                )
                if await cur.fetchone():
                    raise HTTPException(status_code=400, detail="Este horário acabou de ser reservado.")

                await cur.execute(
                    """
                    INSERT INTO agendamentos (servico_id, data_hora_inicio, data_hora_fim, status, cliente_nome, cliente_telefone)
                    VALUES (%s, %s, %s, 'pendente', %s, %s)
                    """,
                    (
                        dados.servico_id, 
                        dados.data_hora_inicio, 
                        dados.data_hora_inicio + timedelta(minutes=30), 
                        dados.cliente_nome, 
                        dados.cliente_telefone
                    )
                )
            await conn.commit()
        return {"mensagem": "Agendamento confirmado!"}
    except Exception as e:
        # Se falhar no banco, devolve o erro organizado para o site
        raise HTTPException(status_code=500, detail=str(e))