"""Registro simples das interações (JSON Lines) para análise de qualidade, custo e latência."""
import json
from pathlib import Path

LOG = Path(__file__).parent / "logs" / "interacoes.jsonl"


def registrar(registro: dict) -> None:
    try:
        LOG.parent.mkdir(exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass  # log nunca pode derrubar o assistente


def carregar() -> list[dict]:
    if not LOG.exists():
        return []
    linhas = []
    for linha in LOG.read_text(encoding="utf-8").splitlines():
        try:
            linhas.append(json.loads(linha))
        except json.JSONDecodeError:
            continue
    return linhas
