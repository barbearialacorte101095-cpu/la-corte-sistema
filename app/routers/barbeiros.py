from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.core.database import get_pool
from app.models.schemas import Barbeiro, BarbeiroCreate

router = APIRouter()


@router.get("", response_model=list[Barbeiro])
async def listar_barbeiros(somente_ativos: bool = True):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            if somente_ativos:
                await cur.execute(
                    "SELECT * FROM barbeiros WHERE ativo = TRUE ORDER BY nome"
                )
            else:
                await cur.execute("SELECT * FROM barbeiros ORDER BY nome")
            return await cur.fetchall()


@router.post("", response_model=Barbeiro, status_code=201)
async def criar_barbeiro(dados: BarbeiroCreate):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO barbeiros (nome, telefone, email, percentual_comissao)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (dados.nome, dados.telefone, dados.email, dados.percentual_comissao),
            )
            return await cur.fetchone()


@router.patch("/{barbeiro_id}/status", response_model=Barbeiro)
async def alternar_status_barbeiro(barbeiro_id: UUID, ativo: bool):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE barbeiros SET ativo = %s WHERE id = %s RETURNING *",
                (ativo, barbeiro_id),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(404, "Barbeiro não encontrado")
            return row
