# Decisões (ADRs)

## Decisão 1: DuckDB em vez de Postgres

- **Decisão:** usar DuckDB como banco de dados do projeto.
- **Por quê:** roda local, sem servidor, é rápido para consultas analíticas e atende o volume do MVP. Qualquer pessoa clona o repositório e roda.
- **Descartado:** Postgres, porque exigiria infraestrutura sem ganho nesta fase.
- **Quando revisar:** se o projeto virar multiusuário ou precisar de escrita concorrente.

## Decisão 2: dados sintéticos em vez do Jira real

- **Decisão:** gerar dados sintéticos por script, em vez de integrar com o Jira real.
- **Por quê:** o case é público, então não expõe dados de nenhuma empresa. A seed fixa torna os resultados reproduzíveis, e eu controlo a história que os dados contam, o que facilita testar a avaliação.
- **Descartado:** Jira real, por risco de confidencialidade, dependência de acesso e dados difíceis de testar de forma determinística.
- **Quando revisar:** quando o produto for validado com um time real, e então a integração com a API do Jira entra.
