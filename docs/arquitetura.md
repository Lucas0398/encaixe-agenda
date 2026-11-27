# Arquitetura

## Visão geral

```
Paciente (WhatsApp)
      │  mensagem
      ▼
Meta Cloud API ──webhook──► API (FastAPI) ──► fila de tarefas ──► worker
                                                     │
                     ┌───────────────────────────────┼──────────────────────┐
                     ▼                               ▼                      ▼
              IA (Claude, tool use)        Domínio (regras puras)      Gateway Pix
              entende o pedido             horários, status, regras    (Asaas / MP)
                     │                               │
                     └──────────────► Google Agenda ◄┘
                                      (fonte da verdade)
                                             │
                                      Postgres (pacientes, agendamentos,
                                      histórico, mensagens, tarefas)
```

## Princípios

1. **O Google Agenda é a fonte da verdade dos horários.** A secretária continua usando a agenda normalmente. O sistema lê de lá antes de oferecer horário e sincroniza as edições manuais (LS-34).
2. **A IA só interpreta; o código decide.** A IA conversa e chama ferramentas (`buscar_horarios`, `criar_agendamento`...). Cada ferramenta valida as regras da clínica e o status antes de agir. A IA nunca grava nada diretamente.
3. **Regras em configuração, não em código.** Tudo que varia por clínica fica em `RegrasClinica` (JSON na tabela `clinicas`). Ver [regras-por-clinica.md](regras-por-clinica.md).
4. **Status só muda por transição permitida.** `dominio/estados.py` define o que pode virar o quê. Cada mudança gera um registro no histórico e pode disparar ações.
5. **Domínio sem dependências.** `src/encaixe/dominio/` não acessa rede nem banco. É onde ficam os testes mais importantes.
6. **Na dúvida, chama humano.** Baixa confiança da IA, reclamação ou erro técnico → pausa o bot para aquele paciente e avisa a secretária.

## Status do agendamento

| De | Pode ir para |
|---|---|
| `pendente_pagamento` | `confirmado` (Pix pago), `cancelado_falta_pagamento` (prazo vencido), cancelamentos |
| `confirmado` | `presenca_confirmada` (respondeu ao lembrete), `realizado`, `faltou`, cancelamentos |
| `presenca_confirmada` | `realizado`, `faltou`, cancelamentos |
| `cancelado_falta_pagamento` | `confirmado` (Pix chegou atrasado e o horário ainda está livre) |
| `realizado`, `faltou`, `cancelado_paciente`, `cancelado_clinica` | — (finais) |

Cancelamentos = `cancelado_paciente` ou `cancelado_clinica`.

Status ativos (ocupam o horário): `pendente_pagamento`, `confirmado`, `presenca_confirmada`.
Clínica sem pagamento antecipado: o agendamento já nasce `confirmado`.

## Garantia contra horário duplicado

Dois pacientes podem escolher o mesmo horário quase ao mesmo tempo. Para evitar isso:

1. `horarios_livres` oferece só o que cabe na capacidade do serviço.
2. Na hora de gravar, dentro de uma transação: trava por profissional (`pg_advisory_xact_lock`), recontagem da ocupação e só então `insert` + criação do evento no Google.
3. Se não couber mais, o paciente recebe novas opções.

## Mensagens e a janela de 24h

A Meta só permite texto livre até 24h depois da última mensagem do paciente. Fora disso (lembrete D-1, aviso de pagamento) só **templates aprovados**. O campo `conversas.ultima_entrada_em` decide qual dos dois usar.

## Dados e LGPD

- Guardar só o necessário: nome, telefone, horário, serviço, pagamento. Nada de queixa clínica.
- Não registrar o texto das mensagens em log (só id e tipo).
- `mensagens_whatsapp.conteudo` tem prazo de retenção (LS-27).
- Segredos só em variáveis de ambiente.
