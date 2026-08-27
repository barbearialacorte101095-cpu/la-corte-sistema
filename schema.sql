-- ============================================
-- LA CORTE BARBER SHOP — Schema PostgreSQL
-- Rode este script inteiro no SQL Editor do Supabase
-- ============================================

CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE barbeiros (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(120) NOT NULL,
    telefone VARCHAR(20),
    email VARCHAR(150) UNIQUE,
    percentual_comissao NUMERIC(5,2) NOT NULL DEFAULT 50.00,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE clientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(120) NOT NULL,
    telefone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(150),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE servicos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco NUMERIC(10,2) NOT NULL,
    duracao_minutos INT NOT NULL DEFAULT 30,
    ativo BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE horarios_disponiveis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    barbeiro_id UUID NOT NULL REFERENCES barbeiros(id) ON DELETE CASCADE,
    dia_semana SMALLINT NOT NULL CHECK (dia_semana BETWEEN 0 AND 6), -- 0 = domingo
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL
);

CREATE TYPE status_agendamento AS ENUM (
    'pendente', 'confirmado', 'concluido', 'cancelado', 'nao_compareceu'
);

CREATE TABLE agendamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    barbeiro_id UUID NOT NULL REFERENCES barbeiros(id),
    servico_id UUID NOT NULL REFERENCES servicos(id),
    data_hora_inicio TIMESTAMPTZ NOT NULL,
    data_hora_fim TIMESTAMPTZ NOT NULL,
    status status_agendamento NOT NULL DEFAULT 'pendente',
    observacoes TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT sem_conflito_horario EXCLUDE USING gist (
        barbeiro_id WITH =,
        tstzrange(data_hora_inicio, data_hora_fim) WITH &&
    )
);

CREATE TYPE tipo_transacao AS ENUM ('entrada', 'saida');
CREATE TYPE categoria_transacao AS ENUM (
    'servico', 'produto', 'comissao', 'despesa_fixa', 'despesa_variavel', 'outro'
);

CREATE TABLE transacoes_financeiras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tipo tipo_transacao NOT NULL,
    categoria categoria_transacao NOT NULL,
    valor NUMERIC(10,2) NOT NULL CHECK (valor > 0),
    descricao VARCHAR(255),
    agendamento_id UUID REFERENCES agendamentos(id),
    barbeiro_id UUID REFERENCES barbeiros(id),
    data_transacao TIMESTAMPTZ NOT NULL DEFAULT now(),
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_agendamentos_data ON agendamentos (data_hora_inicio);
CREATE INDEX idx_agendamentos_barbeiro ON agendamentos (barbeiro_id, data_hora_inicio);
CREATE INDEX idx_transacoes_data ON transacoes_financeiras (data_transacao);

-- ============================================
-- Dados de exemplo (opcional — apague se não quiser)
-- ============================================

INSERT INTO barbeiros (nome, telefone, percentual_comissao) VALUES
    ('Diego Ramos', '21999990001', 50.00),
    ('Bruno Alves', '21999990002', 45.00);

INSERT INTO servicos (nome, descricao, preco, duracao_minutos) VALUES
    ('Corte Degradê', 'Corte moderno com máquina e tesoura', 55.00, 40),
    ('Barba Completa', 'Toalha quente, navalha e finalização', 40.00, 30),
    ('Corte + Barba', 'Combo completo', 85.00, 60),
    ('Sobrancelha', 'Design com navalha', 20.00, 15);

-- Segunda a sábado, 9h às 19h, para os dois barbeiros de exemplo
INSERT INTO horarios_disponiveis (barbeiro_id, dia_semana, hora_inicio, hora_fim)
SELECT b.id, dia, '09:00', '19:00'
FROM barbeiros b, generate_series(1, 6) AS dia;
