import streamlit as st
import pandas as pd
from graphviz import Digraph

# ==============================
# TÍTULO
# ==============================
st.set_page_config(page_title="Organograma App", layout="wide")
st.title("📊 Organograma da Empresa")

# ==============================
# CARREGAR DADOS
# ==============================
# Caso queira permitir upload de Excel
uploaded_file = st.file_uploader("📂 Envie a planilha do organograma (Excel)", type=["xlsx", "csv"])

if uploaded_file is not None:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.subheader("📋 Estrutura carregada")
    st.dataframe(df)

    # ==============================
    # GERAR ORGANOGRAMA
    # ==============================
    dot = Digraph(comment="Organograma", format="png")
    dot.attr(rankdir="TB", size="10")

    # Criar os nós
    for _, row in df.iterrows():
        dot.node(row["Nome"], f'{row["Nome"]}\n{row["Cargo"]}')

    # Criar as relações de gestão
    for _, row in df.iterrows():
        if pd.notna(row["Gestor"]) and row["Gestor"] != "":
            dot.edge(row["Gestor"], row["Nome"])

    # Exibir no Streamlit
    st.subheader("🖼️ Visualização do Organograma")
    st.graphviz_chart(dot)

else:
    st.info("👉 Faça upload de um arquivo Excel ou CSV contendo as colunas: **Nome, Cargo, Gestor, Setor**")
