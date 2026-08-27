from datetime import date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.database import get_pool
from app.models.schemas import Agendamento, AgendamentoCreate, AgendamentoStatusUpdate

router = APIRouter()


@router.get("", response_model=list[dict])
async def listar_agendamentos(
    data: date | None = Query(None, description="Filtra pela data (YYYY-MM-DD)"),
    barbeiro_id: UUID | None = None,
):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            filtros = []
            params: list = []

            if data:
                filtros.append("a.data_hora_inicio::date = %s")
                params.append(data)
            if barbeiro_id:
                filtros.append("a.barbeiro_id = %s")
                params.append(barbeiro_id)

            where = f"WHERE {' AND '.join(filtros)}" if filtros else ""

            await cur.execute(
                f"""
                SELECT
                    a.id, a.data_hora_inicio, a.data_hora_fim, a.status, a.observacoes,
                    c.nome AS cliente_nome, c.telefone AS cliente_telefone,
                    b.nome AS barbeiro_nome,
                    s.nome AS servico_nome, s.preco AS servico_preco
                FROM agendamentos a
                JOIN clientes c ON c.id = a.cliente_id
                JOIN barbeiros b ON b.id = a.barbeiro_id
                JOIN servicos s ON s.id = a.servico_id
                {where}
                ORDER BY a.data_hora_inicio
                """,
                params,
            )
            return await cur.fetchall()


@router.post("", response_model=Agendamento, status_code=201)
async def criar_agendamento(dados: AgendamentoCreate):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            # Busca a duração do serviço para calcular o horário de término
            await cur.execute(
                "SELECT duracao_minutos FROM servicos WHERE id = %s AND ativo = TRUE",
                (dados.servico_id,),
            )
            servico = await cur.fetchone()
            if not servico:
                raise HTTPException(404, "Serviço não encontrado ou inativo")

            data_hora_fim = dados.data_hora_inicio + timedelta(
                minutes=servico["duracao_minutos"]
            )

            # Upsert simples de cliente por telefone
            await cur.execute(
                """
                INSERT INTO clientes (nome, telefone, email)
                VALUES (%s, %s, %s)
                ON CONFLICT (telefone) DO UPDATE SET nome = EXCLUDED.nome
                RETURNING id
                """,
                (dados.cliente_nome, dados.cliente_telefone, dados.cliente_email),
            )
            cliente = await cur.fetchone()

            try:
                await cur.execute(
                    """
                    INSERT INTO agendamentos
                        (cliente_id, barbeiro_id, servico_id, data_hora_inicio,
                         data_hora_fim, observacoes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        cliente["id"],
                        dados.barbeiro_id,
                        dados.servico_id,
                        dados.data_hora_inicio,
                        data_hora_fim,
                        dados.observacoes,
                    ),
                )
            except Exception as exc:
                # Violação da constraint de exclusão (sem_conflito_horario)
                if "sem_conflito_horario" in str(exc):
                    raise HTTPException(
                        409, "Esse barbeiro já tem um horário marcado nesse intervalo"
                    )
                raise

            return await cur.fetchone()


@router.patch("/{agendamento_id}/status", response_model=Agendamento)
async def atualizar_status(agendamento_id: UUID, dados: AgendamentoStatusUpdate):
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE agendamentos SET status = %s WHERE id = %s RETURNING *",
                (dados.status, agendamento_id),
            )
            row = await cur.fetchone()
            if not row:
                raise HTTPException(404, "Agendamento não encontrado")
            return row


@router.get("/disponibilidade", response_model=list[str])
async def horarios_disponiveis(
    barbeiro_id: UUID, servico_id: UUID, data: date
):
    """Retorna os horários (HH:MM) livres para um barbeiro em um dia,
    considerando a duração do serviço e os agendamentos já existentes."""
    pool = await get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT duracao_minutos FROM servicos WHERE id = %s", (servico_id,)
            )
            servico = await cur.fetchone()
            if not servico:
                raise HTTPException(404, "Serviço não encontrado")
            duracao = timedelta(minutes=servico["duracao_minutos"])

            dia_semana = data.weekday()
            dia_semana = (dia_semana + 1) % 7  # Python: seg=0 -> banco: dom=0

            await cur.execute(
                """
                SELECT hora_inicio, hora_fim FROM horarios_disponiveis
                WHERE barbeiro_id = %s AND dia_semana = %s
                """,
                (barbeiro_id, dia_semana),
            )
            janelas = await cur.fetchall()
            if not janelas:
                return []

            await cur.execute(
                """
                SELECT data_hora_inicio, data_hora_fim FROM agendamentos
                WHERE barbeiro_id = %s
                  AND data_hora_inicio::date = %s
                  AND status NOT IN ('cancelado', 'nao_compareceu')
                """,
                (barbeiro_id, data),
            )
            ocupados = await cur.fetchall()

            livres: list[str] = []
            slot_minutos = 30

            for janela in janelas:
                atual = datetime.combine(data, janela["hora_inicio"])
                fim_janela = datetime.combine(data, janela["hora_fim"])

                while atual + duracao <= fim_janela:
                    fim_slot = atual + duracao
                    conflita = any(
                        atual < o["data_hora_fim"] and fim_slot > o["data_hora_inicio"]
                        for o in ocupados
                    )
                    if not conflita:
                        livres.append(atual.strftime("%H:%M"))
                    atual += timedelta(minutes=slot_minutos)

            return livres
