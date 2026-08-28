from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.core.database import get_pool
from app.models.schemas import Servico, ServicoCreate

router = APIRouter()

@router.get("", response_model=list[Servico])
async def listar_servicos(somente_ativos: bool = True):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            if somente_ativos:
                await cur.execute(
                    "SELECT * FROM servicos WHERE ativo = TRUE ORDER BY preco"
                )
            else:
                await cur.execute("SELECT * FROM servicos ORDER BY preco")
            return await cur.fetchall()

@router.post("", response_model=Servico, status_code=201)
async def criar_servico(dados: ServicoCreate):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO servicos (nome, descricao, preco, duracao_minutos)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (dados.nome, dados.descricao, dados.preco, dados.duracao_minutos),
            )
            return await cur.fetchone()

@router.patch("/{servico_id}/status", response_model=Servico)
async def alternar_status_servico(servico_id: UUID, ativo: bool):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE servicos SET ativo = %s WHERE id = %s RETURNING *",
                (ativo, servico_id),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(404, "Serviço não encontrado")
            return row

@router.delete("/{servico_id}")
async def excluir_servico(servico_id: UUID):
    try:
        pool = await get_pool() # 1. Conexão devidamente instanciada
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "DELETE FROM servicos WHERE id = %s",
                    (servico_id,) # 2. UUID passado corretamente
                )
            await conn.commit() # 3. Commit CRUCIAL para efetivar a exclusão
            
        return {"mensagem": "Serviço excluído com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))