"""DORA Copilot: dashboard + assistente.  Rodar com: streamlit run app.py"""
import os
from datetime import date, timedelta

import streamlit as st

import metrics

st.set_page_config(page_title="DORA Copilot", page_icon="📊", layout="wide")

# nome, unidade, "menor é melhor?"
LABELS = {
    "deploy_frequency": ("Deploy frequency", "deploys/semana", False),
    "lead_time": ("Lead time", "horas", True),
    "change_failure_rate": ("Change failure rate", "%", True),
    "mttr": ("MTTR", "horas", True),
}
DATA_START, DATA_END = date(2026, 5, 1), date(2026, 10, 31)

st.title("📊 DORA Copilot")
st.caption("Métricas de entrega (dados sintéticos) com um assistente de IA que consulta os números por ferramentas.")

# ---------- filtros ----------
with st.sidebar:
    st.header("Filtros")
    team_choice = st.selectbox("Time", ["Todos"] + metrics.list_teams())
    period = st.date_input(
        "Período",
        value=(date(2026, 9, 1), DATA_END),
        min_value=DATA_START,
        max_value=DATA_END,
    )
team = None if team_choice == "Todos" else team_choice

if len(period) != 2:
    st.info("Selecione a data inicial e a final no filtro de período.")
    st.stop()

start, end = period
n_days = (end - start).days + 1
prev_end = start - timedelta(days=1)
prev_start = prev_end - timedelta(days=n_days - 1)
s, e, ps, pe = (d.isoformat() for d in (start, end, prev_start, prev_end))

st.subheader(f"{team_choice}: {start:%d/%m/%Y} a {end:%d/%m/%Y}")
st.caption(f"Variação comparada ao período anterior de mesmo tamanho ({prev_start:%d/%m} a {prev_end:%d/%m}).")

# ---------- KPIs ----------
for col, (metric, (label, unit, lower_is_better)) in zip(st.columns(4), LABELS.items()):
    cur = metrics.get_metric(metric, s, e, team)["value"]
    prev = metrics.get_metric(metric, ps, pe, team)["value"]
    delta = None
    if cur is not None and prev:
        delta = f"{(cur - prev) / prev * 100:+.1f}%"
    col.metric(
        f"{label} ({unit})",
        "sem dados" if cur is None else f"{cur:.1f}",
        delta,
        delta_color="inverse" if lower_is_better else "normal",
    )

# ---------- gráficos semanais ----------
st.markdown("#### Evolução semanal")
chart_cols = st.columns(2)
for i, (metric, (label, unit, _)) in enumerate(LABELS.items()):
    with chart_cols[i % 2]:
        st.markdown(f"**{label}** ({unit})")
        series = metrics.get_weekly_series(metric, s, e, team)
        if series.empty:
            st.caption("Sem dados no período.")
        else:
            st.line_chart(series.set_index("week")["value"])

# ---------- chat com o assistente ----------
st.divider()
st.subheader("💬 Pergunte ao Copilot")
st.caption("Ex.: Como está o MTTR do time Pagamentos em outubro? · Compare o lead time de maio com outubro.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("meta"):
            st.caption(msg["meta"])

question = st.chat_input("Faça uma pergunta sobre as métricas...")
if question:
    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        if not os.getenv("ANTHROPIC_API_KEY"):
            st.warning("Defina a variável de ambiente ANTHROPIC_API_KEY e reinicie o app.")
        else:
            try:
                import assistant
                history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                with st.spinner("Consultando os dados..."):
                    result = assistant.ask(history)
                st.markdown(result["text"])
                meta = (f"{result['latency_s']}s · {result['tokens_in']} tokens de entrada · "
                        f"{result['tokens_out']} de saída · ferramentas: "
                        f"{', '.join(c['tool'] for c in result['tool_calls']) or 'nenhuma'}")
                st.caption(meta)
                if result["tool_calls"]:
                    with st.expander("Ver chamadas de ferramenta (transparência)"):
                        for call in result["tool_calls"]:
                            st.json(call, expanded=False)
                st.session_state.messages.append(
                    {"role": "assistant", "content": result["text"], "meta": meta})
            except Exception as exc:
                st.error(f"Erro ao consultar o assistente: {exc}")
                st.session_state.messages.pop()  # evita deixar a pergunta sem resposta no histórico
