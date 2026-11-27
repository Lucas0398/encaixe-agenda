-- EncaixeAgenda — schema inicial (Postgres 14+).
-- Carregado automaticamente pelo docker-compose na primeira subida do banco.
-- Quando o schema começar a mudar com dados reais, migrar para Alembic.

-- Clínicas e regras (LS-31) -------------------------------------------------

create table clinicas (
    id                        uuid primary key default gen_random_uuid(),
    nome                      text not null,
    whatsapp_phone_number_id  text unique,            -- identifica a clínica no webhook
    regras                    jsonb not null default '{}', -- validado por encaixe.dominio.regras.RegrasClinica
    criado_em                 timestamptz not null default now()
);

create table profissionais (
    id                  uuid primary key default gen_random_uuid(),
    clinica_id          uuid not null references clinicas(id),
    nome                text not null,
    google_calendar_id  text not null,
    ativo               boolean not null default true
);

create table servicos (
    id              uuid primary key default gen_random_uuid(),
    clinica_id      uuid not null references clinicas(id),
    nome            text not null,
    duracao_min     integer not null check (duracao_min > 0),
    capacidade      integer not null default 1 check (capacidade > 0),
    valor_centavos  integer not null default 0 check (valor_centavos >= 0),
    ativo           boolean not null default true
);

create table expedientes (
    id               uuid primary key default gen_random_uuid(),
    profissional_id  uuid not null references profissionais(id),
    dia_semana       smallint not null check (dia_semana between 0 and 6), -- 0 = segunda
    inicio           time not null,
    fim              time not null,
    check (fim > inicio)
);

-- Pacientes e conversas ------------------------------------------------------

create table pacientes (
    id          uuid primary key default gen_random_uuid(),
    clinica_id  uuid not null references clinicas(id),
    telefone    text not null,  -- formato wa_id, ex.: 5582999990000
    nome        text,
    criado_em   timestamptz not null default now(),
    unique (clinica_id, telefone)
);

create table conversas (
    id                 uuid primary key default gen_random_uuid(),
    clinica_id         uuid not null references clinicas(id),
    paciente_id        uuid not null references pacientes(id),
    estado             jsonb not null default '{}', -- em que passo do fluxo o paciente está
    bot_pausado_ate    timestamptz,                 -- escalonamento para humano (LS-23)
    ultima_entrada_em  timestamptz,                 -- define a janela de 24h do WhatsApp
    unique (clinica_id, paciente_id)
);

-- Log de mensagens. O wamid como chave garante idempotência do webhook.
-- LGPD: apagar `conteudo` após o prazo de retenção (LS-27).
create table mensagens_whatsapp (
    wamid       text primary key,
    clinica_id  uuid not null references clinicas(id),
    telefone    text not null,
    direcao     text not null check (direcao in ('entrada', 'saida')),
    tipo        text not null,
    conteudo    jsonb,
    status      text,          -- sent, delivered, read, failed (só saída)
    criado_em   timestamptz not null default now()
);

-- Agendamentos (LS-32) -------------------------------------------------------

create type status_agendamento as enum (
    'pendente_pagamento', 'confirmado', 'presenca_confirmada', 'realizado',
    'faltou', 'cancelado_paciente', 'cancelado_clinica', 'cancelado_falta_pagamento'
);

create table agendamentos (
    id               uuid primary key default gen_random_uuid(),
    clinica_id       uuid not null references clinicas(id),
    paciente_id      uuid not null references pacientes(id),
    profissional_id  uuid not null references profissionais(id),
    servico_id       uuid not null references servicos(id),
    inicio           timestamptz not null,
    fim              timestamptz not null,
    status           status_agendamento not null,
    google_event_id  text,
    origem           text not null default 'bot' check (origem in ('bot', 'manual')),
    criado_em        timestamptz not null default now(),
    atualizado_em    timestamptz not null default now(),
    check (fim > inicio)
);

create index agendamentos_ativos_por_profissional
    on agendamentos (profissional_id, inicio)
    where status in ('pendente_pagamento', 'confirmado', 'presenca_confirmada');

-- Trava contra dois pacientes no mesmo horário (LS-19): ao gravar, dentro da
-- mesma transação:
--   select pg_advisory_xact_lock(hashtext(:profissional_id::text));
--   -- recontar a ocupação no intervalo e comparar com a capacidade do serviço
--   insert into agendamentos ...;
-- A trava é por profissional e liberada no commit.

create table agendamento_historico (
    id              bigserial primary key,
    agendamento_id  uuid not null references agendamentos(id),
    de              status_agendamento,
    para            status_agendamento not null,
    motivo          text not null,
    autor           text not null,
    em              timestamptz not null default now()
);

-- Fila de tarefas agendadas (LS-33) -------------------------------------------
-- Worker pega tarefas com:
--   select ... from tarefas where status = 'pendente' and executar_em <= now()
--   order by executar_em for update skip locked limit 10;

create table tarefas (
    id           bigserial primary key,
    tipo         text not null,               -- ex.: checar_pagamento, lembrete_d1
    executar_em  timestamptz not null,
    payload      jsonb not null default '{}',
    chave_unica  text unique,                 -- evita agendar a mesma tarefa duas vezes
    status       text not null default 'pendente'
                 check (status in ('pendente', 'executando', 'concluida', 'cancelada', 'falhou')),
    tentativas   integer not null default 0,
    ultimo_erro  text,
    criado_em    timestamptz not null default now()
);

create index tarefas_pendentes on tarefas (executar_em) where status = 'pendente';

-- Pagamentos (LS-36) -----------------------------------------------------------

create table pagamentos (
    id              uuid primary key default gen_random_uuid(),
    agendamento_id  uuid not null references agendamentos(id),
    gateway         text not null,        -- asaas, mercadopago
    gateway_id      text unique,          -- id da cobrança no gateway (idempotência do webhook)
    valor_centavos  integer not null check (valor_centavos > 0),
    status          text not null default 'pendente'
                    check (status in ('pendente', 'pago', 'expirado', 'estornado', 'cancelado')),
    pix_copia_cola  text,
    expira_em       timestamptz,
    pago_em         timestamptz,
    criado_em       timestamptz not null default now()
);
