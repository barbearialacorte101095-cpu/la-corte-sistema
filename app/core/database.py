from psycopg_pool import AsyncConnectionPool
from psycopg.rows import dict_row

from app.core.config import settings

# Pool pequeno de propósito: cada invocação serverless deve segurar
# poucas conexões simultâneas, já que o Postgres tem um teto baixo delas.
# O pool é reaproveitado entre invocações "quentes" da mesma function.
pool = AsyncConnectionPool(
    conninfo=settings.DATABASE_URL,
    min_size=0,
    max_size=3,
    open=False,
    kwargs={"row_factory": dict_row},
)


async def get_pool() -> AsyncConnectionPool:
    """Garante que o pool está aberto e o retorna para uso nos routers."""
    if pool.closed:
        await pool.open()
    return pool
