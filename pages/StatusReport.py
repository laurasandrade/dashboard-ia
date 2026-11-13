"""Status report semanal: versão sem IA (sempre disponível) e versão redigida pelo Gemini."""
import os

import streamlit as st

import demo
import status_report as sr

st.set_page_config(page_title="Status report · DORA Copilot", page_icon="📝")
st.title("📝 Status report semanal")
st.caption("Os fatos são calculados por código. Na versão com IA, o modelo só redige; "
           "o guardrail confere se cada número do texto existe nos fatos.")

pacote = sr.montar_pacote()
sem_ia = sr.relatorio_sem_ia(pacote)
tem_chave = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))

demo.tela_de_acesso()
pode, motivo = demo.pode_usar_ia()
if st.button("Gerar versão com IA (Gemini)", disabled=not (tem_chave and pode)):
    with st.spinner("Redigindo o relatório..."):
        st.session_state.relatorio_ia = sr.gerar_relatorio_ia(pacote)
    demo.registrar_uso()
if not tem_chave:
    st.info("Sem chave do Gemini neste terminal: a versão sem IA continua disponível abaixo.")
elif not pode and demo.ia_liberada():
    st.warning(motivo)

r = st.session_state.get("relatorio_ia")
if r:
    if r["erro"]:
        st.error(r["erro"])
    else:
        if r["numeros_nao_rastreados"]:
            st.warning("Números que não aparecem nos fatos: " + ", ".join(r["numeros_nao_rastreados"])
                       + ". Confira antes de enviar.")
        else:
            st.success("Todos os números do texto existem nos fatos calculados.")
        st.markdown(r["texto"])
        st.caption(f"{r['latencia_s']} s")
        st.download_button("Baixar versão com IA (.md)", r["texto"], file_name="status-report-ia.md")

with st.expander("Versão sem IA (determinística)", expanded=not r):
    st.markdown(sem_ia)
    st.download_button("Baixar versão sem IA (.md)", sem_ia, file_name="status-report.md")
