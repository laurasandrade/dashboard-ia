"""Painel de observabilidade: uso, latência, erros e alertas do assistente."""
from collections import Counter
from pathlib import Path

import pandas as pd
import streamlit as st

import demo
from observabilidade import carregar

st.set_page_config(page_title="Observabilidade · DORA Copilot", page_icon="🔎", layout="wide")
st.title("🔎 Observabilidade do assistente")

publicada = Path(__file__).resolve().parent.parent / "avaliacao" / "publicada.md"
if publicada.exists():
    st.subheader("Última avaliação publicada")
    with st.expander("Resultado da avaliação com perguntas fixas", expanded=False):
        st.markdown(publicada.read_text(encoding="utf-8"))

st.subheader("Uso ao vivo")

df = pd.DataFrame(carregar())
if df.empty:
    st.info("Ainda não há interações registradas. Faça perguntas na página Assistente.")
    st.stop()

origens = ["todas"] + sorted(df["origem"].dropna().unique().tolist())
origem = st.sidebar.selectbox("Origem", origens)
if origem != "todas":
    df = df[df["origem"] == origem]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Interações", len(df))
c2.metric("Latência média", f"{df['latencia_s'].mean():.1f} s")
c3.metric("Com erro", f"{df['erro'].notna().mean() * 100:.0f} %")
c4.metric("Com número não rastreado",
          f"{(df['numeros_nao_rastreados'].apply(len) > 0).mean() * 100:.0f} %")

st.subheader("Uso das ferramentas")
uso = Counter(f for fs in df["ferramentas"] for f in fs)
if uso:
    st.bar_chart(pd.Series(uso))
else:
    st.write("Nenhuma ferramenta chamada ainda.")

st.subheader("Últimas interações")
if demo.modo_demo():
    st.caption("Em modo demonstração, o texto das perguntas fica oculto para proteger quem está testando.")
else:
    ultimas = df.sort_values("quando", ascending=False).head(30)
    st.dataframe(ultimas[["quando", "origem", "pergunta", "ferramentas", "passos",
                          "latencia_s", "erro", "numeros_nao_rastreados"]],
                 hide_index=True)
