import streamlit as st
import pandas as pd
import json
import requests
import xml.etree.ElementTree as ET
import anthropic
import time
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="Hot Topics Dashboard", layout="wide")

# ── Chaves via Streamlit Secrets ──────────────────────────────
YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

st.title("🔥 Hot Topics — Painel de Tendências")
st.caption("Monitoramento automatizado de tópicos em alta nas redes sociais")

# ── Abas ──────────────────────────────────────────────────────
aba1, aba2 = st.tabs(["📋 Painel Geral", "🔍 Análise por Tema"])

# ════════════════════════════════════════════════════════════
# ABA 1 — PAINEL GERAL
# ════════════════════════════════════════════════════════════
with aba1:
    with open("pipeline_final.json", "r", encoding="utf-8") as f:
        dados = json.load(f)

    df = pd.DataFrame(dados)

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

    for _, row in df_filtrado.iterrows():
        emoji = {"P": "🌱", "M": "📈", "G": "🔥"}[row["classificacao"]]
        sentimento_emoji = {"POSITIVO": "😊", "NEGATIVO": "😟", "NEUTRO": "😐"}.get(row["sentimento_atual"], "😐")

        with st.expander(f"{emoji} [{row['classificacao']}] {row['titulo']} — {row['plataforma']}"):
            st.markdown(f"**Resumo:** {row['resumo']}")
            st.markdown(f"**Recomendacao:** {row['recomendacao_marca']}")
            st.markdown(f"**{sentimento_emoji} Sentimento:** {row['sentimento_atual']} -> {row['tendencia_sentimento']}")
            if row['crescimento_previsto_pct'] != "N/A":
                st.markdown(f"**Crescimento previsto (7 dias):** {row['crescimento_previsto_pct']}% (dados {row['fonte_dados_previsao']})")

