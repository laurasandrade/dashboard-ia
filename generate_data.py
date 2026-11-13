"""Gera dados sintéticos de entrega (estilo Jira/GitHub) em DuckDB.

Tabelas:
  changes   -> cada mudança que foi para produção
  incidents -> incidentes causados por mudanças que falharam
Uso: python generate_data.py
"""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)  # seed fixa = dados reproduzíveis

# time -> "velocidade" relativa (quanto maior, mais deploys)
TEAMS = {"Pagamentos": 1.0, "Onboarding": 0.8, "Plataforma": 1.2, "Dados": 0.6, "Mobile": 0.9}
START = pd.Timestamp("2026-05-01")
END = pd.Timestamp("2026-10-31")
DB_PATH = Path(__file__).parent / "dora.duckdb"


def generate_team(team: str, speed: float):
    changes, incidents = [], []
    days = pd.date_range(START, END, freq="D")
    for i, day in enumerate(days):
            continue
        progress = i / len(days)  # 0 -> 1: o time melhora ao longo do tempo
        n_deploys = rng.poisson(speed * (0.8 + 0.8 * progress))
        for _ in range(n_deploys):
            deployed_at = day + pd.Timedelta(hours=float(rng.uniform(9, 18)))
            lead_h = float(rng.lognormal(np.log(72 * (1 - 0.4 * progress)), 0.6))
            failed = bool(rng.random() < (0.22 - 0.12 * progress))
            change_id = f"{team[:3].upper()}-{len(changes) + 1:04d}"
            changes.append({
                "change_id": change_id,
                "team": team,
                "first_commit_at": deployed_at - pd.Timedelta(hours=lead_h),
                "deployed_at": deployed_at,
                "failed": failed,
            })
            if failed:
                mttr_h = float(rng.lognormal(np.log(6 * (1 - 0.35 * progress)), 0.7))
                incidents.append({
                    "incident_id": f"INC-{team[:3].upper()}-{len(incidents) + 1:04d}",
                    "team": team,
                    "change_id": change_id,
                    "started_at": deployed_at + pd.Timedelta(minutes=int(rng.integers(5, 60))),
                    "resolved_at": deployed_at + pd.Timedelta(hours=mttr_h),
                })
    return changes, incidents


def main():
    all_changes, all_incidents = [], []
    for team, speed in TEAMS.items():
        c, inc = generate_team(team, speed)
        all_changes += c
        all_incidents += inc
    changes_df = pd.DataFrame(all_changes)
    incidents_df = pd.DataFrame(all_incidents)

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE changes AS SELECT * FROM changes_df")
    con.execute("CREATE OR REPLACE TABLE incidents AS SELECT * FROM incidents_df")
    print(f"changes: {len(changes_df)} | incidents: {len(incidents_df)} | db: {DB_PATH}")


if __name__ == "__main__":
    main()
