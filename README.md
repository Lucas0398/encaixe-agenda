# EncaixeAgenda

Secretária inteligente para clínicas: lê os pedidos de **agendamento, remarcação e cancelamento** no WhatsApp, marca no **Google Agenda** sem conflito de horário e envia **confirmação** e **lembrete 1 dia antes**. Opcionalmente cobra por **Pix** e libera o horário se o paciente não pagar.

> ⚠️ **Repositório público.** Nunca faça commit de `.env`, chaves, tokens ou dados de pacientes. O `.gitignore` já bloqueia os casos comuns, mas confira antes de cada commit.

## Status

Fase inicial. O que já existe:

| Parte | Situação |
|---|---|
| Regras por clínica (`dominio/regras.py`) | ✅ com testes |
| Status do agendamento (`dominio/estados.py`) | ✅ com testes |
| Horários livres e conflitos (`dominio/disponibilidade.py`) | ✅ com testes |
| Feriados nacionais (`dominio/feriados.py`) | ✅ com testes |
| Webhook do WhatsApp: verificação, assinatura, leitura (`whatsapp/webhook.py`) | ✅ com testes |
| Envio de mensagens (`whatsapp/cliente.py`) | 🟡 escrito, falta testar com o número |
| Google Agenda (`agenda/google.py`) | 🟡 escrito, falta testar com a conta |
| API (`api/app.py`) | 🟡 recebe e valida o webhook; ainda não processa |
| Banco (`db/schema.sql`) | 🟡 schema inicial, sem camada de acesso |
| IA, fluxos de conversa, fila de tarefas, pagamento | ⏳ próximas etapas |

## Como rodar

Requisitos: Python 3.12+ e Docker.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest                      # testes do núcleo
cp .env.example .env        # preencha com suas chaves
docker compose up --build   # banco + API em http://localhost:8000/health
```

Para a Meta conseguir chamar o webhook no seu computador, use um túnel HTTPS (ex.: `cloudflared tunnel --url http://localhost:8000`) e cadastre `https://<seu-tunel>/webhook/whatsapp`. Detalhes em [docs/setup-whatsapp.md](docs/setup-whatsapp.md).

### Testar as integrações

```bash
python scripts/testar_whatsapp.py 5582999990000      # envia o template hello_world
python scripts/testar_agenda.py SEU_CALENDAR_ID --escrever
```

## Estrutura

```
src/encaixe/
  dominio/     regras puras, sem rede nem banco (onde mora o diferencial)
  whatsapp/    webhook (entrada) e cliente (saída) da Cloud API
  agenda/      contrato da agenda + implementação Google + fake em memória
  api/         FastAPI: /health e /webhook/whatsapp
  config.py    variáveis de ambiente
db/schema.sql  tabelas do Postgres
scripts/       testes manuais das integrações
docs/          arquitetura, guias de configuração e decisões
```

## Documentação

- [Arquitetura](docs/arquitetura.md)
- [Regras configuráveis por clínica](docs/regras-por-clinica.md)
- [Configurar o WhatsApp (Meta)](docs/setup-whatsapp.md)
- [Configurar o Google Agenda](docs/setup-google.md)
- Decisões: [0001 — código próprio em vez de n8n](docs/decisoes/0001-codigo-proprio-em-vez-de-n8n.md)

O planejamento das tarefas fica no Linear (projeto Secretária Inteligente, issues `LS-*`).
