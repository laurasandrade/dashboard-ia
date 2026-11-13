"""Gera dados sintéticos de PROGRAMA no mesmo dora.duckdb: projetos, marcos, dependências,
riscos, indicadores de valor agregado (EVM) e itens de trabalho (para a previsão Monte Carlo).

Não mexe nas tabelas changes/incidents. Dados 100% fictícios.
Uso: python generate_program.py     (feche o Streamlit antes, o arquivo precisa estar livre)
"""
from datetime import date, timedelta
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)  # semente fixa = dados reproduzíveis
DB_PATH = Path(__file__).parent / "dora.duckdb"
AS_OF = date(2026, 10, 31)  # "hoje" do programa (fim dos dados DORA)

# id, nome, responsável, time, início, fim planejado, orçamento (R$), SPI alvo, CPI alvo, total de itens
PROJETOS = [
    ("P1", "Open Finance - Consentimento", "Renata Alves", "Plataforma", date(2026, 5, 4), date(2026, 12, 18), 1_200_000, 0.98, 1.00, 120),
    ("P2", "Pix Parcelado", "Carlos Mota", "Pagamentos", date(2026, 6, 1), date(2026, 11, 27), 900_000, 0.78, 0.88, 90),
    ("P3", "App Mobile v2", "Juliana Prado", "Mobile", date(2026, 5, 18), date(2027, 1, 29), 1_500_000, 0.90, 0.95, 150),
    ("P4", "Onboarding Digital", "Marcos Lima", "Onboarding", date(2026, 7, 6), date(2026, 12, 11), 600_000, 1.02, 1.03, 70),
    ("P5", "Data Lake Regulatório", "Patrícia Nunes", "Dados", date(2026, 5, 4), date(2026, 11, 20), 800_000, 0.82, 0.90, 100),
]

D = date
# projeto, nome do marco, data planejada, data real (None = ainda aberto)
MARCOS = [
    ("P1", "Kickoff e escopo fechado", D(2026, 5, 4), D(2026, 5, 4)),
    ("P1", "Design técnico aprovado", D(2026, 6, 12), D(2026, 6, 12)),
    ("P1", "Consentimento em homologação", D(2026, 8, 28), D(2026, 9, 2)),
    ("P1", "Piloto interno", D(2026, 10, 23), D(2026, 10, 26)),
    ("P1", "Go-live", D(2026, 12, 18), None),
    ("P2", "Kickoff e escopo fechado", D(2026, 6, 1), D(2026, 6, 1)),
    ("P2", "Arquitetura aprovada", D(2026, 7, 10), D(2026, 7, 17)),
    ("P2", "MVP em homologação interna", D(2026, 9, 4), D(2026, 9, 18)),
    ("P2", "Homologação regulatória", D(2026, 10, 16), None),
    ("P2", "Go-live", D(2026, 11, 27), None),
    ("P3", "Kickoff e escopo fechado", D(2026, 5, 18), D(2026, 5, 18)),
    ("P3", "Protótipo validado", D(2026, 6, 26), D(2026, 7, 3)),
    ("P3", "Beta fechado", D(2026, 9, 25), D(2026, 10, 2)),
    ("P3", "Beta aberto", D(2026, 10, 26), None),
    ("P3", "Lançamento nas lojas", D(2027, 1, 29), None),
    ("P4", "Kickoff e escopo fechado", D(2026, 7, 6), D(2026, 7, 6)),
    ("P4", "Fluxo de KYC definido", D(2026, 8, 7), D(2026, 8, 7)),
    ("P4", "SDK de onboarding pronto", D(2026, 10, 9), D(2026, 10, 9)),
    ("P4", "Piloto com clientes", D(2026, 11, 13), None),
    ("P4", "Go-live", D(2026, 12, 11), None),
    ("P5", "Kickoff e escopo fechado", D(2026, 5, 4), D(2026, 5, 4)),
    ("P5", "Modelo de dados aprovado", D(2026, 6, 19), D(2026, 6, 26)),
    ("P5", "Ingestão em lote pronta", D(2026, 8, 28), D(2026, 9, 11)),
    ("P5", "Relatórios regulatórios v1", D(2026, 10, 28), None),
    ("P5", "Go-live", D(2026, 11, 20), None),
]

