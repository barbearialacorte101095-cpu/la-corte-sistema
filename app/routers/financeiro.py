from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Query

from app.core.database import get_pool
from app.models.schemas import ResumoFinanceiro, Transacao, TransacaoCreate

router = APIRouter()


@router.get("/transacoes", response_model=list[Transacao])
async def listar_transacoes(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    tipo: str | None = Query(None, pattern="^(entrada|saida)$"),
):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            filtros = []
            params: list = []

            if data_inicio:
                filtros.append("data_transacao::date >= %s")
                params.append(data_inicio)
            if data_fim:
                filtros.append("data_transacao::date <= %s")
                params.append(data_fim)
            if tipo:
                filtros.append("tipo = %s")
                params.append(tipo)

            where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

            await cur.execute(
                f"""
                SELECT * FROM transacoes_financeiras
                {where}
                ORDER BY data_transacao DESC
                """,
                params,
            )
            return await cur.fetchall()


@router.post("/transacoes", response_model=Transacao, status_code=201)
async def registrar_transacao(dados: TransacaoCreate):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO transacoes_financeiras
                    (tipo, categoria, valor, descricao, agendamento_id,
                     barbeiro_id, data_transacao)
                VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, now()))
                RETURNING *
                """,
                (
                    dados.tipo,
                    dados.categoria,
                    dados.valor,
                    dados.descricao,
                    dados.agendamento_id,
                    dados.barbeiro_id,
                    dados.data_transacao,
                ),
            )
            return await cur.fetchone()


@router.get("/resumo", response_model=ResumoFinanceiro)
async def resumo_financeiro(
    data_inicio: date = Query(..., description="Início do período (YYYY-MM-DD)"),
    data_fim: date = Query(..., description="Fim do período (YYYY-MM-DD)"),
):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    COALESCE(SUM(valor) FILTER (WHERE tipo = 'entrada'), 0) AS entradas,
                    COALESCE(SUM(valor) FILTER (WHERE tipo = 'saida'), 0) AS saidas
                FROM transacoes_financeiras
                WHERE data_transacao::date BETWEEN %s AND %s
                """,
                (data_inicio, data_fim),
            )
            row = await cur.fetchone()
            entradas: Decimal = row["entradas"]
            saidas: Decimal = row["saidas"]

            await cur.execute(
                """
                SELECT COALESCE(SUM(valor), 0) AS total FROM transacoes_financeiras
                WHERE categoria = 'comissao'
                  AND data_transacao::date BETWEEN %s AND %s
                """,
                (data_inicio, data_fim),
            )
            comissoes = (await cur.fetchone())["total"]

            return ResumoFinanceiro(
                entradas=entradas,
                saidas=saidas,
                saldo=entradas - saidas,
                comissoes_pendentes=comissoes,
            )
