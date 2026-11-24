# Protótipo n8n — conteúdo para Instagram

Este protótipo adapta a lógica do workflow público “Generate Instagram Content from Top Trends with AI Image Generation” ao projeto dos cartões em aquarela.

## O que ele faz agora

1. É iniciado manualmente.
2. Carrega os dados reais do produto N01.
3. Cria três ideias de conteúdo locais para teste.
4. Seleciona a ideia com maior pontuação.
5. Produz legenda, briefing visual, prompt de imagem e checklist de revisão.
6. Encerra em `AGUARDANDO_APROVACAO_HUMANA`.

Ele não pesquisa perfis, não chama APIs pagas, não usa credenciais e não publica no Instagram.

## Como testar

1. Abra o n8n.
2. Escolha **Import from File**.
3. Importe `prototipo-conteudo-instagram-cartoes.json`.
4. Abra o node **Configuração do produto** para revisar preço, formato e CTA.
5. Clique em **Execute workflow**.
6. Abra o resultado do node **Aguardar aprovação humana**.

## Saída esperada

- Tema e gancho selecionados.
- Legenda pronta para revisão.
- Prompt de imagem.
- Caminho do visual de exemplo.
- Checklist obrigatório antes de publicar.
- Status de aprovação falso por padrão.

## Visual de exemplo

`../../assets/prototipo-instagram-n01-v2-natural.png`

O visual foi criado com o `imagegen` em modo de edição, usando a foto real do N01 como alvo. A versão 2 remove a mão superior que parecia flutuar, deixa o cartão apoiado sobre o envelope e mantém apenas uma mão entrando naturalmente pelo canto inferior esquerdo. Por ser uma imagem gerada, ela deve ser tratada como protótipo visual, não como prova fotográfica literal do produto.

## Diferenças em relação ao template original

O template de referência usa agendamento, coleta de tendências do Instagram por RapidAPI, PostgreSQL para deduplicação, análise e legenda com OpenAI, geração de imagens por Replicate/Flux, publicação pela Facebook Graph API e notificações pelo Telegram.

Nossa primeira versão retira essas dependências para validar antes:

- se os ganchos combinam com a marca;
- se o conteúdo gera pedidos reais;
- se a imagem continua fiel ao produto artesanal;
- se o tempo economizado justifica a automação.

## Evolução proposta

### Fase 1 — atual

Geração local de pauta e pacote para aprovação.

### Fase 2 — depois das primeiras vendas

- Entrada por formulário com produto, ocasião e estoque.
- Pesquisa de sinais de tendência em fontes autorizadas.
- IA para rascunho de legenda e briefing.
- Geração ou edição visual.
- Registro em planilha ou banco para evitar repetição.
- Aprovação humana obrigatória.

### Fase 3 — somente se houver volume

- Publicação pela Instagram Graph API.
- Registro de URL e horário.
- Coleta de métricas.
- Alertas de falha.

## Regra editorial

Tendência é um sinal de formato, assunto ou linguagem. Não deve ser usada para copiar a arte, a legenda ou a identidade de outra pessoa.

## Prompt final usado no protótipo visual

```text
Use case: precise-object-edit
Asset type: prototype Instagram feed creative, portrait 4:5
Primary request: transformar a foto real do cartão em fotografia comercial autêntica.
Scene/backdrop: fundo marfim limpo, envelope kraft e pequenos ramos de eucalipto.
Subject: preservar cartão, textura do papel, caligrafia, mãos, anéis e esmalte.
Text: “Feliz Natal”, “De:”, “Para:”.
Constraints: alterar apenas o ambiente; sem texto promocional, logo ou marca-d'água.
```

## Referência

- [Template original no GitHub](https://github.com/enescingoz/awesome-n8n-templates/blob/main/Instagram_Twitter_Social_Media/Generate%20Instagram%20Content%20from%20Top%20Trends%20with%20AI%20Image%20Generation.json)
