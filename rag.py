"""RAG simples e gratuito: busca lexical BM25 sobre a pasta docs/ (arquivos .md).

Decisão de projeto: BM25 em vez de embeddings. A base é pequena e de vocabulário
controlado, então a busca lexical é suficiente, roda offline, não consome cota de API
e é totalmente explicável. Se a base crescer ou as perguntas ficarem mais livres,
a troca por embeddings fica isolada neste arquivo.
"""
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

DOCS_DIR = Path(__file__).parent / "docs"
STOP = {"a", "o", "as", "os", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
        "um", "uma", "e", "ou", "que", "para", "por", "com", "se", "ao", "como", "qual",
        "quais", "e", "sao", "ser", "foi", "tem", "mais", "menos", "ha", "meu", "minha"}
MAX_TRECHO = 900


def _norm(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")


def _tokens(texto: str) -> list[str]:
    saida = []
    for t in re.findall(r"[a-z0-9]+", _norm(texto)):
        if t in STOP or len(t) < 2:
            continue
        if len(t) > 3 and t.endswith("s"):  # plural simples
            t = t[:-1]
        if len(t) > 5:  # radical por prefixo: calculado, cálculo e calcula viram "calcu"
            t = t[:5]
        saida.append(t)
    return saida


def _trechos(caminho: Path) -> list[dict]:
    """Quebra o .md por títulos (#, ##); trechos longos são divididos por parágrafo."""
    titulo_doc, secao, buffer, partes = caminho.stem, "", [], []

    def fechar():
        corpo = "\n".join(buffer).strip()
        if corpo:
            partes.append((secao, corpo))

    for linha in caminho.read_text(encoding="utf-8").splitlines():
        if linha.startswith("#"):
            fechar()
            buffer.clear()
            secao = linha.lstrip("# ").strip()
        else:
            buffer.append(linha)
    fechar()

    saida = []
    for sec, corpo in partes:
        atual = ""
        for par in corpo.split("\n\n"):
            if atual and len(atual) + len(par) > MAX_TRECHO:
                saida.append({"fonte": caminho.name, "secao": sec, "texto": atual.strip()})
                atual = ""
            atual += par + "\n\n"
        if atual.strip():
            saida.append({"fonte": caminho.name, "secao": sec, "texto": atual.strip()})
    return saida


class Indice:
    def __init__(self, pasta: Path = DOCS_DIR, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.trechos = []
        for arq in sorted(pasta.glob("*.md")):
            self.trechos += _trechos(arq)
        # o título da seção entra duas vezes na indexação: ajuda a achar "MTTR", "Lead time" etc.
        self.tokens = [_tokens(t["secao"]) * 2 + _tokens(t["texto"]) for t in self.trechos]
        n = max(len(self.tokens), 1)
        self.tam_medio = sum(len(t) for t in self.tokens) / n or 1
        df = Counter(tok for toks in self.tokens for tok in set(toks))
        self.idf = {tok: math.log(1 + (n - c + 0.5) / (c + 0.5)) for tok, c in df.items()}

    def buscar(self, consulta: str, k: int = 3, score_minimo: float = 1.0) -> list[dict]:
        q = set(_tokens(consulta))
        resultados = []
        for i, toks in enumerate(self.tokens):
            freq = Counter(toks)
            score = 0.0
            for tok in q:
                f = freq.get(tok, 0)
                if f:
                    norm = f + self.k1 * (1 - self.b + self.b * len(toks) / self.tam_medio)
                    score += self.idf.get(tok, 0) * f * (self.k1 + 1) / norm
            if score >= score_minimo:
                t = self.trechos[i]
                resultados.append({"fonte": t["fonte"], "secao": t["secao"],
                                   "trecho": t["texto"], "score": round(score, 2)})
        return sorted(resultados, key=lambda r: -r["score"])[:k]


_indice = None
_assinatura = None


def buscar_docs(consulta: str, k: int = 3) -> list[dict]:
    """Busca nos documentos; recria o índice sozinho se algum .md mudar."""
    global _indice, _assinatura
    arquivos = sorted(DOCS_DIR.glob("*.md"))
    assinatura = [(a.name, a.stat().st_mtime) for a in arquivos]
    if _indice is None or assinatura != _assinatura:
        _indice, _assinatura = Indice(), assinatura
    return _indice.buscar(consulta, k)
