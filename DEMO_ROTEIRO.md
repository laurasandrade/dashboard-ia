# Roteiro do vídeo de demonstração (2 minutos)

## Antes de gravar
- [ ] App rodando local, navegador em tela cheia, zoom em 110% a 125%.
- [ ] Notificações desligadas e abas pessoais fechadas.
- [ ] `python generate_program.py` rodado e `logs/interacoes.jsonl` com algumas interações (a página Observabilidade não pode estar vazia).
- [ ] Perguntas do assistente já testadas (veja a cena 5).
- [ ] Leia o texto em voz alta uma vez com o cronômetro.

## Cenas

| Tempo | Tela | O que falar |
|---|---|---|
| 0:00 a 0:12 | Página **Programa**, cartões de status | "Gerenciar vários projetos costuma significar cor de status por opinião e prazo em data única. Montei um programa fictício para mostrar outro jeito: regra, probabilidade e números rastreáveis." |
| 0:12 a 0:35 | Aba **Projetos**, tabela com os motivos | "O status sai de regra: SPI abaixo de 0,85, marco atrasado há mais de 14 dias ou dependência bloqueada deixam o projeto vermelho. Aqui o Pix Parcelado está vermelho por atraso de marco, e cada motivo aparece escrito." |
| 0:35 a 0:55 | Abas **Dependências** e **Riscos** | "O Data Lake está bloqueado porque depende de eventos do Pix Parcelado, que por sua vez depende da API do Open Finance. A matriz mostra onde estão os riscos críticos." |
| 0:55 a 1:15 | Aba **Previsão de entrega** (mexer no controle de confiança) | "A previsão usa o ritmo real de entrega, em 10 mil simulações. Em vez de uma data, eu digo: com 85% de confiança, até tal dia, e esta é a chance de cumprir o plano. Não é promessa: se o ritmo muda, a previsão muda." |
| 1:15 a 1:40 | Página **Assistente**: perguntar "Quais projetos estão com status vermelho?" e "Qual a previsão do Pix Parcelado com 85% de confiança?" (abrir "Ferramentas consultadas") | "Posso perguntar em linguagem natural. O modelo não escreve SQL: ele chama ferramentas somente leitura, e dá para ver exatamente o que foi consultado." |
| 1:40 a 1:52 | Página **Observabilidade**, avaliação publicada | "Cada resposta tem checagem de números e fica registrada. Avaliei com 27 perguntas fixas: 22 de 23 com nota automática, e a resposta certa vem do banco, não de mim." |
| 1:52 a 2:00 | Voltar à página Programa | "Os dados são sintéticos, mas o método vale para Jira e GitHub reais. O link está na descrição." |

## Dicas de gravação
- Windows: `Win + Alt + R` (Xbox Game Bar) grava a janela; OBS Studio é gratuito e dá mais controle.
- Grave a voz separada se puder, ou em ambiente silencioso; legenda ajuda quem assiste sem som.
- Publique no YouTube como **não listado** ou direto no LinkedIn; coloque o link no README e na seção Destaques do perfil.
- Para um GIF no README, grave só a cena da previsão (10 a 15 segundos).
