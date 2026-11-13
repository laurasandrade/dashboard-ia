# Definições de programa neste projeto

Documento de referência do DORA Copilot para a visão de programa. As regras abaixo são exatamente as que o código (program.py) aplica. Os projetos, valores e datas são fictícios.

## Data de referência
Todos os cálculos de programa usam a data de referência 31/10/2026 ("hoje" do programa).

## Status do projeto (verde, amarelo, vermelho)
O status é calculado por regras, não por opinião.

Vermelho, se qualquer uma destas condições for verdadeira:
- SPI abaixo de 0,85;
- CPI abaixo de 0,85;
- algum marco atrasado há mais de 14 dias;
- alguma dependência com status bloqueada.

Amarelo, se não for vermelho e qualquer uma destas for verdadeira:
- SPI abaixo de 0,95;
- CPI abaixo de 0,90;
- algum marco atrasado há 14 dias ou menos;
- alguma dependência com status em risco.

Verde: nenhuma das condições acima.

## Valor agregado (EVM)
- BAC: orçamento total do projeto.
- PV (valor planejado): quanto do orçamento deveria estar realizado até hoje, de forma linear entre o início e o fim planejado.
- EV (valor agregado): quanto do orçamento corresponde ao trabalho realmente concluído.
- AC (custo real): quanto já foi gasto.
- SPI = EV dividido por PV. Abaixo de 1 significa atraso em relação ao plano.
- CPI = EV dividido por AC. Abaixo de 1 significa que o projeto está gastando mais do que o previsto pelo trabalho entregue.
- EAC (estimativa final) = BAC dividido por CPI. Projeta o custo final se o desempenho de custo continuar igual.
- VAC = BAC menos EAC. Negativo significa estouro de orçamento projetado.

## Pontuação de risco
Pontuação = probabilidade (1 a 5) vezes impacto (1 a 5). De 1 a 6, risco baixo. De 8 a 12, risco médio. De 15 a 25, risco alto ou crítico. Risco crítico é o de pontuação 15 ou mais. Riscos encerrados não entram nas listas de riscos abertos.

## Dependências entre projetos
Cada dependência tem um status: ok, em risco ou bloqueada. Dependência bloqueada é aquela cuja entrega já passou da data necessária sem ser atendida, ou que está impedindo o trabalho do projeto dependente.

## Previsão de entrega (Monte Carlo)
- A previsão usa o ritmo real de entrega: quantos itens de trabalho o projeto concluiu em cada uma das últimas 8 semanas.
- São feitas 10.000 simulações. Em cada uma, sorteia-se o ritmo de cada semana futura entre as semanas recentes até terminar os itens que faltam.
- O resultado é uma distribuição de datas. Com 85% de confiança, em 85% das simulações o trabalho termina até aquela data. Não é uma promessa de prazo.
- A chance de cumprir o prazo é o percentual de simulações que terminam até a data de fim planejada.
- A semente é fixa, então a mesma pergunta sempre dá a mesma previsão.

## Limitações
- SPI mede valor entregue em relação ao plano. A previsão Monte Carlo mede o ritmo recente. As duas podem discordar, e a discordância é um sinal para investigar, não um erro.
- A previsão assume que o ritmo recente continua. Mudança de equipe ou de escopo invalida a previsão.
- Os dados são sintéticos e servem para demonstrar o método.
