# Runbook de incidentes (fictício, para o case)

## Severidades
- SEV1: serviço crítico fora do ar ou perda de dados. Resposta imediata, acionar o líder de plantão.
- SEV2: funcionalidade importante degradada, com alternativa para o usuário. Resposta em até 1 hora.
- SEV3: problema localizado, sem impacto relevante. Tratar no planejamento do time.

## Durante o incidente
1. Quem identifica abre o incidente e registra o horário de início, que alimenta o cálculo de MTTR.
2. Define-se uma pessoa responsável pela coordenação e outra pela comunicação.
3. Prioridade é restaurar o serviço (por exemplo, com rollback da última mudança) antes de investigar a causa.
4. A comunicação com as partes interessadas é feita a cada 30 minutos em SEV1.

## Depois do incidente
- Registrar o horário de resolução, que fecha o cálculo de MTTR.
- Fazer a revisão pós-incidente (post-mortem) em até 5 dias úteis, sem culpados, focada em processo e em ações de melhoria.
- Incidentes originados por mudanças contam na taxa de falha em mudanças.
