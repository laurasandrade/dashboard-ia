"""Cálculo das 4 métricas DORA sobre o DuckDB.

Estas funções são SOMENTE LEITURA e serão expostas ao LLM como tools
(tool calling) na Semana 2: o modelo nunca escreve SQL livre.
"""
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).parent / "dora.duckdb"

METRICS = {
    "deploy_frequency": "deploys por semana",
    "lead_time": "horas (mediana, do 1º commit ao deploy)",
    "change_failure_rate": "% de mudanças que falharam",
    "mttr": "horas (média para restaurar o serviço)",
}


def _con():
    return duckdb.connect(str(DB_PATH), read_only=True)


def get_metric(metric: str, start: str, end: str, team: str | None = None) -> dict:
    """Valor de uma métrica DORA num período [start, end] (YYYY-MM-DD), opcionalmente por time."""
    if metric not in METRICS:
        raise ValueError(f"Métrica inválida: {metric}. Opções: {list(METRICS)}")
    params = [start, end + " 23:59:59"]
    team_filter = ""
    if team:
        team_filter = " AND team = ?"
        params.append(team)

    if metric == "deploy_frequency":
        sql = f"SELECT count(*) FROM changes WHERE deployed_at BETWEEN ? AND ?{team_filter}"
    elif metric == "lead_time":
        sql = ("SELECT median(epoch(deployed_at - first_commit_at) / 3600) FROM changes "
               f"WHERE deployed_at BETWEEN ? AND ?{team_filter}")
    elif metric == "change_failure_rate":
        sql = ("SELECT avg(failed::INT) * 100 FROM changes "
               f"WHERE deployed_at BETWEEN ? AND ?{team_filter}")
    else:  # mttr
        sql = ("SELECT avg(epoch(resolved_at - started_at) / 3600) FROM incidents "
               f"WHERE started_at BETWEEN ? AND ?{team_filter}")

    value = _con().execute(sql, params).fetchone()[0]
    if value is None:
        return {"metric": metric, "value": None, "note": "sem dados no período"}
    if metric == "deploy_frequency":
        weeks = max((_days(start, end)) / 7, 1)
        value = value / weeks
    return {"metric": metric, "unit": METRICS[metric], "team": team or "todos",
            "start": start, "end": end, "value": round(float(value), 2)}

def compare_periods(metric: str, a_start: str, a_end: str, b_start: str, b_end: str,
                    team: str | None = None) -> dict:
    """Compara a mesma métrica em dois períodos (A = base, B = atual)."""
    a = get_metric(metric, a_start, a_end, team)
    b = get_metric(metric, b_start, b_end, team)
    if a["value"] is None or b["value"] is None or a["value"] == 0:
        return {"metric": metric, "a": a, "b": b, "delta_abs": None, "delta_pct": None}
    delta = (b["value"] - a["value"]) / a["value"] * 100
    return {"metric": metric, "a": a, "b": b,
            "delta_abs": round(b["value"] - a["value"], 2),
            "delta_pct": round(delta, 1)}
            
def get_weekly_series(metric: str, start: str, end: str, team: str | None = None):
    """Série semanal de uma métrica (DataFrame com colunas week e value), para os gráficos."""
    if metric not in METRICS:
        raise ValueError(f"Métrica inválida: {metric}. Opções: {list(METRICS)}")
    params = [start, end + " 23:59:59"]
    team_filter = ""
    if team:
        team_filter = " AND team = ?"
        params.append(team)

    if metric == "deploy_frequency":
        agg, table, col = "count(*)", "changes", "deployed_at"
    elif metric == "lead_time":
        agg, table, col = "median(epoch(deployed_at - first_commit_at) / 3600)", "changes", "deployed_at"
    elif metric == "change_failure_rate":
        agg, table, col = "avg(failed::INT) * 100", "changes", "deployed_at"
    else:  # mttr
        agg, table, col = "avg(epoch(resolved_at - started_at) / 3600)", "incidents", "started_at"

    sql = (f"SELECT date_trunc('week', {col}) AS week, {agg} AS value FROM {table} "
           f"WHERE {col} BETWEEN ? AND ?{team_filter} GROUP BY 1 ORDER BY 1")
    return _con().execute(sql, params).df()


def list_teams() -> list[str]:
    return [r[0] for r in _con().execute("SELECT DISTINCT team FROM changes ORDER BY 1").fetchall()]


def _days(start: str, end: str) -> int:
    from datetime import date
    return (date.fromisoformat(end) - date.fromisoformat(start)).days + 1


if __name__ == "__main__":
    for m in METRICS:
        print(get_metric(m, "2026-05-01", "2026-10-31"))
    print(compare_periods("change_failure_rate", "2026-05-01", "2026-06-30",
                          "2026-09-01", "2026-10-31"))
