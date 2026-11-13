"""Visão de programa: status, dependências, riscos, previsão de entrega (Monte Carlo) e EVM."""
import pandas as pd
import streamlit as st

import program

st.set_page_config(page_title="Programa · DORA Copilot", page_icon="🗂️", layout="wide")
st.title("🗂️ Visão do programa")
st.caption(f"Projetos fictícios · dados sintéticos · data de referência {program.as_of():%d/%m/%Y}")

EMOJI = {"verde": "🟢", "amarelo": "🟡", "vermelho": "🔴"}
projetos = program.program_status()["projetos"]
nomes = {p["project_id"]: f'{p["project_id"]} · {p["projeto"]}' for p in projetos}

aba_proj, aba_dep, aba_risco, aba_prev, aba_evm = st.tabs(
    ["Projetos", "Dependências", "Riscos", "Previsão de entrega", "Prazo e custo (EVM)"])

with aba_proj:
    cont = {s: sum(p["status"] == s for p in projetos) for s in EMOJI}
    c = st.columns(3)
    for col, (s, e) in zip(c, EMOJI.items()):
        col.metric(f"{e} {s.capitalize()}", cont[s])
    df = pd.DataFrame([{
        "Status": f'{EMOJI[p["status"]]} {p["status"]}', "Projeto": p["projeto"], "Responsável": p["responsavel"],
        "SPI": p["spi"], "CPI": p["cpi"], "Itens concluídos (%)": p["pct_itens_concluidos"],
        "Fim planejado": p["fim_planejado"], "Riscos críticos": p["riscos_criticos"],
        "Motivos": "; ".join(p["motivos"]) or "-"} for p in projetos])
    st.dataframe(df, hide_index=True)
    st.markdown("**Marcos atrasados**")
    atrasos = [{"Projeto": p["projeto"], "Marco": a["marco"], "Dias de atraso": a["dias_de_atraso"]}
               for p in projetos for a in p["marcos_atrasados"]]
    st.dataframe(pd.DataFrame(atrasos), hide_index=True) if atrasos else st.write("Nenhum marco atrasado.")
    with st.expander("Como o status é definido"):
        st.markdown("**Vermelho:** SPI ou CPI abaixo de 0,85, marco atrasado há mais de 14 dias ou dependência "
                    "bloqueada.  \n**Amarelo:** SPI abaixo de 0,95, CPI abaixo de 0,90, marco atrasado até 14 dias "
                    "ou dependência em risco.  \n**Verde:** nenhuma das condições.")

with aba_dep:
    so_problemas = st.checkbox("Só dependências com problema", value=True)
    deps = program.list_dependencies(only_issues=so_problemas)["dependencias"]
    if deps:
        st.dataframe(pd.DataFrame(deps).rename(columns={
            "dep_id": "Id", "dependente": "Projeto dependente", "fornecedor": "Projeto fornecedor",
            "descricao": "Descrição", "necessaria_ate": "Necessária até",
            "dias_ate_o_prazo": "Dias até o prazo", "status": "Status"}), hide_index=True)
        st.caption("Dias até o prazo negativo = a data necessária já passou.")
    else:
        st.write("Nenhuma dependência para mostrar.")

with aba_risco:
    riscos = program.list_risks()["riscos"]
    dfr = pd.DataFrame(riscos)
    st.markdown("**Matriz de riscos abertos** (probabilidade x impacto, quantidade de riscos em cada célula)")
    matriz = pd.crosstab(dfr["probabilidade"], dfr["impacto"]).reindex(
        index=[5, 4, 3, 2, 1], columns=[1, 2, 3, 4, 5], fill_value=0)
    matriz.index.name, matriz.columns.name = "Probabilidade", "Impacto"
    st.dataframe(matriz)
    st.markdown("**Lista de riscos** (maior pontuação primeiro)")
    st.dataframe(dfr[["risk_id", "projeto", "titulo", "categoria", "pontuacao", "responsavel", "status", "mitigacao"]]
                 .rename(columns={"risk_id": "Id", "projeto": "Projeto", "titulo": "Risco", "categoria": "Categoria",
                                  "pontuacao": "Pontuação", "responsavel": "Responsável", "status": "Status",
                                  "mitigacao": "Mitigação"}), hide_index=True)

with aba_prev:
    st.markdown("Quando o trabalho restante termina, a partir do **ritmo real de entrega** das últimas semanas.")
    c1, c2, c3 = st.columns(3)
    pid = c1.selectbox("Projeto", list(nomes), format_func=nomes.get, key="prev_proj")
    conf = c2.slider("Nível de confiança (%)", 50, 95, 85, step=5)
    janela = c3.slider("Semanas de histórico", 4, 12, 8)
    f = program.forecast_delivery(pid, conf, janela)
    m = st.columns(4)
    m[0].metric("Itens restantes", f["itens_restantes"])
    m[1].metric("Mediana (P50)", f"{pd.Timestamp(f['data_p50']):%d/%m/%Y}")
    m[2].metric(f"Com {conf}% de confiança", f"{pd.Timestamp(f['data_na_confianca']):%d/%m/%Y}",
                delta=f"{f['diferenca_para_o_plano_dias']:+d} dias vs. plano", delta_color="inverse")
    m[3].metric("Chance de cumprir o prazo", f"{f['chance_de_cumprir_o_prazo_pct']}%",
                help=f"Fim planejado: {pd.Timestamp(f['fim_planejado']):%d/%m/%Y}")
    st.markdown("**Distribuição das simulações** (probabilidade % de terminar em cada número de semanas)")
    st.bar_chart(program.distribuicao_semanas(pid, janela))
    st.caption(f"{f['metodo']}. Entregas por semana (da mais recente para a mais antiga): "
               f"{f['entregas_por_semana_recentes']}. Não é uma promessa: se o ritmo ou o escopo mudarem, a previsão muda.")

with aba_evm:
    pid2 = st.selectbox("Projeto", list(nomes), format_func=nomes.get, key="evm_proj")
    e = program.get_evm(pid2)
    m = st.columns(4)
    m[0].metric("SPI (prazo)", e["spi"], help="Abaixo de 1: atrasado em relação ao plano")
    m[1].metric("CPI (custo)", e["cpi"], help="Abaixo de 1: gastando mais do que o trabalho entregue")
    m[2].metric("Estimativa final (EAC)", f"R$ {e['estimativa_final_eac']:,}".replace(",", "."))
    m[3].metric("Variação final (VAC)", f"R$ {e['variacao_final_vac']:,}".replace(",", "."),
                help="Negativo: estouro de orçamento projetado")
    st.line_chart(program.evm_series(pid2).set_index("week_end"))
    st.caption("PV = valor planejado, EV = valor agregado (trabalho concluído), AC = custo real, acumulados.")
