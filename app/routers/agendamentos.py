from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import get_pool

router = APIRouter()

class AgendamentoCliente(BaseModel):
    cliente_nome: str
    cliente_telefone: str
    servico_id: str 
    data_hora_inicio: str # Recebe como texto limpo

@router.get("")
async def listar_agendamentos(data: str = None):
    try:
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id, servico_id, data_hora_inicio, status, cliente_nome, cliente_telefone FROM agendamentos")
                rows = await cur.fetchall()
                
        agendamentos = []
        for r in rows:
            dt_val = r[2]
            if not dt_val:
                continue
                
            if isinstance(dt_val, datetime):
                dt_obj = dt_val
            else:
                try:
                    dt_obj = datetime.fromisoformat(str(dt_val).replace('Z', '+00:00'))
                except:
                    continue
                    
            dt_str = dt_obj.strftime("%Y-%m-%d")
            # Filtro inteligente no Python
            if data and dt_str != data:
                continue
                
            agendamentos.append({
                "id": str(r[0]),
                "servico_id": str(r[1]) if r[1] else None,
                "data_hora_inicio": dt_obj.isoformat(),
                "status": str(r[3]) if r[3] else "pendente",
                "cliente_nome": str(r[4]) if r[4] else "Cliente",
                "cliente_telefone": str(r[5]) if r[5] else ""
            })
        
        agendamentos.sort(key=lambda x: x["data_hora_inicio"])
        return agendamentos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/disponibilidade")
async def verificar_disponibilidade(data: str):
    try:
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT data_hora_inicio, status FROM agendamentos")
                rows = await cur.fetchall()
                
        horarios_ocupados = []
        for r in rows:
            status = str(r[1]).lower() if r[1] else ""
            if status == 'cancelado':
                continue
                
            dt_val = r[0]
            if not dt_val:
                continue
                
            if isinstance(dt_val, datetime):
                dt_obj = dt_val
            else:
                try:
                    dt_obj = datetime.fromisoformat(str(dt_val).replace('Z', '+00:00'))
                except:
                    continue
                    
            if dt_obj.strftime("%Y-%m-%d") == data:
                horarios_ocupados.append(dt_obj.strftime("%H:%M"))
        
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
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def criar_agendamento(dados: AgendamentoCliente):
    try:
        dt_inicio = datetime.fromisoformat(dados.data_hora_inicio.replace('Z', ''))
        dt_fim = dt_inicio + timedelta(minutes=30)
        
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                # Verificação cega e absoluta se O MESMO HORÁRIO EXATO foi escolhido
                await cur.execute("SELECT data_hora_inicio, status FROM agendamentos")
                rows = await cur.fetchall()
                for r in rows:
                    if str(r[1]).lower() == 'cancelado':
                        continue
                    val = r[0]
                    if isinstance(val, datetime):
                        if val.replace(tzinfo=None) == dt_inicio.replace(tzinfo=None):
                            raise HTTPException(status_code=400, detail="Este horário já está reservado.")

                await cur.execute(
                    """
                    INSERT INTO agendamentos (servico_id, data_hora_inicio, data_hora_fim, status, cliente_nome, cliente_telefone)
                    VALUES (%s, %s, %s, 'pendente', %s, %s)
                    """,
                    (dados.servico_id, dt_inicio, dt_fim, dados.cliente_nome, dados.cliente_telefone)
                )
            await conn.commit()
        return {"mensagem": "Agendamento confirmado!"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))