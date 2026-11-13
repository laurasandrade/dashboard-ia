"""Funções de PROGRAMA (somente leitura): status, riscos, dependências, EVM e previsão de entrega.

Como em metrics.py, estas funções são expostas ao assistente como ferramentas: o modelo
nunca escreve SQL. Os dados são sintéticos (veja generate_program.py).
"""
import unicodedata
from datetime import date, timedelta

import duckdb
import numpy as np

from metrics import DB_PATH

SIMULACOES = 10_000
MAX_SEMANAS = 104
SEMENTE = 42  # fixa: a mesma pergunta sempre dá a mesma previsão (reprodutível e avaliável)


def _rows(sql: str, params: list | None = None) -> list[dict]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        cur = con.execute(sql, params or [])
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        con.close()


def as_of() -> date:
    return _rows("SELECT as_of FROM program_meta")[0]["as_of"]


def _norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def list_projects() -> list[dict]:
    return _rows("SELECT project_id, name, owner, team, start_date, planned_end, budget "
                 "FROM projects ORDER BY project_id")


def resolver_projeto(ref: str) -> dict:
    """Aceita id (P2), nome (ou parte dele) ou time. Erro claro se não achar ou se for ambíguo."""
    projetos = list_projects()
    r = _norm(str(ref or "")).strip()
    if not r:
        raise ValueError("Informe o projeto.")
    achados = [p for p in projetos if r == p["project_id"].lower() or r in _norm(p["name"]) or r == _norm(p["team"])]
    if len(achados) == 1:
        return achados[0]
    opcoes = [f'{p["project_id"]} ({p["name"]})' for p in projetos]
    if not achados:
        raise ValueError(f"Projeto não encontrado: {ref}. Opções: {opcoes}")
    raise ValueError(f"Projeto ambíguo: {ref}. Opções: {opcoes}")


# ---------- EVM ----------
def get_evm(project: str) -> dict:
    p = resolver_projeto(project)
    ult = _rows("SELECT * FROM evm_snapshots WHERE project_id = ? ORDER BY week_end DESC LIMIT 1", [p["project_id"]])[0]
    bac = float(p["budget"])
    pv, ev, ac = float(ult["planned_value"]), float(ult["earned_value"]), float(ult["actual_cost"])
    spi, cpi = ev / pv, ev / ac
    eac = bac / cpi
    return {"project_id": p["project_id"], "projeto": p["name"], "data": ult["week_end"].isoformat(),
            "orcamento_bac": round(bac), "valor_planejado_pv": round(pv), "valor_agregado_ev": round(ev),
            "custo_real_ac": round(ac), "spi": round(spi, 2), "cpi": round(cpi, 2),
            "estimativa_final_eac": round(eac), "variacao_final_vac": round(bac - eac)}


def evm_series(project: str):
    p = resolver_projeto(project)
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute("SELECT week_end, planned_value AS PV, earned_value AS EV, actual_cost AS AC "
                           "FROM evm_snapshots WHERE project_id = ? ORDER BY week_end", [p["project_id"]]).df()
    finally:
        con.close()


# ---------- Dependências ----------
def list_dependencies(project: str | None = None, only_issues: bool = True) -> dict:
    hoje = as_of()
    filtro, params = "", []
    if project:
        pid = resolver_projeto(project)["project_id"]
        filtro, params = " WHERE d.project_id = ? OR d.provider_id = ?", [pid, pid]
    linhas = _rows("SELECT d.dep_id, d.project_id, a.name AS dependente, d.provider_id, b.name AS fornecedor, "
                   "d.description, d.needed_by, d.status FROM dependencies d "
                   "JOIN projects a ON a.project_id = d.project_id "
                   "JOIN projects b ON b.project_id = d.provider_id" + filtro + " ORDER BY d.needed_by", params)
    saida = []
    for r in linhas:
        if only_issues and r["status"] == "ok":
            continue
        saida.append({"dep_id": r["dep_id"], "dependente": r["dependente"], "fornecedor": r["fornecedor"],
                      "descricao": r["description"], "necessaria_ate": r["needed_by"].isoformat(),
                      "dias_ate_o_prazo": (r["needed_by"] - hoje).days, "status": r["status"]})
    return {"data_referencia": hoje.isoformat(), "total": len(saida), "dependencias": saida}


