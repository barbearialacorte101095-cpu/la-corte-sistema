from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import get_pool
from uuid import UUID

router = APIRouter()

class AgendamentoCliente(BaseModel):
    cliente_nome: str
    cliente_telefone: str
    servico_id: UUID 
    data_hora_inicio: datetime

@router.get("")
async def listar_agendamentos(data: str = None):
    try:
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                if data:
                    # O TO_CHAR força o banco a entregar a data já formatada como texto limpo
                    await cur.execute(
                        """
                        SELECT id, servico_id, TO_CHAR(data_hora_inicio, 'YYYY-MM-DD"T"HH24:MI:SS'), status, cliente_nome, cliente_telefone 
                        FROM agendamentos 
                        WHERE data_hora_inicio::date = %s::date 
                        ORDER BY data_hora_inicio
                        """,
                        (data,)
                    )
                else:
                    await cur.execute(
                        """
                        SELECT id, servico_id, TO_CHAR(data_hora_inicio, 'YYYY-MM-DD"T"HH24:MI:SS'), status, cliente_nome, cliente_telefone 
                        FROM agendamentos 
                        ORDER BY data_hora_inicio
                        """
                    )
                
                rows = await cur.fetchall()
                agendamentos = []
                for r in rows:
                    agendamentos.append({
                        "id": str(r[0]),
                        "servico_id": str(r[1]) if r[1] else None,
                        "data_hora_inicio": str(r[2]) if r[2] else None,
                        "status": r[3],
                        "cliente_nome": r[4] if r[4] else "Cliente",
                        "cliente_telefone": r[5] if r[5] else ""
                    })
                return agendamentos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar: {str(e)}")

@router.get("/disponibilidade")
async def verificar_disponibilidade(data: str):
    try:
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                # O TO_CHAR extrai apenas a Hora e o Minuto direto no banco
                await cur.execute(
                    "SELECT TO_CHAR(data_hora_inicio, 'HH24:MI') FROM agendamentos WHERE data_hora_inicio::date = %s::date AND status != 'cancelado'",
                    (data,)
                )
                rows = await cur.fetchall()
                horarios_ocupados = [r[0] for r in rows if r[0]]
                
                horarios_disponiveis = []
                hora_atual = datetime.strptime("09:00", "%H:%M")
                hora_fim = datetime.strptime("19:30", "%H:%M")
                
                while hora_atual <= hora_fim:
                    str_hora = hora_atual.strftime("%H:%M")
                    if str_hora not in horarios_ocupados:
                        horarios_disponiveis.append(str_hora)
                    hora_atual += timedelta(minutes=30)
                    
                return horarios_disponiveis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na disponibilidade: {str(e)}")

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
                    raise HTTPException(status_code=400, detail="Este horário já está reservado.")

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
        raise HTTPException(status_code=500, detail=str(e))