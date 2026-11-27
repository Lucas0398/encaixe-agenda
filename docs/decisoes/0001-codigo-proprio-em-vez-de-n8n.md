# 0001 — Código próprio em vez de n8n

**Data:** 27/11/2026 · **Status:** aceita · **Issue:** LS-9

## Contexto

O produto precisa de regras que mudam de clínica para clínica (ex.: cancelar o agendamento se o Pix não for pago em 2h, cobrar só de paciente novo, lista de espera). Essa capacidade de personalizar é o diferencial em relação à Doctoralia.

## Opções

1. **n8n como base:** rápido para ligar APIs e bom para demonstração.
2. **Código próprio (Python + FastAPI + Postgres):** mais trabalho no início, controle total.

## Decisão

Código próprio. O n8n fica restrito a protótipos e automações internas.

## Motivos

- **Estado da conversa e status do agendamento:** viram um emaranhado de nós "IF" no fluxo visual; em código são uma máquina de estados testada.
- **Conflito de horário:** precisa de transação e trava no banco, o que é frágil no n8n.
- **Testes e versionamento:** cada regra tem teste automatizado e histórico no Git.
- **Várias clínicas:** uma base de código com configuração por clínica, em vez de um fluxo copiado por cliente.
- **Licença:** a licença gratuita do n8n (Sustainable Use License) restringe vender acesso ao n8n, e os limites para um produto vendido a várias clínicas são pouco claros.

## Consequências

- Mais código para manter. Para compensar, o domínio fica isolado, sem rede nem banco, e coberto por testes.
- Integrações (WhatsApp, Google, Pix) ficam atrás de interfaces simples, que podem ser trocadas.
