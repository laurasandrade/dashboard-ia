# Metas internas e boas práticas de leitura (fictícias, para o case)

As metas abaixo são fictícias e foram definidas apenas para este projeto de portfólio.

## Metas por time
- Frequência de deploy: pelo menos 4 deploys por semana por time.
- Lead time (mediana): até 48 horas.
- Taxa de falha em mudanças: até 15%.
- MTTR: até 6 horas.

## Como interpretar variações
- Variações abaixo de 10% em períodos curtos devem ser tratadas como ruído, não como tendência.
- A taxa de falha só é considerada confiável com pelo menos 10 deploys no período analisado.
- Nenhuma métrica deve ser lida sozinha: frequência alta com taxa de falha crescente indica velocidade sem qualidade.
- As métricas servem para melhorar o processo e conversar com o time, nunca para ranquear ou punir pessoas.

## Ritual de revisão
- Revisão mensal das quatro métricas com cada time, comparando com o mês anterior.
- Quando uma meta não é atingida por dois meses seguidos, o time propõe uma ação de melhoria no planejamento seguinte.
