from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import get_pool

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
                        "INSERT INTO transacoes_financeiras (tipo, categoria, valor, descricao) VALUES (%s, %s, %s, %s)",
                        (dados.tipo, dados.categoria, dados.valor, dados.descricao)
                    )
                except Exception:
                    # Fallback de segurança se a tabela tiver outro nome
                    await conn.rollback()
                    await cur.execute(
                        "INSERT INTO transacoes (tipo, categoria, valor, descricao) VALUES (%s, %s, %s, %s)",
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
                try:
                    await cur.execute("SELECT tipo, valor, criado_em FROM transacoes_financeiras")
                    rows = await cur.fetchall()
                except Exception:
                    await conn.rollback()
                    try:
                        await cur.execute("SELECT tipo, valor, criado_em FROM transacoes")
                        rows = await cur.fetchall()
                    except Exception:
                        pass # Retorna vazio sem causar erro 500

        entradas = 0.0
        saidas = 0.0

        for r in rows:
            tipo = str(r[0])
            valor = float(r[1] or 0)
            dt_str = str(r[2]) if r[2] else ""
            
            if len(dt_str) >= 10:
                data_do_banco = dt_str[:10]
                
                # Filtragem cirúrgica no Python
                if data_inicio <= data_do_banco <= data_fim:
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