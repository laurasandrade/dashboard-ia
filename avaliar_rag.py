"""Avaliação mínima da recuperação: para cada pergunta, o trecho certo está no top 3?

Uso: python avaliar_rag.py
Acrescente casos conforme o assunto dos seus documentos. Vira a base da avaliação da Semana 4.
"""
from rag import buscar_docs

# (pergunta, arquivo esperado, palavra que deve aparecer no trecho certo)
CASOS = [
    ("como é calculado o lead time?", "definicoes-metricas.md", "mediana"),
    ("qual a meta de MTTR?", "metas-e-praticas.md", "6 horas"),
    ("qual é a meta de taxa de falha?", "metas-e-praticas.md", "15%"),
    ("o que fazer durante um incidente SEV1?", "runbook-incidentes.md", "SEV1"),
    ("quando fazer o post-mortem?", "runbook-incidentes.md", "5 dias"),
    ("variação pequena é tendência ou ruído?", "metas-e-praticas.md", "ruído"),
    ("como o MTTR é calculado?", "definicoes-metricas.md", "resolução"),
    ("cálculo MTTR", "definicoes-metricas.md", "resolução"),
    ("por que usamos a mediana?", "definicoes-metricas.md", "mediana"),
    ("o que significa SEV2?", "runbook-incidentes.md", "SEV2"),
    ("quantos deploys por semana cada time deve fazer?", "metas-e-praticas.md", "4 deploys"),
    ("como o status vermelho de um projeto é definido?", "definicoes-programa.md", "0,85"),
    ("o que é SPI?", "definicoes-programa.md", "SPI"),
    ("como é calculado o EAC?", "definicoes-programa.md", "BAC"),
    ("o que significa 85% de confiança na previsão?", "definicoes-programa.md", "85%"),
    ("o que fazer quando um projeto fica amarelo?", "governanca-e-processos.md", "plano de recuperação"),
    ("como funciona o controle de mudanças?", "governanca-e-processos.md", "análise de impacto"),
    ("quais os critérios de go/no-go?", "governanca-e-processos.md", "rollback"),
    ("quem aprova mudança acima do limite de alçada?", "governanca-e-processos.md", "patrocinador"),
    ("qual a capital da França?", None, None),  # fora do escopo: não deve achar nada
]

def certo(r, arquivo, palavra):
    return r["fonte"] == arquivo and palavra.lower() in r["trecho"].lower()


acertos = primeiro = 0
for pergunta, arquivo, palavra in CASOS:
    res = buscar_docs(pergunta)
    if arquivo is None:
        ok = top1 = not res
    else:
        ok = any(certo(r, arquivo, palavra) for r in res)
        top1 = bool(res) and certo(res[0], arquivo, palavra)
    acertos += ok
    primeiro += top1
    print(("OK   " if ok else "FALHA"), "(1º)" if top1 else "    ", pergunta,
          "->", [(r["fonte"], r["score"]) for r in res])
print(f"\nNo top 3: {acertos}/{len(CASOS)} | em 1º lugar: {primeiro}/{len(CASOS)}")