# dependente, fornecedor, descrição, necessária até, status (ok / at_risk / blocked)
DEPENDENCIAS = [
    ("P2", "P1", "API de consentimento do Open Finance", D(2026, 11, 6), "at_risk"),
    ("P3", "P4", "SDK de onboarding embarcado no app", D(2026, 11, 13), "ok"),
    ("P5", "P2", "Eventos de pagamento parcelado para os relatórios", D(2026, 10, 30), "blocked"),
    ("P4", "P1", "Consentimento no fluxo de cadastro", D(2026, 11, 20), "ok"),
    ("P3", "P1", "Login com Open Finance", D(2026, 12, 4), "at_risk"),
]

# projeto, título, categoria, probabilidade (1-5), impacto (1-5), responsável, status, mitigação, registrado em
RISCOS = [
    ("P1", "Mudança de regra do Banco Central no consentimento", "Regulatório", 3, 5, "Renata Alves", "mitigating", "Acompanhar consulta pública e manter o desenho flexível", D(2026, 7, 14)),
    ("P1", "Atraso do fornecedor de certificados digitais", "Fornecedor", 2, 4, "Renata Alves", "open", "Pedir certificados com antecedência de 30 dias", D(2026, 8, 3)),
    ("P2", "Atraso na homologação regulatória", "Regulatório", 5, 5, "Carlos Mota", "open", "Reunião semanal com o regulador e plano B de escopo reduzido", D(2026, 9, 21)),
    ("P2", "Dependência da API de consentimento (P1)", "Prazo", 4, 4, "Carlos Mota", "mitigating", "Mock da API para destravar o time enquanto P1 entrega", D(2026, 9, 8)),
    ("P2", "Saída de desenvolvedor sênior", "Pessoas", 3, 4, "Carlos Mota", "open", "Mapear conhecimento e pareamento com o segundo desenvolvedor", D(2026, 10, 5)),
    ("P3", "Rejeição do app nas lojas", "Técnico", 2, 4, "Juliana Prado", "open", "Checklist das políticas das lojas antes de cada envio", D(2026, 8, 17)),
    ("P3", "Crescimento de escopo no beta aberto", "Escopo", 4, 3, "Juliana Prado", "open", "Controle de mudanças com corte por prioridade", D(2026, 9, 29)),
    ("P3", "Atraso do SDK de onboarding (P4)", "Prazo", 2, 4, "Juliana Prado", "mitigating", "Alinhamento quinzenal com o time de Onboarding", D(2026, 9, 1)),
    ("P3", "Estouro de orçamento por retrabalho", "Custo", 3, 3, "Juliana Prado", "open", "Revisão de qualidade antes de entrar em sprint", D(2026, 10, 12)),
    ("P4", "Falha do provedor de KYC acima do contratado", "Fornecedor", 3, 4, "Marcos Lima", "open", "Provedor secundário em avaliação", D(2026, 9, 15)),
    ("P4", "Custo de nuvem acima do previsto", "Custo", 2, 2, "Marcos Lima", "closed", "Ajuste de dimensionamento já aplicado", D(2026, 7, 27)),
    ("P5", "Qualidade dos dados de origem", "Técnico", 4, 4, "Patrícia Nunes", "open", "Regras de validação na ingestão e relatório de qualidade", D(2026, 8, 24)),
    ("P5", "Eventos de pagamento indisponíveis (bloqueio com P2)", "Prazo", 5, 4, "Patrícia Nunes", "open", "Escalar para o comitê e negociar entrega parcial dos eventos", D(2026, 10, 19)),
    ("P5", "Multa por atraso em relatório regulatório", "Regulatório", 3, 5, "Patrícia Nunes", "open", "Comunicar o regulador sobre o cronograma revisado", D(2026, 10, 22)),
]


def semanas_ate(inicio: date, fim: date) -> list[date]:
    datas, d = [], inicio
    while d < fim:
        datas.append(d)
        d += timedelta(days=7)
    datas.append(fim)
    return datas


