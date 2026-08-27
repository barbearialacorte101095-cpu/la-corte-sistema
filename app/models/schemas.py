from datetime import datetime, time
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---------- Barbeiros ----------

class BarbeiroBase(BaseModel):
    nome: str = Field(..., max_length=120)
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    percentual_comissao: Decimal = Field(default=Decimal("50.00"), ge=0, le=100)


class BarbeiroCreate(BarbeiroBase):
    pass


class Barbeiro(BarbeiroBase):
    id: UUID
    ativo: bool
    criado_em: datetime


# ---------- Clientes ----------

class ClienteBase(BaseModel):
    nome: str = Field(..., max_length=120)
    telefone: str = Field(..., max_length=20)
    email: Optional[EmailStr] = None


class ClienteCreate(ClienteBase):
    pass


class Cliente(ClienteBase):
    id: UUID
    criado_em: datetime


# ---------- Serviços ----------

class ServicoBase(BaseModel):
    nome: str = Field(..., max_length=100)
    descricao: Optional[str] = None
    preco: Decimal = Field(..., gt=0)
    duracao_minutos: int = Field(default=30, gt=0)


class ServicoCreate(ServicoBase):
    pass


class Servico(ServicoBase):
    id: UUID
    ativo: bool


# ---------- Horários disponíveis ----------

class HorarioDisponivel(BaseModel):
    barbeiro_id: UUID
    dia_semana: int = Field(..., ge=0, le=6)
    hora_inicio: time
    hora_fim: time


# ---------- Agendamentos ----------

class AgendamentoCreate(BaseModel):
    cliente_nome: str
    cliente_telefone: str
    cliente_email: Optional[EmailStr] = None
    barbeiro_id: UUID
    servico_id: UUID
    data_hora_inicio: datetime
    observacoes: Optional[str] = None


class Agendamento(BaseModel):
    id: UUID
    cliente_id: UUID
    barbeiro_id: UUID
    servico_id: UUID
    data_hora_inicio: datetime
    data_hora_fim: datetime
    status: str
    observacoes: Optional[str] = None
    criado_em: datetime


class AgendamentoStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pendente|confirmado|concluido|cancelado|nao_compareceu)$")


# ---------- Financeiro ----------

class TransacaoCreate(BaseModel):
    tipo: str = Field(..., pattern="^(entrada|saida)$")
    categoria: str = Field(
        ..., pattern="^(servico|produto|comissao|despesa_fixa|despesa_variavel|outro)$"
    )
    valor: Decimal = Field(..., gt=0)
    descricao: Optional[str] = None
    agendamento_id: Optional[UUID] = None
    barbeiro_id: Optional[UUID] = None
    data_transacao: Optional[datetime] = None


class Transacao(TransacaoCreate):
    id: UUID
    criado_em: datetime


class ResumoFinanceiro(BaseModel):
    entradas: Decimal
    saidas: Decimal
    saldo: Decimal
    comissoes_pendentes: Decimal
