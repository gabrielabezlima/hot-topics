import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Hot Topics Dashboard", layout="wide")

st.title("🔥 Hot Topics — Painel de Tendências")
st.caption("Monitoramento automatizado de tópicos em alta nas redes sociais")

# ── Carregar dados ────────────────────────────────────────────
with open("pipeline_final.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

df = pd.DataFrame(dados)

# ── Resumo PMG ────────────────────────────────────────────────
total_p = len(df[df["classificacao"] == "P"])
total_m = len(df[df["classificacao"] == "M"])
total_g = len(df[df["classificacao"] == "G"])

st.success(f"✅ {len(df)} tópicos monitorados — dados atualizados.")
st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🌱 Emergentes (P)")
    st.markdown(f"## **{total_p}**")
    st.caption("tópicos identificados")
with col2:
    st.markdown("### 📈 Crescendo (M)")
    st.markdown(f"## **{total_m}**")
    st.caption("tópicos em crescimento")
with col3:
    st.markdown("### 🔥 Mainstream (G)")
    st.markdown(f"## **{total_g}**")
    st.caption("tópico consolidado")

st.markdown("---")

# ── Filtros ───────────────────────────────────────────────────
st.subheader("📋 Lista de Tópicos")

col_f1, col_f2 = st.columns(2)
with col_f1:
    filtro_pmg = st.selectbox("Filtrar por classificação:", ["Todos", "P - Emergente", "M - Crescendo", "G - Mainstream"])
with col_f2:
    filtro_plataforma = st.selectbox("Filtrar por plataforma:", ["Todas"] + sorted(df["plataforma"].unique().tolist()))

df_filtrado = df.copy()
if filtro_pmg != "Todos":
    df_filtrado = df_filtrado[df_filtrado["classificacao"] == filtro_pmg[0]]
if filtro_plataforma != "Todas":
    df_filtrado = df_filtrado[df_filtrado["plataforma"] == filtro_plataforma]

# ── Lista de tópicos ──────────────────────────────────────────
for _, row in df_filtrado.iterrows():
    emoji = {"P": "🌱", "M": "📈", "G": "🔥"}[row["classificacao"]]
    sentimento_emoji = {"POSITIVO": "😊", "NEGATIVO": "😟", "NEUTRO": "😐"}.get(row["sentimento_atual"], "😐")

    with st.expander(f"{emoji} [{row['classificacao']}] {row['titulo']} — {row['plataforma']}"):
        st.markdown(f"**📝 Resumo:** {row['resumo']}")
        st.markdown(f"**🎯 Recomendação:** {row['recomendacao_marca']}")
        st.markdown(f"**{sentimento_emoji} Sentimento:** {row['sentimento_atual']} → {row['tendencia_sentimento']}")
        if row['crescimento_previsto_pct'] != "N/A":
            st.markdown(f"**Crescimento previsto (7 dias):** {row['crescimento_previsto_pct']}% *(dados {row['fonte_dados_previsao']})*")