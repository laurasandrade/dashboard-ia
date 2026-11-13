"""Guardrails do assistente: validação de entrada e checagem de números na saída.

A checagem de saída é a mais importante para o case: todo número que o modelo escreve
precisa aparecer nas fontes consultadas (banco ou documentação) ou na própria pergunta.
Número que não aparece é sinalizado na tela, porque pode ser conta ou invenção do modelo.
"""
import re

MAX_CARACTERES = 500
# número com milhar em pt-BR (1.347.000 ou 1.347,50) ou número simples (48,9 | 48.9 | 7)
# (?<![A-Za-z\d]): ignora número colado em letra, como P50, P85, SEV1 ou R-03 (rótulos, não valores)
_NUM = re.compile(r"(?<![A-Za-z\d])(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:[.,]\d+)?)")
_MILHAR = re.compile(r"\d{1,3}(?:\.\d{3})+(?:,\d+)?")


def validar_entrada(pergunta: str) -> str | None:
    """Devolve a mensagem de erro, ou None se a pergunta é aceitável."""
    p = (pergunta or "").strip()
    if not p:
        return "Digite uma pergunta."
    if len(p) > MAX_CARACTERES:
        return f"Pergunta longa demais (máximo de {MAX_CARACTERES} caracteres)."
    return None


def _valor(s: str) -> float:
    return float(s.replace(",", "."))


def _casas(s: str) -> int:
    m = re.search(r"[.,](\d+)$", s)
    return len(m.group(1)) if m else 0


def _interpretacoes(s: str) -> list[tuple[float, int]]:
    """Valores possíveis do texto. "1.347" pode ser mil trezentos e quarenta e sete (pt-BR)
    ou 1,347 (ponto decimal); aceitamos se qualquer leitura bater com as fontes."""
    leituras = []
    if _MILHAR.fullmatch(s):
        sem_milhar = s.replace(".", "")
        casas = len(sem_milhar.split(",")[1]) if "," in sem_milhar else 0
        leituras.append((float(sem_milhar.replace(",", ".")), casas))
    if not _MILHAR.fullmatch(s) or "," not in s:
        try:
            leituras.append((_valor(s), _casas(s)))
        except ValueError:
            pass
    return leituras


def _coletar(obj, saida: set) -> None:
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        saida.add(abs(float(obj)))  # "caiu 70%" e delta_pct = -70.0 são o mesmo número
    elif isinstance(obj, str):
        saida.update(_valor(n) for n in _NUM.findall(obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):  # "semanas_p50" torna legítimo falar em 50% (mediana)
                saida.update(float(n) for n in re.findall(r"\d+", k))
            _coletar(v, saida)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _coletar(v, saida)


def verificar_numeros(resposta: str, pergunta: str, chamadas: list[dict]) -> list[str]:
    """Números da resposta que não aparecem na pergunta nem nas fontes consultadas."""
    permitidos: set[float] = set()
    _coletar(pergunta, permitidos)
    for c in chamadas:
        _coletar(c.get("argumentos"), permitidos)
        _coletar(c.get("resultado"), permitidos)

    nao_rastreados = []
    for s in dict.fromkeys(_NUM.findall(resposta or "")):
        leituras = _interpretacoes(s)
        if any(d == 0 and (v <= 31 or 2020 <= v <= 2035) for v, d in leituras):
            continue  # datas, contagens pequenas, anos
        if not any(round(p, d) == round(v, d) for v, d in leituras for p in permitidos):
            nao_rastreados.append(s)
    return nao_rastreados