# ════════════════════════════════════════════════════════════
# ABA 2 — ANÁLISE POR TEMA
# ════════════════════════════════════════════════════════════
with aba2:
    st.subheader("🔍 Análise Completa por Tema")
    st.caption("Digite um tema para gerar um Hot Topics segmentado completo.")

    tema = st.text_input("Digite o tema:", placeholder="Ex: inteligência artificial, black friday...")

    if st.button("🔍 Analisar tema") and tema:

        # ── Links de pesquisa ─────────────────────────────
        tema_url = tema.replace(" ", "+")
        links = {
            "YouTube": f"https://www.youtube.com/results?search_query={tema_url}",
            "Google": f"https://www.google.com/search?q={tema_url}",
            "TikTok": f"https://www.tiktok.com/search?q={tema_url}",
            "Instagram": f"https://www.instagram.com/explore/tags/{tema_url}/",
            "X/Twitter": f"https://x.com/search?q={tema_url}",
            "Reddit": f"https://www.reddit.com/search/?q={tema_url}"
        }

        with st.spinner("Coletando dados e gerando análise completa..."):

            dados_plataformas = {}

            # ── Google Trends ─────────────────────────────
            try:
                url = "https://trends.google.com/trending/rss?geo=BR"
                headers = {"User-Agent": "Mozilla/5.0"}
                resposta = requests.get(url, headers=headers)
                root = ET.fromstring(resposta.content)
                trends = [item.find("title").text for item in root.findall(".//item")]
                encontrado = any(tema.lower() in t.lower() for t in trends)
                dados_plataformas["Google Trends"] = {
                    "encontrado": encontrado,
                    "volume": 1 if encontrado else 0,
                    "detalhe": "Em alta no Google Trends agora" if encontrado else "Fora do top 10 do Google Trends hoje"
                }
            except:
                dados_plataformas["Google Trends"] = {"encontrado": False, "volume": 0, "detalhe": "Erro ao buscar"}

            # ── YouTube ───────────────────────────────────
            try:
                from googleapiclient.discovery import build
                youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
                resposta_yt = youtube.search().list(
                    part="snippet",
                    q=tema,
                    type="video",
                    order="viewCount",
                    regionCode="BR",
                    maxResults=10
                ).execute()
                videos = resposta_yt.get("items", [])
                dados_plataformas["YouTube"] = {
                    "encontrado": len(videos) > 0,
                    "volume": len(videos),
                    "detalhe": f"{len(videos)} vídeos encontrados",
                    "itens": [v["snippet"]["title"] for v in videos[:5]]
                }
            except Exception as e:
                dados_plataformas["YouTube"] = {"encontrado": False, "volume": 0, "detalhe": f"Erro: {e}"}

            # ── Classificação PMG ─────────────────────────
            volume_total = sum(d["volume"] for d in dados_plataformas.values())
            plataformas_ativas = sum(1 for d in dados_plataformas.values() if d["encontrado"])

            if plataformas_ativas >= 2 or volume_total >= 10:
                classificacao = "G"
                emoji_pmg = "🔥"
                classificacao_texto = "Mainstream"
            elif plataformas_ativas == 1 or volume_total >= 5:
                classificacao = "M"
                emoji_pmg = "📈"
                classificacao_texto = "Crescendo"
            else:
                classificacao = "P"
                emoji_pmg = "🌱"
                classificacao_texto = "Emergente"

            # ── IA: Resumo, Recomendação, Sentimento, Hashtags ──
            resumo_ia = recomendacao_ia = sentimento_ia = tendencia_ia = hashtags_ia = ""

            if client:
                try:
                    # Resumo
                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=250,
                        messages=[{"role": "user", "content": f"""Você é um analista de social listening. Gere um resumo sobre o tema "{tema}" nas redes sociais brasileiras. Máximo 3 frases em português."""}]
                    )
                    resumo_ia = resp.content[0].text
                    time.sleep(0.5)

                    # Recomendação
                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=250,
                        messages=[{"role": "user", "content": f"""Você é um estrategista de marketing. Para o tema "{tema}" classificado como {classificacao_texto}, recomende em até 3 frases se uma marca deve ENTRAR, OBSERVAR ou EVITAR, com justificativa e formato de conteúdo sugerido."""}]
                    )
                    recomendacao_ia = resp.content[0].text
                    time.sleep(0.5)

                    # Sentimento
                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=10,
                        messages=[{"role": "user", "content": f"""Analise o sentimento público sobre "{tema}". Responda APENAS: POSITIVO, NEGATIVO ou NEUTRO."""}]
                    )
                    sentimento_ia = resp.content[0].text.strip().upper()
                    if sentimento_ia not in ["POSITIVO", "NEGATIVO", "NEUTRO"]:
                        sentimento_ia = "NEUTRO"
                    time.sleep(0.5)

                    # Tendência
                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=10,
                        messages=[{"role": "user", "content": f"""Para o tema "{tema}" com sentimento {sentimento_ia}, preveja a tendência. Responda APENAS: MELHORANDO, PIORANDO ou ESTAVEL."""}]
                    )
                    tendencia_ia = resp.content[0].text.strip().upper()
                    if tendencia_ia not in ["MELHORANDO", "PIORANDO", "ESTAVEL"]:
                        tendencia_ia = "ESTAVEL"
                    time.sleep(0.5)

                    # Hashtags
                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=150,
                        messages=[{"role": "user", "content": f"""Liste 8 hashtags e termos-chave relacionados ao tema "{tema}" que seriam usados nas redes sociais brasileiras. Formato: #hashtag1, #hashtag2, termo1, termo2..."""}]
                    )
                    hashtags_ia = resp.content[0].text
                    time.sleep(0.5)

                except Exception as e:
                    resumo_ia = f"Erro IA: {e}"

            # ── Previsão de crescimento (Prophet) ─────────
            crescimento_pct = 0
            try:
                import pandas as pd
                from prophet import Prophet

                dias = 14
                datas = [datetime.now() - timedelta(days=i) for i in range(dias, 0, -1)]
                valor_base = max(volume_total * 1000, 100)
                valores = np.linspace(valor_base * 0.3, valor_base, dias)
                ruido = np.random.normal(0, valor_base * 0.05, dias)
                valores = np.maximum(valores + ruido, 0)

                df_prophet = pd.DataFrame({"ds": datas, "y": valores})
                modelo = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
                modelo.fit(df_prophet)
                futuro = modelo.make_future_dataframe(periods=7)
                previsao = modelo.predict(futuro)
                valor_previsto = previsao.iloc[-1]["yhat"]
                crescimento_pct = round(((valor_previsto - valor_base) / valor_base) * 100, 1)
            except:
                crescimento_pct = 0

        # ── EXIBIR RESULTADO ──────────────────────────────
        st.markdown("---")
        st.markdown(f"# {emoji_pmg} Hot Topics: **{tema}**")
        st.markdown(f"### Classificação: **{classificacao} — {classificacao_texto}**")
        st.markdown("---")

        # Bloco 1: Presença nas plataformas + Links
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📡 Presença nas Plataformas")
            for plataforma, dados in dados_plataformas.items():
                icone = "✅" if dados["encontrado"] else "❌"
                st.markdown(f"{icone} **{plataforma}:** {dados['detalhe']}")

            if "itens" in dados_plataformas.get("YouTube", {}):
                st.markdown("**Top vídeos encontrados:**")
                for v in dados_plataformas["YouTube"]["itens"]:
                    st.caption(f"• {v}")

        with col2:
            st.markdown("### 🔗 Pesquisar nas Plataformas")
            for plataforma, link in links.items():
                st.markdown(f"[🔍 Ver **{plataforma}**]({link})")

        st.markdown("---")

        # Bloco 2: Análise de IA
        col3, col4 = st.columns(2)

        with col3:
            st.markdown("### 📝 Resumo e Contexto")
            st.markdown(resumo_ia)

            st.markdown("### 🎯 Recomendação de Marca")
            st.markdown(recomendacao_ia)

        with col4:
            sentimento_emoji = {"POSITIVO": "😊", "NEGATIVO": "😟", "NEUTRO": "😐"}.get(sentimento_ia, "😐")
            tendencia_emoji = {"MELHORANDO": "📈", "PIORANDO": "📉", "ESTAVEL": "➡️"}.get(tendencia_ia, "➡️")

            st.markdown("### 😊 Sentimento e Tendência")
            st.markdown(f"**Sentimento atual:** {sentimento_emoji} {sentimento_ia}")
            st.markdown(f"**Tendência:** {tendencia_emoji} {tendencia_ia}")

            st.markdown("### 🔮 Previsão de Crescimento (7 dias)")
            seta = "📈" if crescimento_pct > 0 else "📉"
            st.markdown(f"{seta} **{crescimento_pct:+.1f}%** *(dados simulados)*")

            st.markdown("### 🏷️ Principais Termos e Hashtags")
            st.markdown(hashtags_ia)