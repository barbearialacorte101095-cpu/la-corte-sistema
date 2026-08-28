from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_pool
from datetime import datetime

router = APIRouter()

class TransacaoCreate(BaseModel):
    tipo: str
    categoria: str
    valor: float
    descricao: str = None

@router.post("/transacoes")
async def criar_transacao(dados: TransacaoCreate):
    try:
        pool = await get_pool()
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                try:
                    await cur.execute(
                        "INSERT INTO transacoes (tipo, categoria, valor, descricao) VALUES (%s, %s, %s, %s)",
                        (dados.tipo, dados.categoria, dados.valor, dados.descricao)
                    )
                except Exception:
                    await conn.rollback()
                    await cur.execute(
                        "INSERT INTO transacoes_financeiras (tipo, categoria, valor, descricao) VALUES (%s, %s, %s, %s)",
                        (dados.tipo, dados.categoria, dados.valor, dados.descricao)
                    )
            await conn.commit()
        return {"mensagem": "Transação registrada com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resumo")
async def resumo_financeiro(data_inicio: str, data_fim: str):
    try:
        pool = await get_pool()
        rows = []
        async with pool.connection() as conn:
            async with conn.cursor() as cur:
                # O Python vai testar todos os nomes possíveis de colunas até achar a certa
                # Os aliases (AS tipo/valor/dt) garantem chaves previsíveis no dict
                # retornado por cada linha, independente do nome real da coluna de data.
                queries = [
                    "SELECT tipo AS tipo, valor AS valor, created_at AS dt FROM transacoes",
                    "SELECT tipo AS tipo, valor AS valor, criado_em AS dt FROM transacoes",
                    "SELECT tipo AS tipo, valor AS valor, data_transacao AS dt FROM transacoes",
                    "SELECT tipo AS tipo, valor AS valor, created_at AS dt FROM transacoes_financeiras",
                    "SELECT tipo AS tipo, valor AS valor, criado_em AS dt FROM transacoes_financeiras"
                ]
                for q in queries:
                    try:
                        await cur.execute(q)
                        rows = await cur.fetchall()
                        break
                    except Exception:
                        await conn.rollback()

        entradas = 0.0
        saidas = 0.0

        for r in rows:
            tipo = str(r["tipo"]).lower()
            try:
                valor = float(r["valor"])
            except:
                valor = 0.0
            
            val_dt = r["dt"]
            # O Python decide como formatar independente de como o banco devolver
            if isinstance(val_dt, datetime):
                data_str = val_dt.strftime("%Y-%m-%d")
            else:
                data_str = str(val_dt)[:10]

            if data_inicio <= data_str <= data_fim:
                if tipo == 'entrada':
                    entradas += valor
                else:
                    saidas += valor

        return {
            "entradas": entradas,
            "saidas": saidas,
            "saldo": entradas - saidas
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))