def gerar_evm():
    linhas = []
    for pid, _, _, _, ini, fim, bac, spi_alvo, cpi_alvo, _ in PROJETOS:
        datas = semanas_ate(ini, AS_OF)
        pv = np.array([bac * min((d - ini).days / (fim - ini).days, 1.0) for d in datas])
        rampa = np.minimum(np.arange(len(datas)) / 12, 1.0)
        spi = 1 + (spi_alvo - 1) * rampa + rng.normal(0, 0.01, len(datas))
        cpi = 1 + (cpi_alvo - 1) * rampa + rng.normal(0, 0.01, len(datas))
        spi[-1], cpi[-1] = spi_alvo, cpi_alvo  # fecha exatamente no valor-alvo
        ev = np.maximum.accumulate(pv * spi)
        ac = np.maximum.accumulate(ev / cpi)
        for d, p, e, a in zip(datas, pv, ev, ac):
            linhas.append({"project_id": pid, "week_end": d, "planned_value": round(p, 2),
                           "earned_value": round(e, 2), "actual_cost": round(a, 2)})
    return pd.DataFrame(linhas)


def gerar_itens():
    linhas = []
    for pid, _, _, _, ini, fim, _, spi_alvo, _, total in PROJETOS:
        p = (AS_OF - ini).days / (fim - ini).days
        concluidos = round(total * p * spi_alvo)  # progresso real = planejado x SPI
        semanas = semanas_ate(ini, AS_OF)[:-1] or [ini]
        pesos = rng.gamma(4, 1, len(semanas))
        por_semana = rng.multinomial(concluidos, pesos / pesos.sum())
        n = 0
        for ini_sem, qtd in zip(semanas, por_semana):
            for _ in range(int(qtd)):
                dia = min(ini_sem + timedelta(days=int(rng.integers(0, 7))), AS_OF)
                n += 1
                linhas.append({"item_id": f"{pid}-{n:03d}", "project_id": pid, "created_at": ini,
                               "done_at": pd.Timestamp(dia) + pd.Timedelta(hours=float(rng.uniform(9, 18)))})
        for k in range(concluidos + 1, total + 1):
            linhas.append({"item_id": f"{pid}-{k:03d}", "project_id": pid, "created_at": ini, "done_at": pd.NaT})
    return pd.DataFrame(linhas)


def main():
    projetos = pd.DataFrame([{"project_id": p[0], "name": p[1], "owner": p[2], "team": p[3],
                              "start_date": p[4], "planned_end": p[5], "budget": p[6]} for p in PROJETOS])
    marcos = pd.DataFrame([{"milestone_id": f"M{i + 1:02d}", "project_id": m[0], "name": m[1],
                            "planned_date": m[2], "actual_date": m[3]} for i, m in enumerate(MARCOS)])
    deps = pd.DataFrame([{"dep_id": f"D{i + 1}", "project_id": d[0], "provider_id": d[1],
                          "description": d[2], "needed_by": d[3], "status": d[4]} for i, d in enumerate(DEPENDENCIAS)])
    riscos = pd.DataFrame([{"risk_id": f"R-{i + 1:02d}", "project_id": r[0], "title": r[1], "category": r[2],
                            "probability": r[3], "impact": r[4], "owner": r[5], "status": r[6],
                            "mitigation": r[7], "raised_at": r[8]} for i, r in enumerate(RISCOS)])
    evm, itens = gerar_evm(), gerar_itens()
    meta = pd.DataFrame([{"as_of": AS_OF}])

    con = duckdb.connect(str(DB_PATH))
    for nome, df in [("projects", projetos), ("milestones", marcos), ("dependencies", deps),
                     ("risks", riscos), ("evm_snapshots", evm), ("work_items", itens),
                     ("program_meta", meta)]:
        con.execute(f"CREATE OR REPLACE TABLE {nome} AS SELECT * FROM df")
    con.close()
    print(f"projetos: {len(projetos)} | marcos: {len(marcos)} | dependências: {len(deps)} | "
          f"riscos: {len(riscos)} | snapshots EVM: {len(evm)} | itens: {len(itens)} | data de referência: {AS_OF}")


if __name__ == "__main__":
    main()
