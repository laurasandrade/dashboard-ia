"""Página do assistente (o Streamlit a lista no menu lateral, junto do dashboard)."""
import os

import streamlit as st

import demo
from assistant import MODELO, perguntar

st.set_page_config(page_title="Assistente · DORA Copilot", page_icon="🤖")
st.title("🤖 Assistente DORA")
st.caption(f"Pergunte em linguagem natural. O modelo ({MODELO}) consulta as métricas por "
           "ferramentas somente leitura: os números vêm do banco e as regras vêm da documentação, não do modelo.")

demo.tela_de_acesso()
if not demo.ia_liberada():
    demo.mostrar_exemplos()
    st.stop()

if not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
    st.error("Chave do Gemini não encontrada. No PowerShell, antes de rodar o Streamlit:\n\n"
             '`$env:GEMINI_API_KEY="sua-chave"`')
    st.stop()

with st.sidebar:
    st.markdown("**Exemplos de pergunta**")
    st.markdown("- A taxa de falha piorou no último mês?\n"
                "- Compare o MTTR do time Dados com o do time Mobile.\n"
                "- Como o lead time é calculado?\n"
                "- O time Mobile atingiu a meta de lead time no último mês?\n"
                "- Quando fazemos o post-mortem de um incidente?")
    if st.button("Limpar conversa"):
        st.session_state.msgs = []
        st.rerun()

if "msgs" not in st.session_state:
    st.session_state.msgs = []


def mostrar_chamadas(chamadas):
    if chamadas:
        with st.expander(f"Ferramentas consultadas ({len(chamadas)})"):
            for c in chamadas:
                st.markdown(f"`{c['ferramenta']}`")
                st.json({"argumentos": c["argumentos"], "resultado": c["resultado"]}, expanded=False)


for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        mostrar_chamadas(m.get("chamadas"))

pergunta = st.chat_input("Ex.: a taxa de falha piorou no time Dados no último mês?")
if pergunta:
    pode, motivo = demo.pode_usar_ia()
    if not pode:
        st.warning(motivo)
        st.stop()
    historico = [(m["role"], m["content"]) for m in st.session_state.msgs]
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Consultando as métricas..."):
            r = perguntar(pergunta, historico)
        demo.registrar_uso()
        if r["erro"]:
            st.error(r["erro"])
        else:
            st.markdown(r["resposta"])
            if r["numeros_nao_rastreados"]:
                st.warning("Números que não aparecem nas fontes consultadas: "
                           + ", ".join(r["numeros_nao_rastreados"])
                           + ". Podem ser contas do modelo; confira antes de usar.")
            mostrar_chamadas(r["chamadas"])
            st.caption(f"{r['latencia_s']} s · {r['passos']} chamada(s) ao modelo")
    if not r["erro"]:
        st.session_state.msgs.append({"role": "user", "content": pergunta})
        st.session_state.msgs.append({"role": "assistant", "content": r["resposta"],
                                      "chamadas": r["chamadas"]})
