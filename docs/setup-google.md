# Configurar o Google Agenda

Usamos **conta de serviço**, e não login OAuth. Com Gmail comum e app OAuth em modo de teste, o acesso expira a cada 7 dias e o bot para; a conta de serviço não tem esse problema.

## 1. Agenda de teste

1. Entre no Google Agenda com o Gmail do projeto e confira o fuso **(GMT-03:00) Maceió**.
2. Crie uma agenda por profissional (para teste: "Teste – Fisioterapeuta 1").
3. Opcional: uma agenda "Bloqueios" para férias, feriados locais e reuniões.

## 2. Projeto no Google Cloud

1. Em console.cloud.google.com, com o mesmo Gmail, crie o projeto `encaixe-agenda`.
2. APIs e serviços → Biblioteca → ative a **Google Calendar API**.
3. IAM e administrador → Contas de serviço → **Criar conta de serviço** (`encaixe-bot`). Não precisa de papel no projeto.
4. Na conta criada → Chaves → Adicionar chave → **JSON**. Salve como `credenciais/google-service-account.json` (a pasta está no `.gitignore`; nunca faça commit desse arquivo).

## 3. Dar acesso à agenda

1. Copie o e-mail da conta de serviço (`encaixe-bot@<projeto>.iam.gserviceaccount.com`).
2. No Google Agenda → Configurações da agenda → **Compartilhar com pessoas específicas** → adicione esse e-mail com **Fazer alterações nos eventos**.
3. Na mesma tela, em **Integrar agenda**, copie o **ID da agenda**.

## 4. Testar

```bash
python scripts/testar_agenda.py ID_DA_AGENDA             # lista os eventos de amanhã
python scripts/testar_agenda.py ID_DA_AGENDA --escrever  # cria e apaga um evento de teste
```

## Padrão dos eventos

- Título: `[Serviço] – Nome do paciente`
- Descrição: telefone e origem
- Cor pelo status (ver `COR_AGENDA` em `dominio/estados.py`): amarelo = aguardando pagamento, verde = confirmado
- Eventos criados pelo sistema levam a propriedade privada `encaixe_agendamento_id`. Assim a sincronização sabe o que foi o bot e o que foi a secretária.
- Eventos marcados como **Livre** no Google não ocupam horário; eventos de dia inteiro bloqueiam o dia.
