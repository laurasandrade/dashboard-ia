"""Gera exemplos_demo.json a partir das suas interações reais (logs/interacoes.jsonl).

Uso:  python exportar_exemplos.py
Depois ABRA o exemplos_demo.json, apague o que não quiser mostrar e confira as respostas.
Ficam de fora: respostas com erro e respostas com número sem fonte.
"""
import json
from pathlib import Path

from observabilidade import carregar

SAIDA = Path(__file__).parent / "exemplos_demo.json"
MAX_EXEMPLOS = 12


def main():
    vistos, escolhidos = set(), []
    for r in reversed(carregar()):  # mais recentes primeiro
        if r.get("origem") not in ("avaliacao", "app") or r.get("erro") or not r.get("resposta"):
            continue
        if r.get("numeros_nao_rastreados") or r["pergunta"] in vistos:
            continue
        vistos.add(r["pergunta"])
        escolhidos.append({"pergunta": r["pergunta"], "resposta": r["resposta"],
                           "ferramentas": r.get("ferramentas", []), "latencia_s": r.get("latencia_s")})
    escolhidos = list(reversed(escolhidos[:MAX_EXEMPLOS]))
    SAIDA.write_text(json.dumps(escolhidos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(escolhidos)} exemplos salvos em {SAIDA.name}. Revise o arquivo antes de publicar.")


if __name__ == "__main__":
    main()