# ---------- Riscos ----------
def list_risks(project: str | None = None, min_score: int | None = None) -> dict:
    """Riscos abertos ou em mitigação, do maior para o menor (pontuação = probabilidade x impacto)."""
    sql = ("SELECT r.risk_id, r.project_id, p.name AS projeto, r.title, r.category, r.probability, r.impact, "
           "r.probability * r.impact AS score, r.owner, r.status, r.mitigation FROM risks r "
           "JOIN projects p ON p.project_id = r.project_id WHERE r.status <> 'closed'")
    params = []
    if project:
        sql += " AND r.project_id = ?"
        params.append(resolver_projeto(project)["project_id"])
    if min_score:
        sql += " AND r.probability * r.impact >= ?"
        params.append(int(min_score))
    linhas = _rows(sql + " ORDER BY score DESC, r.risk_id", params)
    return {"total": len(linhas), "riscos": [
        {"risk_id": r["risk_id"], "projeto": r["projeto"], "titulo": r["title"], "categoria": r["category"],
         "probabilidade": r["probability"], "impacto": r["impact"], "pontuacao": r["score"],
         "responsavel": r["owner"], "status": r["status"], "mitigacao": r["mitigation"]} for r in linhas]}


# ---------- Status (RAG) ----------
def _rag(spi: float, cpi: float, atraso_max: int, deps: list[dict]) -> tuple[str, list[str]]:
    bloqueada = any(d["status"] == "blocked" for d in deps)
    em_risco = any(d["status"] == "at_risk" for d in deps)
    vermelho, amarelo = [], []
    if spi < 0.85: vermelho.append(f"SPI {spi:.2f} abaixo de 0,85")
    if cpi < 0.85: vermelho.append(f"CPI {cpi:.2f} abaixo de 0,85")
    if atraso_max > 14: vermelho.append(f"marco atrasado há {atraso_max} dias")
    if bloqueada: vermelho.append("dependência bloqueada")
    if spi < 0.95: amarelo.append(f"SPI {spi:.2f} abaixo de 0,95")
    if cpi < 0.90: amarelo.append(f"CPI {cpi:.2f} abaixo de 0,90")
    if 0 < atraso_max <= 14: amarelo.append(f"marco atrasado há {atraso_max} dias")
    if em_risco: amarelo.append("dependência em risco")
    if vermelho: return "vermelho", vermelho
    if amarelo: return "amarelo", amarelo
    return "verde", []


def program_status(project: str | None = None) -> dict:
    hoje = as_of()
    alvo = [resolver_projeto(project)] if project else list_projects()
    saida = []
    for p in alvo:
        pid = p["project_id"]
        evm = get_evm(pid)
        marcos = _rows("SELECT name, planned_date, actual_date FROM milestones WHERE project_id = ? ORDER BY planned_date", [pid])
        abertos = [m for m in marcos if m["actual_date"] is None]
        atrasados = [{"marco": m["name"], "dias_de_atraso": (hoje - m["planned_date"]).days}
                     for m in abertos if m["planned_date"] < hoje]
        atraso_max = max([a["dias_de_atraso"] for a in atrasados], default=0)
        proximo = next((m for m in abertos if m["planned_date"] >= hoje), None)
        deps = [d for d in _rows("SELECT description, status FROM dependencies WHERE project_id = ?", [pid])]
        itens = _rows("SELECT count(*) AS total, count(done_at) AS feitos FROM work_items WHERE project_id = ?", [pid])[0]
        criticos = _rows("SELECT count(*) AS n FROM risks WHERE project_id = ? AND status <> 'closed' "
                         "AND probability * impact >= 15", [pid])[0]["n"]
        rag, motivos = _rag(evm["spi"], evm["cpi"], atraso_max, deps)
        saida.append({"project_id": pid, "projeto": p["name"], "responsavel": p["owner"], "time": p["team"],
                      "fim_planejado": p["planned_end"].isoformat(), "status": rag, "motivos": motivos,
                      "spi": evm["spi"], "cpi": evm["cpi"],
                      "itens_concluidos": itens["feitos"], "itens_total": itens["total"],
                      "pct_itens_concluidos": round(itens["feitos"] / itens["total"] * 100, 1),
                      "marcos_atrasados": atrasados,
                      "proximo_marco": None if not proximo else {"marco": proximo["name"], "data": proximo["planned_date"].isoformat()},
                      "riscos_criticos": criticos,
                      "dependencias_com_problema": [d for d in deps if d["status"] != "ok"]})
    return {"data_referencia": hoje.isoformat(), "projetos": saida}


