import streamlit as st
import pandas as pd
import textwrap
import re
from collections import defaultdict
from graphviz import Digraph

# --- Função original adaptada ---
def criar_organograma_excel(df, largura_max=20):
    colunas_esperadas = ["Nome", "Cargo", "Gestor", "Setor"]
    df = df[[c for c in df.columns if c in colunas_esperadas]]

    dot = Digraph(comment="Organograma", format="png")
    dot.attr(rankdir="TB", size="9", nodesep="0.3", ranksep="0.4")
    dot.attr("node", shape="box", style="rounded,filled", color="lightblue",
             fontname="Helvetica", fontsize="12", width="1.6", height="0.9", fixedsize="false")
    dot.attr(splines="ortho")

    re_operacional = re.compile(r"\b(analista|operador|auxiliar|estagiario|aprendiz)\b", flags=re.IGNORECASE)

    # --- Agrupar por setor ---
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

    # --- Operacionais agrupados ---
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

    # --- Empilhar operacionais ---
    for gestor, nomes in ops_por_gestor.items():
        nomes = sorted(nomes, key=lambda x: x.lower())
        dot.edge(gestor, nomes[0], style="invis", weight="50")
        for a, b in zip(nomes, nomes[1:]):
            dot.edge(a, b, style="invis", weight="50")

    return dot


# --- Streamlit App ---
st.set_page_config(page_title="Organograma Interativo", layout="wide")
st.title("📊 Organograma Interativo")

uploaded_file = st.file_uploader("Carregar arquivo Excel", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("📂 Pré-visualização dos dados")
    st.dataframe(df)

    dot = criar_organograma_excel(df, largura_max=30)

    st.subheader("📌 Organograma Gerado")
    st.graphviz_chart(dot.source)

    # Botão para download do SVG
    svg_bytes = dot.pipe(format="svg")
    st.download_button(
        label="⬇️ Baixar Organograma (SVG)",
        data=svg_bytes,
        file_name="organograma.svg",
        mime="image/svg+xml"
    )
