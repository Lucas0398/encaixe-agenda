# Configurar o WhatsApp (Meta Cloud API)

Guia para o número de teste do EncaixeAgenda. Para uma clínica real, repita usando a conta empresarial da clínica (issues LS-13 e LS-14).

## 1. Número

- Use um chip que receba SMS ou ligação para o código de verificação.
- O número **não pode estar ativo no app WhatsApp** (comum ou Business) na hora do registro na API. Se já estiver, apague a conta do WhatsApp nesse número antes, ou use o fluxo de coexistência da Meta.
- Enquanto o número definitivo não fica pronto, dá para testar com o **número de teste** que a Meta fornece (envia para até 5 números cadastrados).

## 2. Conta empresarial e app

1. Em business.facebook.com, crie o portfólio empresarial "EncaixeAgenda" usando o Gmail do projeto.
2. Em developers.facebook.com → Meus apps → Criar app → tipo **Empresa** → vincule ao portfólio.
3. Adicione o produto **WhatsApp**.
4. Em WhatsApp → Configuração da API: adicione e verifique o número.
5. Crie um **usuário do sistema** (Configurações do negócio → Usuários do sistema) com permissão no app e na conta do WhatsApp. Gere um token **permanente** com as permissões `whatsapp_business_messaging` e `whatsapp_business_management`.
6. Anote no `.env`:
   - `WHATSAPP_TOKEN`: o token permanente
   - `WHATSAPP_PHONE_NUMBER_ID`: a "Identificação do número de telefone"
   - `WHATSAPP_APP_SECRET`: Configurações do app → Básico → Chave secreta
   - `WHATSAPP_GRAPH_VERSAO`: a versão atual da Graph API mostrada na documentação

## 3. Testar o envio

```bash
python scripts/testar_whatsapp.py 55DDDNUMERO
```

Deve chegar o template `hello_world` no seu celular.

## 4. Webhook (receber mensagens)

1. Suba a API localmente (`docker compose up`) e abra um túnel HTTPS:
   `cloudflared tunnel --url http://localhost:8000` (ou ngrok).
2. Invente um texto para `WHATSAPP_VERIFY_TOKEN` e coloque no `.env`.
3. No app da Meta → WhatsApp → Configuração → Webhook:
   - URL de retorno: `https://<seu-tunel>/webhook/whatsapp`
   - Token de verificação: o mesmo `WHATSAPP_VERIFY_TOKEN`
4. Assine o campo **messages**.
5. Mande "oi" do seu celular para o número. A mensagem deve aparecer no log da API.

## 5. Templates

Mensagens fora da janela de 24h exigem template aprovado. Os textos propostos estão nas issues LS-16 (confirmação e lembrete) e LS-38 (pagamento). Crie no Gerenciador do WhatsApp → Modelos de mensagem, categoria **Utilidade**, idioma **pt_BR**.