# ---------- Previsão de entrega (Monte Carlo) ----------
def _throughput(pid: str, janela: int, hoje: date) -> list[int]:
    semanas = []
    for k in range(janela):
        fim = hoje - timedelta(days=7 * k)
        ini = fim - timedelta(days=7)
        n = _rows("SELECT count(*) AS n FROM work_items WHERE project_id = ? "
                  "AND CAST(done_at AS DATE) > ? AND CAST(done_at AS DATE) <= ?", [pid, ini, fim])[0]["n"]
        semanas.append(int(n))
    return semanas


def _simular(pid: str, janela: int, simulacoes: int):
    hoje = as_of()
    restante = _rows("SELECT count(*) AS n FROM work_items WHERE project_id = ? AND done_at IS NULL", [pid])[0]["n"]
    tp = _throughput(pid, janela, hoje)
    if restante == 0:
        return np.zeros(simulacoes, dtype=int), restante, tp, hoje
    if sum(tp) == 0:
        raise ValueError("Sem entregas nas últimas semanas: não dá para prever.")
    rng = np.random.default_rng(SEMENTE)
    sorteio = rng.choice(np.array(tp), size=(simulacoes, MAX_SEMANAS))
    atingiu = sorteio.cumsum(axis=1) >= restante
    semanas = np.where(atingiu.any(axis=1), atingiu.argmax(axis=1) + 1, MAX_SEMANAS)
    return semanas, restante, tp, hoje


def forecast_delivery(project: str, confidence: int = 85, window_weeks: int = 8) -> dict:
    """Quando o trabalho restante termina, com um nível de confiança (percentil das simulações)."""
    p = resolver_projeto(project)
    confianca = int(confidence)
    if not 50 <= confianca <= 99:
        raise ValueError("A confiança deve estar entre 50 e 99.")
    janela = int(window_weeks)
    if not 4 <= janela <= 12:
        raise ValueError("A janela de throughput deve ter entre 4 e 12 semanas.")
    semanas, restante, tp, hoje = _simular(p["project_id"], janela, SIMULACOES)
    p50 = int(np.percentile(semanas, 50, method="higher"))
    pc = int(np.percentile(semanas, confianca, method="higher"))
    folga_semanas = max((p["planned_end"] - hoje).days // 7, -1)
    prob = float(np.mean(semanas <= folga_semanas) * 100) if folga_semanas >= 0 else 0.0
    data_conf = hoje + timedelta(weeks=pc)
    return {"project_id": p["project_id"], "projeto": p["name"], "data_referencia": hoje.isoformat(),
            "itens_restantes": int(restante), "entregas_por_semana_recentes": tp,
            "confianca_pct": confianca, "semanas_p50": p50, "data_p50": (hoje + timedelta(weeks=p50)).isoformat(),
            "semanas_na_confianca": pc, "data_na_confianca": data_conf.isoformat(),
            "fim_planejado": p["planned_end"].isoformat(),
            "diferenca_para_o_plano_dias": (data_conf - p["planned_end"]).days,
            "chance_de_cumprir_o_prazo_pct": round(prob, 1),
            "metodo": f"{SIMULACOES} simulações sorteando o ritmo das últimas {janela} semanas"}


def distribuicao_semanas(project: str, window_weeks: int = 8):
    """Série {semanas: probabilidade %} para o histograma da página."""
    import pandas as pd
    p = resolver_projeto(project)
    semanas, *_ = _simular(p["project_id"], int(window_weeks), SIMULACOES)
    cont = pd.Series(semanas).value_counts(normalize=True).sort_index() * 100
    return cont.round(2)
