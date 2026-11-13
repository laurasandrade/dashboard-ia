# Processos do programa

Os dois fluxos abaixo representam as regras de `docs/governanca-e-processos.md`, que é a fonte da verdade (é esse texto que o assistente consulta). Os diagramas estão em Mermaid, que o GitHub desenha direto. Uma versão em notação BPMN formal pode ser gerada a partir deles.

## 1. Escalonamento por status

```mermaid
flowchart TD
  A(["Status semanal calculado por regra"]) --> B{"Status do projeto"}
  B -->|Verde| C["Segue o ritual normal"]
  B -->|Amarelo| D["Gerente do projeto apresenta plano de recuperação em até 5 dias úteis"]
  B -->|Vermelho| E["Comunicar o patrocinador em até 24 horas"]
  E --> F["Escalonar ao comitê executivo com opções de decisão"]
  F --> G{"Decisão do comitê"}
  G -->|Cortar escopo| H["Atualizar plano, orçamento e registro de riscos"]
  G -->|Reforçar a equipe| H
  G -->|Renegociar prazo ou orçamento| H
  D --> H
  C --> I(["Próxima revisão semanal"])
  H --> I
```

## 2. Controle de mudanças

```mermaid
flowchart TD
  A(["Solicitação de mudança"]) --> B["Registrar motivo e solicitante"]
  B --> C["Análise de impacto em escopo, prazo, custo, risco e dependências"]
  C --> D{"Impacto de até 10% no orçamento e até 2 semanas no prazo?"}
  D -->|Sim| E["Gerente do programa decide"]
  D -->|Não| F["Patrocinador decide"]
  E --> G{"Mudança aprovada?"}
  F --> G
  G -->|Sim| H["Atualizar plano, orçamento e registro de riscos"]
  G -->|Não| I["Encerrar a solicitação com a justificativa"]
  H --> J(["Fim"])
  I --> J
```
