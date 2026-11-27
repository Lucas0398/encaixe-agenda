# Regras configuráveis por clínica

Cada clínica tem um JSON de regras na coluna `clinicas.regras`, validado por `encaixe.dominio.regras.RegrasClinica`. Só é preciso informar o que for diferente do padrão; chaves desconhecidas são recusadas (pega erro de digitação).

| Regra | Padrão | Para que serve |
|---|---|---|
| `fuso` | `America/Maceio` | Fuso da clínica |
| `granularidade_slots_min` | `30` | De quanto em quanto tempo oferecer horários (08:00, 08:30...) |
| `intervalo_entre_sessoes_min` | `0` | Folga obrigatória entre um atendimento e outro |
| `max_opcoes_oferecidas` | `5` | Quantos horários o bot mostra de cada vez |
| `antecedencia_minima_agendamento_horas` | `2` | Não oferece horário em cima da hora |
| `antecedencia_minima_cancelamento_horas` | `24` | Depois disso, cancelamento vai para a secretária |
| `bloquear_feriados_nacionais` | `true` | Fecha nos feriados nacionais |
| `bloquear_pontos_facultativos` | `true` | Fecha no Carnaval e no Corpus Christi |
| `datas_bloqueadas` | `[]` | Feriados estaduais/municipais, recessos e férias coletivas |
| `exige_pagamento_antecipado` | `false` | Liga o fluxo de Pix antes da sessão |
| `pagamento_exigido_para` | `todos` | `todos` ou `so_pacientes_novos` |
| `prazo_pagamento_horas` | `2` | Tempo para pagar antes de liberar o horário |
| `aviso_antes_do_prazo_min` | `30` | Aviso "faltam X minutos" |
| `lembrete_d1_horario` | `10:00` | Hora do envio do lembrete do dia anterior |
| `primeira_avaliacao_vai_para_humano` | `true` | Primeira consulta é marcada pela secretária |

Duração, capacidade e valor de cada atendimento ficam na tabela `servicos`; a grade de horários de cada profissional fica em `expedientes`.

## Exemplo: clínica que cobra sinal só de paciente novo

```json
{
  "exige_pagamento_antecipado": true,
  "pagamento_exigido_para": "so_pacientes_novos",
  "prazo_pagamento_horas": 3,
  "intervalo_entre_sessoes_min": 10,
  "datas_bloqueadas": ["2026-12-24", "2026-12-31"]
}
```

## Feriados locais

Só os feriados **nacionais** são calculados automaticamente. Os estaduais e municipais variam: confirme a lista com a clínica e cadastre em `datas_bloqueadas`.

## Como adicionar uma regra nova

1. Adicione o campo em `RegrasClinica` com um padrão que mantém o comportamento atual.
2. Use o campo na regra de domínio correspondente.
3. Escreva o teste.
4. Documente nesta tabela.
