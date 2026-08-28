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
                    # Método 100% seguro: Transforma a data do banco em texto antes de buscar
                    await cur.execute(
                        """
                        SELECT id, servico_id, data_hora_inicio, status, cliente_nome, cliente_telefone 
                        FROM agendamentos 
                        WHERE CAST(data_hora_inicio AS TEXT) LIKE %s
                        ORDER BY data_hora_inicio
                        """,
                        (f"{data}%",)
                    )
                else:
                    await cur.execute("SELECT id, servico_id, data_hora_inicio, status, cliente_nome, cliente_telefone FROM agendamentos ORDER BY data_hora_inicio")
                
                rows = await cur.fetchall()
                agendamentos = []
                for r in rows:
                    val = r[2]
                    # Garante a formatação ISO do texto
                    data_str = str(val).replace(' ', 'T') if val else None

                    agendamentos.append({
                        "id": str(r[0]),
                        "servico_id": str(r[1]) if r[1] else None,
                        "data_hora_inicio": data_str,
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
                # Busca as datas transformadas em texto para evitar quebra de contrato
                await cur.execute(
                    "SELECT data_hora_inicio FROM agendamentos WHERE CAST(data_hora_inicio AS TEXT) LIKE %s AND status != 'cancelado'",
                    (f"{data}%",)
                )
                rows = await cur.fetchall()
                
                horarios_ocupados = []
                for r in rows:
                    if r[0]:
                        # Corta e pega exatamente a string da hora (Ex: 2026-08-28 13:30 -> 13:30)
                        hora = str(r[0]).replace('T', ' ').split(' ')[1][:5]
                        horarios_ocupados.append(hora)
                
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