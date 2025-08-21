import streamlit as st
import pandas as pd
from graphviz import Digraph
import textwrap
from collections import defaultdict
import re
import base64
import os

st.set_page_config(page_title="Organograma Dinâmico", layout="wide")

st.title("📊 Organograma Interativo")
st.write("Carregue um arquivo Excel com as colunas: **Nome, Cargo, Gestor, Setor**")

uploaded_file = st.file_uploader("Selecione o arquivo Excel", type=["xlsx"])

def criar_organograma(df, largura_max=20):
    dot = Digraph(comment="Organograma", format="svg")
    dot.attr(rankdir="TB", size="9", nodesep="0.3", ranksep="0.4")
    dot.attr("node", shape="box", style="rounded,filled", color="lightblue",
             fontname="Helvetica", fontsize="12", width="1.6", height="0.9", fixedsize="false")
    dot.attr(splines="ortho")

    # Regex para cargos operacionais
    re_operacional = re.compile(r"\b(analista|operador|auxiliar|estagiario|aprendiz)\b", flags=re.IGNORECASE)

    # --- Agrupar nós por setor ---
    clusters = {}
    for setor in df["Setor"].dropna().unique():
        with dot.subgraph(name=f"cluster_{setor}") as c:
            c.attr(label=setor, style="rounded,dashed", color="blue", fontsize="14", fontname="Helvetica-Bold")
            clusters[setor] = c

    # --- Nós ---
    for _, row in df.iterrows():
        nome_formatado  = "\n".join(textwrap.wrap(str(row["Nome"]),  largura_max))
        cargo_formatado = "\n".join(textwrap.wrap(str(row["Cargo"]), largura_max))
        label = f"{nome_formatado}\n{cargo_formatado}"
        dot.node(str(row["Nome"]), label)

    # --- Preparar grupos operacionais por gestor ---
    ops_por_gestor = defaultdict(list)
    for _, row in df.iterrows():
        if row.get("Gestor") and isinstance(row["Cargo"], str) and re_operacional.search(row["Cargo"]):
            ops_por_gestor[str(row["Gestor"])].append(str(row["Nome"]))

    # --- Arestas ---
    for _, row in df.iterrows():
        if pd.notna(row["Gestor"]) and str(row["Gestor"]).strip() != "":
            if isinstance(row["Cargo"], str) and re_operacional.search(row["Cargo"]):
                dot.edge(str(row["Gestor"]), str(row["Nome"]), constraint="false")
            else:
                dot.edge(str(row["Gestor"]), str(row["Nome"]))

    # --- Forçar empilhamento vertical dos operacionais ---
    for gestor, nomes in ops_por_gestor.items():
        if not nomes:
            continue
        nomes = sorted(nomes, key=lambda x: x.lower())
        dot.edge(gestor, nomes[0], style="invis", weight="50")
        for a, b in zip(nomes, nomes[1:]):
            dot.edge(a, b, style="invis", weight="50")

    return dot

def gerar_download(dot, formato="svg"):
    filename = f"organograma.{formato}"
    dot.render(filename, format=formato, cleanup=True)
    with open(filename, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:file/{formato};base64,{b64}" download="{filename}">⬇️ Baixar {formato.upper()}</a>'
    return href

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, header=0)
    st.write("✅ Arquivo carregado com sucesso!")
    st.dataframe(df)

    # --- Filtros ---
    st.sidebar.header("🔎 Filtros")
    
    # Filtro por setor
    setores = ["Todos"] + sorted(df["Setor"].dropna().unique().tolist())
    setor_escolhido = st.sidebar.selectbox("Filtrar por Setor", setores)

    # Filtro por gestor
    gestores = ["Todos"] + sorted(df["Gestor"].dropna().unique().tolist())
    gestor_escolhido = st.sidebar.selectbox("Filtrar por Gestor", gestores)

    # Filtro por colaborador (busca)
    colaborador_busca = st.sidebar.text_input("🔍 Buscar colaborador (nome ou parte)")

    # --- Aplicação dos filtros ---
    df_filtrado = df.copy()
    if setor_escolhido != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Setor"] == setor_escolhido]
    if gestor_escolhido != "Todos":
        df_filtrado = df_filtrado[(df_filtrado["Gestor"] == gestor_escolhido) | (df_filtrado["Nome"] == gestor_escolhido)]
    if colaborador_busca.strip() != "":
        busca = colaborador_busca.lower()
        df_filtrado = df[df["Nome"].str.lower().str.contains(busca, na=False)]

    # --- Geração do organograma filtrado ---
    if not df_filtrado.empty:
        dot = criar_organograma(df_filtrado, largura_max=30)
        st.graphviz_chart(dot)

        # 🔽 Botões de download
        st.markdown("### 📥 Exportar Organograma")
        st.markdown(gerar_download(dot, "png"), unsafe_allow_html=True)
        st.markdown(gerar_download(dot, "svg"), unsafe_allow_html=True)
    else:
        st.warning("⚠️ Nenhum resultado encontrado para os filtros aplicados.")
