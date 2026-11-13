"""Modo demonstração: libera os recursos de IA só com um código e limita o uso.

Serve para publicar o app sem expor a sua cota gratuita do Gemini.
- Sem DEMO_CODE definido (uso local), nada é bloqueado.
- Com DEMO_CODE definido (app público), quem não tem o código vê tudo, menos as chamadas
  ao Gemini; no lugar, aparecem exemplos reais gravados (exemplos_demo.json).

Variáveis de ambiente (no Streamlit Cloud, em Secrets):
    DEMO_CODE         código de acesso que você passa para recrutadores
    DEMO_MAX_SESSAO   perguntas por visitante (padrão 8)
    DEMO_MAX_DIA      perguntas por dia, somando todos (padrão 60)
"""
import hmac
import json
import os
from datetime import date
from pathlib import Path

import streamlit as st

from observabilidade import carregar

EXEMPLOS = Path(__file__).parent / "exemplos_demo.json"


def modo_demo() -> bool:
    return bool(os.environ.get("DEMO_CODE"))


def _limite(nome: str, padrao: int) -> int:
    try:
        return int(os.environ.get(nome, padrao))
    except ValueError:
        return padrao


def usos_hoje() -> int:
    hoje = date.today().isoformat()
    return sum(1 for r in carregar()
               if r.get("origem") in ("app", "status_report") and str(r.get("quando", "")).startswith(hoje))


def ia_liberada() -> bool:
    return (not modo_demo()) or st.session_state.get("demo_liberado", False)


def tela_de_acesso() -> None:
    """Pede o código quando o app está em modo demonstração e ainda não foi liberado."""
    if ia_liberada():
        return
    st.info("Os recursos de IA usam uma cota gratuita limitada e são liberados por um código. "
            "Sem o código, você pode explorar o resto do app e ler exemplos reais.")
    codigo = st.text_input("Código de acesso", type="password", key="demo_codigo")
    if codigo:
        if hmac.compare_digest(codigo, os.environ["DEMO_CODE"]):
            st.session_state.demo_liberado = True
            st.rerun()
        else:
            st.error("Código incorreto.")


def pode_usar_ia() -> tuple[bool, str]:
    if not ia_liberada():
        return False, "Informe o código de acesso para usar a IA."
    if modo_demo():
        if st.session_state.get("demo_usos", 0) >= _limite("DEMO_MAX_SESSAO", 8):
            return False, "Limite de perguntas desta sessão atingido (modo demonstração)."
        if usos_hoje() >= _limite("DEMO_MAX_DIA", 60):
            return False, "O limite diário da demonstração foi atingido. Volte amanhã."
    return True, ""


def registrar_uso() -> None:
    st.session_state.demo_usos = st.session_state.get("demo_usos", 0) + 1


def mostrar_exemplos() -> None:
    """Perguntas e respostas reais, gravadas por exportar_exemplos.py."""
    try:
        exemplos = json.loads(EXEMPLOS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        exemplos = []
    if not exemplos:
        st.write("Exemplos ainda não publicados.")
        return
    st.markdown("**Exemplos reais de perguntas e respostas do assistente**")
    for ex in exemplos:
        with st.expander(ex["pergunta"]):
            st.markdown(ex["resposta"])
            if ex.get("ferramentas"):
                st.caption("Ferramentas consultadas: " + ", ".join(ex["ferramentas"])
                           + (f" · {ex['latencia_s']} s" if ex.get("latencia_s") else ""))
