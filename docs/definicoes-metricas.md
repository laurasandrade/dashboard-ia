# Definições das métricas DORA neste projeto

Documento de referência do DORA Copilot. As definições abaixo são exatamente as que o código (metrics.py) calcula. Os dados são sintéticos, gerados por generate_data.py com semente fixa.

## Frequência de deploy
Número de deploys em produção no período dividido pelo número de semanas do período (dias divididos por 7, com mínimo de 1 semana). Unidade: deploys por semana. Quanto maior, melhor.

## Lead time
Mediana, em horas, do tempo entre o primeiro commit de uma mudança e o seu deploy em produção. Usamos a mediana, e não a média, para que poucas mudanças muito demoradas não distorçam o resultado. Quanto menor, melhor.

## Taxa de falha em mudanças
Percentual de mudanças implantadas que falharam (causaram incidente) no período. Quanto menor, melhor.

## MTTR (tempo de recuperação)
Média, em horas, entre o início e a resolução dos incidentes. O incidente entra no período pela data de início. Todo incidente nasce de uma mudança que falhou. Quanto menor, melhor.

## Como comparamos períodos
Cada indicador do dashboard é comparado com o período imediatamente anterior, de mesma duração. A variação é percentual: (atual - anterior) / anterior.

## Limitações
- Os dados são sintéticos: servem para demonstrar a solução, não para tirar conclusões sobre equipes reais.
- Períodos curtos ou times com poucos deploys geram variações grandes por ruído estatístico.
