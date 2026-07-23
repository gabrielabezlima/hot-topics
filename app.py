import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import anthropic
import time
import numpy as np
from datetime import datetime, timezone, timedelta
import base64
from pathlib import Path

st.set_page_config(
    page_title="ADAGA — Inteligência de Tendências",
    page_icon="⚔️",
    layout="wide"
)

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
REDDIT_CLIENT_ID = st.secrets.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = st.secrets.get("REDDIT_CLIENT_SECRET", "")
META_ACCESS_TOKEN = st.secrets.get("META_ACCESS_TOKEN", "")
TWITTER_BEARER_TOKEN = st.secrets.get("TWITTER_BEARER_TOKEN", "")
TIKTOK_API_KEY = st.secrets.get("TIKTOK_API_KEY", "")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None
fuso_brasilia = timezone(timedelta(hours=-3))

def get_logo_base64():
    for nome in ["logocerto2.png", "logocerto.png", "assets/logocerto.png", "assets/logocerto2.png"]:
        try:
            logo_path = Path(nome)
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    return base64.b64encode(f.read()).decode()
        except:
            pass
    return None

logo_b64 = get_logo_base64()
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height:240px; margin-bottom:0.5rem;">' if logo_b64 else '<div class="adaga-wordmark">A<span>D</span>AGA</div>'

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

.stApp { background-color: #08090B; }
.stApp p, .stApp span, .stApp div, .stApp label, .stApp li { color: #F4F4F1; font-family: 'Inter', sans-serif; }
.stMarkdown, .stMarkdown p { color: #F4F4F1 !important; }

.adaga-header { border-bottom: 1px solid #B99A70; padding: 1.5rem 0; margin-bottom: 2rem; }
.adaga-wordmark { font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; letter-spacing: 0.4em; color: #F4F4F1; }
.adaga-wordmark span { color: #B99A70; }
.adaga-tagline { font-size: 0.8rem; letter-spacing: 0.15em; color: #F4F4F1; text-transform: uppercase; margin-top: 0.3rem; }

.metric-card { background: #17191D; border-radius: 8px; padding: 1.5rem; text-align: center; border: 1px solid #2A2D33; }
.metric-number { font-family: 'Space Grotesk', sans-serif; font-size: 3rem; font-weight: 700; color: #F4F4F1; line-height: 1; margin: 0.5rem 0; }
.metric-label { font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; color: #F4F4F1; }
.metric-p .metric-number { color: #6C9EFF; }
.metric-m .metric-number { color: #B99A70; }
.metric-g .metric-number { color: #F4F4F1; }

.rank-item { display: flex; align-items: flex-start; padding: 0.8rem 0; border-bottom: 1px solid #17191D; gap: 1rem; }
.rank-number { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; color: #F4F4F1; min-width: 2.5rem; }
.rank-number-gold { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; color: #B99A70; min-width: 2.5rem; }
.rank-title { font-size: 1rem; font-weight: 600; color: #F4F4F1; margin-bottom: 0.2rem; }
.rank-meta { font-size: 0.75rem; color: #F4F4F1; }

.badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.65rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; }
.badge-p { background: #0D1F3C; color: #6C9EFF !important; }
.badge-m { background: #2A1F0D; color: #B99A70 !important; }
.badge-g { background: #2A2D33; color: #F4F4F1 !important; }

.analise-card { background: #17191D; border: 1px solid #2A2D33; border-radius: 8px; padding: 1.2rem; margin: 0.5rem 0; }
.analise-card-gold { background: #17191D; border: 1px solid #B99A70; border-radius: 8px; padding: 1.2rem; margin: 0.5rem 0; }
.analise-label { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.2em; text-transform: uppercase; color: #B99A70; margin-bottom: 0.5rem; }
.analise-text { font-size: 0.9rem; color: #F4F4F1; line-height: 1.6; }

.section-title { font-family: 'Space Grotesk', sans-serif; font-size: 0.65rem; font-weight: 600; letter-spacing: 0.2em; text-transform: uppercase; color: #B99A70; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #2A2D33; }
.status-bar { background: #17191D; border: 1px solid #2A2D33; border-radius: 6px; padding: 0.6rem 1rem; font-size: 0.75rem; color: #F4F4F1; letter-spacing: 0.05em; margin-bottom: 1.5rem; }

.stTextInput > div > div > input { background: #F4F4F1 !important; border: 1px solid #B99A70 !important; color: #08090B !important; border-radius: 6px !important; font-family: 'Inter', sans-serif !important; }
.stTextInput > div > div > input::placeholder { color: #555A61 !important; }
.stSelectbox > div > div { background: #17191D !important; border: 1px solid #2A2D33 !important; color: #F4F4F1 !important; border-radius: 6px !important; }

.stButton > button { background: #B99A70 !important; color: #08090B !important; border: none !important; border-radius: 6px !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; letter-spacing: 0.05em !important; padding: 0.5rem 1.5rem !important; width: 100%; }
.stButton > button:hover { background: #C9AA80 !important; }

.stTabs [data-baseweb="tab-list"] { background: #08090B !important; border-bottom: 1px solid #2A2D33 !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #F4F4F1 !important; font-family: 'Space Grotesk', sans-serif !important; font-size: 0.75rem !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; padding: 0.8rem 1.2rem !important; }
.stTabs [aria-selected="true"] { color: #F4F4F1 !important; border-bottom: 2px solid #B99A70 !important; }

.streamlit-expanderHeader { background: #17191D !important; border: 1px solid #2A2D33 !important; color: #F4F4F1 !important; border-radius: 6px !important; }
hr { border-color: #2A2D33 !important; margin: 1.5rem 0 !important; }
.stSpinner > div { border-top-color: #B99A70 !important; }
.gold { color: #B99A70 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="adaga-header">
    {logo_html}
    <div class="adaga-tagline">⚔ &nbsp; A inteligência que corta o ruído e revela tendências</div>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# FUNÇÕES DE COLETA
# ════════════════════════════════════════════════════════════

def coletar_google_trends(regiao="BR", max_resultados=10):
    try:
        url = f"https://trends.google.com/trending/rss?geo={regiao}"
        resposta = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        root = ET.fromstring(resposta.content)
        topicos = []
        for item in root.findall(".//item")[:max_resultados]:
            titulo = item.find("title").text
            topicos.append({"titulo": titulo, "plataforma": "google_trends", "metrica_principal": 0, "metrica_secundaria": 0})
        return topicos
    except:
        return []

def coletar_youtube(api_key, regiao="BR", max_resultados=10):
    if not api_key:
        return []
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        resposta = youtube.videos().list(part="snippet,statistics", chart="mostPopular", regionCode=regiao, maxResults=max_resultados).execute()
        topicos = []
        for video in resposta["items"]:
            topicos.append({"titulo": video["snippet"]["title"], "plataforma": "youtube", "metrica_principal": int(video["statistics"].get("viewCount", 0)), "metrica_secundaria": int(video["statistics"].get("likeCount", 0))})
        return topicos
    except:
        return []

def coletar_reddit(client_id, client_secret, max_resultados=10):
    if not client_id or not client_secret:
        return []
    try:
        import praw
        reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent="ADAGA/1.0")
        subreddits = ["brasil", "investimentos", "futebol", "tecnologia"]
        topicos = []
        for sub in subreddits:
            for post in reddit.subreddit(sub).hot(limit=max_resultados // len(subreddits)):
                topicos.append({"titulo": post.title, "plataforma": "reddit", "metrica_principal": post.score, "metrica_secundaria": post.num_comments})
        return topicos
    except:
        return []

def coletar_meta(access_token, max_resultados=10):
    if not access_token:
        return []
    try:
        params = {"fields": "id,caption,like_count,comments_count", "limit": max_resultados, "access_token": access_token}
        resposta = requests.get("https://graph.facebook.com/v22.0/me/media", params=params, timeout=10).json()
        topicos = []
        for post in resposta.get("data", []):
            topicos.append({"titulo": post.get("caption", "")[:100], "plataforma": "instagram", "metrica_principal": post.get("like_count", 0), "metrica_secundaria": post.get("comments_count", 0)})
        return topicos
    except:
        return []

def coletar_twitter(bearer_token, max_resultados=10):
    if not bearer_token:
        return []
    try:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        resposta = requests.get("https://api.twitter.com/1.1/trends/place.json", headers=headers, params={"id": 455189}, timeout=10).json()
        topicos = []
        for trend in resposta[0]["trends"][:max_resultados]:
            topicos.append({"titulo": trend["name"], "plataforma": "twitter", "metrica_principal": trend.get("tweet_volume", 0) or 0, "metrica_secundaria": 0})
        return topicos
    except:
        return []

def coletar_tiktok(api_key, max_resultados=10):
    if not api_key:
        return []
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        resposta = requests.get("https://open.tiktokapis.com/v2/research/hashtag/query/", headers=headers, timeout=10).json()
        topicos = []
        for hashtag in resposta.get("data", {}).get("hashtags", [])[:max_resultados]:
            topicos.append({"titulo": f"#{hashtag.get('hashtag_name', '')}", "plataforma": "tiktok", "metrica_principal": hashtag.get("view_count", 0), "metrica_secundaria": hashtag.get("video_count", 0)})
        return topicos
    except:
        return []

def classificar_pmg(topico):
    plataforma = topico["plataforma"]
    metrica = topico["metrica_principal"]
    if plataforma == "google_trends": return "P"
    elif plataforma == "youtube":
        if metrica >= 5_000_000: return "G"
        elif metrica >= 500_000: return "M"
        else: return "P"
    elif plataforma == "reddit":
        if metrica >= 10_000: return "G"
        elif metrica >= 1_000: return "M"
        else: return "P"
    elif plataforma in ["instagram", "facebook"]:
        if metrica >= 100_000: return "G"
        elif metrica >= 10_000: return "M"
        else: return "P"
    elif plataforma == "twitter":
        if metrica >= 100_000: return "G"
        elif metrica >= 10_000: return "M"
        else: return "P"
    elif plataforma == "tiktok":
        if metrica >= 10_000_000: return "G"
        elif metrica >= 1_000_000: return "M"
        else: return "P"
    return "P"

def buscar_contexto_google_news(titulo):
    try:
        query = titulo.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        resposta = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        root = ET.fromstring(resposta.content)
        noticias = []
        for item in root.findall(".//item")[:5]:
            t = item.find("title")
            if t is not None:
                noticias.append(t.text)
        return noticias
    except:
        return []

def gerar_analise_ia(topico):
    if not client:
        return None
    try:
        classificacao_texto = {"P": "emergente", "M": "crescendo", "G": "mainstream"}[topico["classificacao"]]
        plataforma = topico["plataforma"]
        titulo = topico["titulo"]
        metrica = topico.get("metrica_principal", 0)
        noticias = buscar_contexto_google_news(titulo)
        contexto_noticias = "\n".join([f"- {n}" for n in noticias]) if noticias else "Nenhuma notícia encontrada."
        if plataforma == "youtube":
            contexto_plataforma = f"Em alta no YouTube com {metrica:,} visualizações."
        elif plataforma == "google_trends":
            contexto_plataforma = "Entre os mais buscados no Google Trends Brasil agora."
        else:
            contexto_plataforma = f"Em alta na plataforma {plataforma}."

        resp_resumo = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=600,
            messages=[{"role": "user", "content": f"""Analista sênior de social listening. Tópico: "{titulo}" | {classificacao_texto} | {contexto_plataforma}
Notícias: {contexto_noticias}

3 blocos:
CONTEXTO: [2 frases completas sobre o que está acontecendo]
PÚBLICO: [2 frases completas sobre o perfil do público]
SENTIMENTO: [POSITIVO/NEGATIVO/NEUTRO] — [1 frase sobre o tom]"""}]
        )
        time.sleep(0.3)

        resp_rec = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            messages=[{"role": "user", "content": f"""Estrategista de marketing. Tópico: "{titulo}" | {classificacao_texto} | {plataforma}
Notícias: {contexto_noticias}

3 blocos:
DECISÃO: ENTRAR/OBSERVAR/EVITAR — [justificativa]
OPORTUNIDADE: [risco ou oportunidade específica]
FORMATO: [formato, plataforma e timing]"""}]
        )
        return {"resumo": resp_resumo.content[0].text, "recomendacao": resp_rec.content[0].text, "classificacao": topico["classificacao"]}
    except Exception as e:
        return {"erro": str(e)}

# ════════════════════════════════════════════════════════════
# PIPELINE
# ════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def rodar_pipeline():
    todos = []
    todos += coletar_google_trends()
    todos += coletar_youtube(YOUTUBE_API_KEY)
    todos += coletar_reddit(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
    todos += coletar_meta(META_ACCESS_TOKEN)
    todos += coletar_twitter(TWITTER_BEARER_TOKEN)
    todos += coletar_tiktok(TIKTOK_API_KEY)
    for t in todos:
        t["classificacao"] = classificar_pmg(t)
    return todos

# ════════════════════════════════════════════════════════════
# INTERFACE
# ════════════════════════════════════════════════════════════

aba1, aba2, aba3, aba4 = st.tabs(["⚡ RADAR GERAL", "🔍 ANÁLISE POR TEMA", "🎯 TERRITÓRIO", "🏷️ CATEGORIA"])

# ── ABA 1 ──────────────────────────────────────────────────
with aba1:
    with st.spinner("Captando sinais..."):
        dados = rodar_pipeline()

    hora_atualizacao = datetime.now(fuso_brasilia).strftime("%d/%m/%Y às %H:%M")
    st.markdown(f'<div class="status-bar">● MONITORAMENTO ATIVO &nbsp;·&nbsp; {len(dados)} SINAIS CAPTADOS &nbsp;·&nbsp; {hora_atualizacao} &nbsp;·&nbsp; RENOVA A CADA 1H</div>', unsafe_allow_html=True)

    df = pd.DataFrame(dados)
    if not df.empty:
        total_p = len(df[df["classificacao"] == "P"])
        total_m = len(df[df["classificacao"] == "M"])
        total_g = len(df[df["classificacao"] == "G"])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<div class="metric-card metric-p"><div class="metric-label">▲ EMERGENTES</div><div class="metric-number">{total_p}</div><div class="metric-label">sinais identificados</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card metric-m"><div class="metric-label">◆ CRESCENDO</div><div class="metric-number">{total_m}</div><div class="metric-label">em aceleração</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card metric-g"><div class="metric-label">● MAINSTREAM</div><div class="metric-number">{total_g}</div><div class="metric-label">consolidado</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">⚡ Sinais em tempo real</div>', unsafe_allow_html=True)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_pmg = st.selectbox("Classificação", ["Todos", "P — Emergente", "M — Crescendo", "G — Mainstream"])
        with col_f2:
            filtro_plataforma = st.selectbox("Plataforma", ["Todas"] + sorted(df["plataforma"].unique().tolist()))

        df_filtrado = df.copy()
        if filtro_pmg != "Todos":
            df_filtrado = df_filtrado[df_filtrado["classificacao"] == filtro_pmg[0]]
        if filtro_plataforma != "Todas":
            df_filtrado = df_filtrado[df_filtrado["plataforma"] == filtro_plataforma]

        if "analises" not in st.session_state:
            st.session_state.analises = {}

        label_map = {"P": "EMERGENTE", "M": "CRESCENDO", "G": "MAINSTREAM"}
        plataforma_icon = {"google_trends": "🔍", "youtube": "▶", "reddit": "◎", "instagram": "◈", "twitter": "◉", "tiktok": "◐"}

        for idx, row in df_filtrado.iterrows():
            classificacao = row["classificacao"]
            badge_class = f"badge-{classificacao.lower()}"
            num_class = "rank-number-gold" if idx < 3 else "rank-number"
            icon = plataforma_icon.get(row["plataforma"], "•")
            metrica_txt = f" · {row['metrica_principal']:,} views" if row["metrica_principal"] > 0 and row["plataforma"] == "youtube" else ""

            st.markdown(f"""
            <div class="rank-item">
                <div class="{num_class}">{idx+1:02d}</div>
                <div style="flex:1">
                    <div class="rank-title">{row['titulo']}</div>
                    <div class="rank-meta">{icon} {row['plataforma'].upper()}{metrica_txt} &nbsp;<span class="badge {badge_class}">{label_map[classificacao]}</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            chave = f"ia_{idx}"
            if chave in st.session_state.analises:
                analise = st.session_state.analises[chave]
                if "erro" not in analise:
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f'<div class="analise-card"><div class="analise-label">Análise</div><div class="analise-text">{analise["resumo"]}</div></div>', unsafe_allow_html=True)
                    with col_b:
                        st.markdown(f'<div class="analise-card-gold"><div class="analise-label">Recomendação</div><div class="analise-text">{analise["recomendacao"]}</div></div>', unsafe_allow_html=True)
                else:
                    st.error(f"Erro: {analise['erro']}")
            else:
                if st.button("⚔ Analisar", key=chave):
                    with st.spinner("Processando sinal..."):
                        analise = gerar_analise_ia(row.to_dict())
                        if analise:
                            st.session_state.analises[chave] = analise
                            st.rerun()
    else:
        st.markdown('<div class="analise-card">Nenhum sinal captado. Verifique as chaves de API.</div>', unsafe_allow_html=True)

# ── ABA 2 ──────────────────────────────────────────────────
with aba2:
    st.markdown('<div class="section-title">🔍 Análise por Tema</div>', unsafe_allow_html=True)
    st.markdown('<p>Digite um tema para gerar inteligência completa sobre ele agora.</p>', unsafe_allow_html=True)
    tema = st.text_input("", placeholder="Ex: inteligência artificial, black friday...", key="tema_input")

    if st.button("⚔ Analisar tema", key="btn_tema") and tema:
        tema_url = tema.replace(" ", "+")
        links = {
            "YouTube": f"https://www.youtube.com/results?search_query={tema_url}",
            "Google": f"https://www.google.com/search?q={tema_url}",
            "TikTok": f"https://www.tiktok.com/search?q={tema_url}",
            "Instagram": f"https://www.instagram.com/explore/tags/{tema_url}/",
            "X/Twitter": f"https://x.com/search?q={tema_url}",
            "Reddit": f"https://www.reddit.com/search/?q={tema_url}"
        }

        with st.spinner("Captando sinais..."):
            dados_plataformas = {}

            try:
                url = "https://trends.google.com/trending/rss?geo=BR"
                resposta = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                root = ET.fromstring(resposta.content)
                trends = [item.find("title").text for item in root.findall(".//item")]
                encontrado = any(tema.lower() in t.lower() for t in trends)
                dados_plataformas["Google Trends"] = {"encontrado": encontrado, "volume": 1 if encontrado else 0, "detalhe": "Em alta agora" if encontrado else "Fora do top 10"}
            except:
                dados_plataformas["Google Trends"] = {"encontrado": False, "volume": 0, "detalhe": "Erro"}

            try:
                from googleapiclient.discovery import build
                youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
                resposta_yt = youtube.search().list(part="snippet", q=tema, type="video", order="viewCount", regionCode="BR", maxResults=10).execute()
                videos = resposta_yt.get("items", [])
                dados_plataformas["YouTube"] = {"encontrado": len(videos) > 0, "volume": len(videos), "detalhe": f"{len(videos)} vídeos encontrados", "itens": [v["snippet"]["title"] for v in videos[:5]]}
            except Exception as e:
                dados_plataformas["YouTube"] = {"encontrado": False, "volume": 0, "detalhe": f"Erro: {e}"}

            volume_total = sum(d["volume"] for d in dados_plataformas.values())
            plataformas_ativas = sum(1 for d in dados_plataformas.values() if d["encontrado"])

            classificacao = "P"
            if client:
                try:
                    hoje = datetime.now(fuso_brasilia).strftime("%d/%m/%Y")
                    resp_pmg = client.messages.create(model="claude-sonnet-4-6", max_tokens=50, messages=[{"role": "user", "content": f'Classifique "{tema}" considerando: data {hoje}, plataformas {plataformas_ativas}, volume {volume_total}. Responda APENAS: P, M ou G.'}])
                    classificacao = resp_pmg.content[0].text.strip().upper()
                    if classificacao not in ["P", "M", "G"]:
                        classificacao = "M" if plataformas_ativas >= 1 else "P"
                except:
                    classificacao = "G" if plataformas_ativas >= 2 else "M" if plataformas_ativas == 1 else "P"

            classificacao_mapa = {"P": ("▲", "EMERGENTE", "#6C9EFF"), "M": ("◆", "CRESCENDO", "#B99A70"), "G": ("●", "MAINSTREAM", "#F4F4F1")}
            simbolo_pmg, label_pmg, cor_pmg = classificacao_mapa[classificacao]

            resumo_ia = recomendacao_ia = sentimento_ia = tendencia_ia = hashtags_ia = ""
            if client:
                try:
                    noticias_tema = buscar_contexto_google_news(tema)
                    contexto_noticias_tema = "\n".join([f"- {n}" for n in noticias_tema]) if noticias_tema else "Nenhuma notícia."
                    contexto_youtube = ""
                    if dados_plataformas.get("YouTube", {}).get("itens"):
                        videos_str = "\n".join([f"- {v}" for v in dados_plataformas["YouTube"]["itens"]])
                        contexto_youtube = f"\nVídeos em alta:\n{videos_str}"

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=1500, messages=[{"role": "user", "content": f"""Analista sênior de social listening. Tema: "{tema}" ({label_pmg}).
Notícias: {contexto_noticias_tema}{contexto_youtube}

3 parágrafos completos:
1. O que está acontecendo de fato agora
2. Por que está ganhando atenção neste momento
3. Perfil completo do público: faixa etária, interesses, comportamento, plataformas

Sem cortar."""}])
                    resumo_ia = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=1200, messages=[{"role": "user", "content": f"""Estrategista de marketing. Tema: "{tema}" ({label_pmg}).
Notícias: {contexto_noticias_tema}

3 parágrafos completos:
1. ENTRAR/OBSERVAR/EVITAR com justificativa completa
2. Risco ou oportunidade específica detalhada
3. Formato, plataforma e timing ideais

Sem cortar."""}])
                    recomendacao_ia = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=10, messages=[{"role": "user", "content": f'Sentimento sobre "{tema}". APENAS: POSITIVO, NEGATIVO ou NEUTRO.'}])
                    sentimento_ia = resp.content[0].text.strip().upper()
                    if sentimento_ia not in ["POSITIVO", "NEGATIVO", "NEUTRO"]: sentimento_ia = "NEUTRO"
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=10, messages=[{"role": "user", "content": f'Tendência para "{tema}" sentimento {sentimento_ia}. APENAS: MELHORANDO, PIORANDO ou ESTAVEL.'}])
                    tendencia_ia = resp.content[0].text.strip().upper()
                    if tendencia_ia not in ["MELHORANDO", "PIORANDO", "ESTAVEL"]: tendencia_ia = "ESTAVEL"
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=200, messages=[{"role": "user", "content": f'8 hashtags e termos sobre "{tema}" para redes sociais brasileiras. Formato: #hashtag1, #hashtag2, termo1...'}])
                    hashtags_ia = resp.content[0].text
                except Exception as e:
                    resumo_ia = f"Erro: {e}"

            crescimento_pct = round(np.random.uniform(20, 60), 1) if plataformas_ativas > 0 else 0

        st.markdown("---")
        st.markdown(f"""
        <div style="margin-bottom:1.5rem;">
            <div style="font-family:'Space Grotesk'; font-size:1.8rem; font-weight:700; color:{cor_pmg};">{simbolo_pmg} {tema.upper()}</div>
            <div style="font-size:0.75rem; letter-spacing:0.15em; color:#F4F4F1; text-transform:uppercase;">{label_pmg} &nbsp;·&nbsp; {plataformas_ativas} PLATAFORMAS ATIVAS</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="section-title">📡 Presença nas plataformas</div>', unsafe_allow_html=True)
            for plataforma, d in dados_plataformas.items():
                cor = "#B99A70" if d["encontrado"] else "#F4F4F1"
                icone = "▪" if d["encontrado"] else "▫"
                st.markdown(f'<p style="color:{cor}; margin:0.3rem 0;">{icone} <b>{plataforma}</b> — {d["detalhe"]}</p>', unsafe_allow_html=True)
            if "itens" in dados_plataformas.get("YouTube", {}):
                st.markdown('<div class="section-title" style="margin-top:1rem;">Top vídeos</div>', unsafe_allow_html=True)
                for v in dados_plataformas["YouTube"]["itens"]:
                    st.markdown(f'<p style="margin:0.2rem 0; color:#F4F4F1;">▸ {v}</p>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="section-title">🔗 Pesquisar nas plataformas</div>', unsafe_allow_html=True)
            for plataforma, link in links.items():
                st.markdown(f'<a href="{link}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.4rem 0;">⚔ {plataforma}</a>', unsafe_allow_html=True)

        st.markdown("---")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown(f'<div class="analise-card"><div class="analise-label">Contexto e análise</div><div class="analise-text">{resumo_ia}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="analise-card-gold" style="margin-top:1rem;"><div class="analise-label">Recomendação de marca</div><div class="analise-text">{recomendacao_ia}</div></div>', unsafe_allow_html=True)
        with col4:
            sent_cor = {"POSITIVO": "#4CAF50", "NEGATIVO": "#F44336", "NEUTRO": "#B99A70"}.get(sentimento_ia, "#B99A70")
            tend_icon = {"MELHORANDO": "▲", "PIORANDO": "▼", "ESTAVEL": "◆"}.get(tendencia_ia, "◆")
            seta = "▲" if crescimento_pct > 0 else "▼"
            st.markdown(f"""
            <div class="analise-card" style="margin-bottom:1rem;">
                <div class="analise-label">Sentimento</div>
                <div style="font-family:'Space Grotesk'; font-size:1.3rem; color:{sent_cor}; font-weight:700;">{sentimento_ia}</div>
                <div style="font-size:0.8rem; color:#F4F4F1; margin-top:0.3rem;">{tend_icon} Tendência: {tendencia_ia}</div>
            </div>
            <div class="analise-card" style="margin-bottom:1rem;">
                <div class="analise-label">Previsão 7 dias</div>
                <div style="font-family:'Space Grotesk'; font-size:2rem; color:#B99A70; font-weight:700;">{seta} {crescimento_pct:+.1f}%</div>
                <div style="font-size:0.75rem; color:#F4F4F1;">dados simulados</div>
            </div>
            <div class="analise-card">
                <div class="analise-label">Hashtags e termos</div>
                <div class="analise-text">{hashtags_ia}</div>
            </div>
            """, unsafe_allow_html=True)

# ── ABA 3 ──────────────────────────────────────────────────
with aba3:
    st.markdown('<div class="section-title">🎯 Território de Marca</div>', unsafe_allow_html=True)
    st.markdown('<p>Digite o território para mapear o que está em alta dentro dele agora.</p>', unsafe_allow_html=True)
    territorio = st.text_input("", placeholder="Ex: Futebol, Beleza, Tecnologia...", key="territorio_input")

    if st.button("⚔ Analisar território", key="btn_territorio") and territorio:
        territorio_url = territorio.replace(" ", "+")

        with st.spinner("Mapeando território..."):
            topicos_territorio = []
            try:
                from googleapiclient.discovery import build
                youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
                resposta_yt = youtube.search().list(part="snippet", q=territorio, type="video", order="viewCount", regionCode="BR", maxResults=10).execute()
                for v in resposta_yt.get("items", []):
                    topicos_territorio.append({"titulo": v["snippet"]["title"], "canal": v["snippet"]["channelTitle"], "plataforma": "YouTube"})
            except:
                pass

            topicos_painel_relacionados = []
            if client and dados:
                try:
                    titulos_painel = [t["titulo"] for t in dados[:20]]
                    lista_titulos = "\n".join([f"- {t}" for t in titulos_painel])
                    resp_filtro = client.messages.create(model="claude-sonnet-4-6", max_tokens=500, messages=[{"role": "user", "content": f'Território: "{territorio}". Tópicos: {lista_titulos}. Quais têm relação? APENAS os títulos, um por linha. Se nenhum: NENHUM'}])
                    resultado = resp_filtro.content[0].text.strip()
                    if resultado != "NENHUM":
                        topicos_painel_relacionados = [t.strip() for t in resultado.split("\n") if t.strip()]
                except:
                    pass

            analise_territorio = oportunidade_territorio = ""
            temas_recomendados = []
            if client:
                try:
                    noticias_territorio = buscar_contexto_google_news(territorio)
                    contexto_noticias = "\n".join([f"- {n}" for n in noticias_territorio]) if noticias_territorio else "Nenhuma notícia."
                    top_videos_str = "\n".join([f"- {t['titulo']} ({t['canal']})" for t in topicos_territorio[:5]])

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=1500, messages=[{"role": "user", "content": f"""Analista sênior. Território: "{territorio}".
Vídeos: {top_videos_str}
Notícias: {contexto_noticias}

4 parágrafos completos:
1. O que está acontecendo agora
2. Subtema dominante com detalhe completo
3. Perfil completo do público
4. Momento: aquecendo/pico/esfriando com justificativa

Sem cortar."""}])
                    analise_territorio = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=1000, messages=[{"role": "user", "content": f"""Estrategista. Território: "{territorio}".
Vídeos: {top_videos_str}. Notícias: {contexto_noticias}.

3 parágrafos completos:
1. Maior oportunidade de marca
2. Formato e plataforma ideais
3. O que evitar

Sem cortar."""}])
                    oportunidade_territorio = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=300, messages=[{"role": "user", "content": f'Território: "{territorio}". 8 subtemas em alta agora. Emoji + subtema, um por linha.'}])
                    temas_recomendados = [t.strip() for t in resp.content[0].text.strip().split("\n") if t.strip()]
                except:
                    pass

        st.markdown("---")
        st.markdown(f"""
        <div style="margin-bottom:1.5rem;">
            <div style="font-family:'Space Grotesk'; font-size:1.8rem; font-weight:700; color:#B99A70;">🎯 {territorio.upper()}</div>
            <div style="font-size:0.75rem; letter-spacing:0.15em; color:#F4F4F1; text-transform:uppercase;">TERRITÓRIO &nbsp;·&nbsp; {len(topicos_territorio)} SINAIS</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="analise-card"><div class="analise-label">O que está acontecendo</div><div class="analise-text">{analise_territorio or "Não foi possível gerar análise."}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="analise-card-gold"><div class="analise-label">Oportunidade para marcas</div><div class="analise-text">{oportunidade_territorio or "Não foi possível gerar oportunidade."}</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-title">🔥 Top conteúdos</div>', unsafe_allow_html=True)
        for i, t in enumerate(topicos_territorio[:10], 1):
            num_class = "rank-number-gold" if i <= 3 else "rank-number"
            st.markdown(f'<div class="rank-item"><div class="{num_class}">{i:02d}</div><div><div class="rank-title">{t["titulo"]}</div><div class="rank-meta">▶ {t["canal"]}</div></div></div>', unsafe_allow_html=True)

        if topicos_painel_relacionados:
            st.markdown("---")
            st.markdown('<div class="section-title">🔗 Tópicos do radar relacionados</div>', unsafe_allow_html=True)
            label_map_local = {"P": "EMERGENTE", "M": "CRESCENDO", "G": "MAINSTREAM"}
            for t in topicos_painel_relacionados:
                topico_completo = next((x for x in dados if x["titulo"] == t), None)
                if topico_completo:
                    c = topico_completo["classificacao"]
                    st.markdown(f'<p style="margin:0.4rem 0;"><span class="badge badge-{c.lower()}">{label_map_local[c]}</span> &nbsp; {t}</p>', unsafe_allow_html=True)

        if temas_recomendados:
            st.markdown("---")
            st.markdown('<div class="section-title">📋 Temas para monitorar</div>', unsafe_allow_html=True)
            col3, col4 = st.columns(2)
            metade = len(temas_recomendados) // 2
            with col3:
                for t in temas_recomendados[:metade]:
                    st.markdown(f'<p style="margin:0.3rem 0; color:#F4F4F1;">▸ {t}</p>', unsafe_allow_html=True)
            with col4:
                for t in temas_recomendados[metade:]:
                    st.markdown(f'<p style="margin:0.3rem 0; color:#F4F4F1;">▸ {t}</p>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-title">🔗 Pesquisar</div>', unsafe_allow_html=True)
        col5, col6, col7 = st.columns(3)
        with col5:
            st.markdown(f'<a href="https://www.youtube.com/results?search_query={territorio_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">▶ YouTube</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.google.com/search?q={territorio_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">🔍 Google</a>', unsafe_allow_html=True)
        with col6:
            st.markdown(f'<a href="https://www.tiktok.com/search?q={territorio_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">◐ TikTok</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.instagram.com/explore/tags/{territorio_url}/" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">◈ Instagram</a>', unsafe_allow_html=True)
        with col7:
            st.markdown(f'<a href="https://x.com/search?q={territorio_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">◉ X/Twitter</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.reddit.com/search/?q={territorio_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">◎ Reddit</a>', unsafe_allow_html=True)

# ── ABA 4 ──────────────────────────────────────────────────
with aba4:
    st.markdown('<div class="section-title">🏷️ Radar de Categoria</div>', unsafe_allow_html=True)
    st.markdown('<p>Digite uma categoria ou indústria para mapear produtos, marcas e particularidades em destaque agora.</p>', unsafe_allow_html=True)
    categoria = st.text_input("", placeholder="Ex: Cerveja, Smartphones, Cosméticos, Carros...", key="categoria_input")

    if st.button("⚔ Analisar categoria", key="btn_categoria") and categoria:
        categoria_url = categoria.replace(" ", "+")

        with st.spinner("Mapeando categoria..."):
            videos_categoria = []
            try:
                from googleapiclient.discovery import build
                youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
                resposta_yt = youtube.search().list(part="snippet", q=categoria, type="video", order="viewCount", regionCode="BR", maxResults=15).execute()
                for v in resposta_yt.get("items", []):
                    videos_categoria.append({"titulo": v["snippet"]["title"], "canal": v["snippet"]["channelTitle"]})
            except:
                pass

            noticias_categoria = buscar_contexto_google_news(categoria)
            noticias_marcas1 = buscar_contexto_google_news(f"{categoria} marca lançamento")
            noticias_marcas2 = buscar_contexto_google_news(f"{categoria} campanha publicidade")
            noticias_marcas3 = buscar_contexto_google_news(f"melhores marcas {categoria} 2025")

            contexto_noticias_cat = "\n".join([f"- {n}" for n in noticias_categoria]) if noticias_categoria else "Nenhuma notícia."
            contexto_videos_cat = "\n".join([f"- {v['titulo']} (canal: {v['canal']})" for v in videos_categoria[:10]]) if videos_categoria else "Nenhum vídeo."
            todas_noticias_marcas = noticias_marcas1 + noticias_marcas2 + noticias_marcas3
            contexto_noticias_marcas = "\n".join([f"- {n}" for n in todas_noticias_marcas]) if todas_noticias_marcas else "Nenhuma notícia de marcas."

            analise_categoria = marcas_destaque = oportunidade_categoria = produtos_destaque = ""
            temas_categoria = []

            if client:
                try:
                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=1500, messages=[{"role": "user", "content": f"""Analista sênior. Categoria: "{categoria}".
Vídeos: {contexto_videos_cat}
Notícias: {contexto_noticias_cat}

4 parágrafos completos:
1. O que está acontecendo agora
2. Produto ou segmento dominando — detalhe completo
3. Perfil completo do consumidor
4. Momento: aquecendo/pico/esfriando com justificativa

Sem cortar."""}])
                    analise_categoria = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=700, messages=[{"role": "user", "content": f"""Analista de produto. Categoria: "{categoria}".
Vídeos: {contexto_videos_cat}
Notícias: {contexto_noticias_cat}

2 blocos completos:
PRODUTOS EM DESTAQUE:
- Nome — motivo completo

INGREDIENTES / COMPONENTES / PARTICULARIDADES:
- Atributo — por que está sendo valorizado

Sem cortar."""}])
                    produtos_destaque = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=800, messages=[{"role": "user", "content": f"""Analista de inteligência de mercado. Categoria: "{categoria}".

VÍDEOS: {contexto_videos_cat}
NOTÍCIAS: {contexto_noticias_cat}
NOTÍCIAS DE MARCAS: {contexto_noticias_marcas}

Para cada marca encontrada, escreva EXATAMENTE:
[NOME DA MARCA] | [O que está acontecendo] | [Onde aparece] | [POSITIVO ou NEGATIVO ou NEUTRO] | [O que concorrentes podem fazer]

Exemplo:
Brahma | Lançou campanha com Neymar | YouTube e TV | POSITIVO | Concorrentes podem reagir com ativações em bares

Use apenas marcas dos dados. Se não houver, liste as principais com nota: sem dados concretos."""}])
                    marcas_destaque = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=1000, messages=[{"role": "user", "content": f"""Estrategista. Categoria: "{categoria}".
Vídeos: {contexto_videos_cat}. Notícias: {contexto_noticias_cat}.

3 parágrafos completos:
1. Maior oportunidade agora
2. Formato e plataforma ideais
3. O que evitar

Sem cortar."""}])
                    oportunidade_categoria = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=300, messages=[{"role": "user", "content": f'Categoria: "{categoria}". 8 temas em alta agora. Emoji + tema, um por linha.'}])
                    temas_categoria = [t.strip() for t in resp.content[0].text.strip().split("\n") if t.strip()]

                except Exception as e:
                    analise_categoria = f"Erro: {e}"

        st.markdown("---")
        st.markdown(f"""
        <div style="margin-bottom:1.5rem;">
            <div style="font-family:'Space Grotesk'; font-size:1.8rem; font-weight:700; color:#B99A70;">🏷️ {categoria.upper()}</div>
            <div style="font-size:0.75rem; letter-spacing:0.15em; color:#F4F4F1; text-transform:uppercase;">RADAR DE CATEGORIA &nbsp;·&nbsp; {len(videos_categoria)} SINAIS</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="analise-card"><div class="analise-label">O que está acontecendo</div><div class="analise-text">{analise_categoria or "Não foi possível gerar análise."}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="analise-card-gold"><div class="analise-label">Oportunidade para marcas</div><div class="analise-text">{oportunidade_categoria or "Não foi possível gerar oportunidade."}</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f'<div class="analise-card" style="border-color:#6C9EFF;"><div class="analise-label" style="color:#6C9EFF;">Produtos, ingredientes e particularidades</div><div class="analise-text">{produtos_destaque or "Não foi possível identificar."}</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-title">🏆 Marcas em destaque</div>', unsafe_allow_html=True)
        if marcas_destaque:
            linhas = [l.strip() for l in marcas_destaque.split("\n") if l.strip() and "|" in l]
            if linhas:
                for i, linha in enumerate(linhas):
                    partes = [p.strip() for p in linha.split("|")]
                    if len(partes) >= 5:
                        nome_marca = partes[0].strip("[]")
                        acontecendo = partes[1]
                        onde = partes[2]
                        sentimento = partes[3]
                        recomendacao = partes[4]
                        sent_cor = {"POSITIVO": "#4CAF50", "NEGATIVO": "#F44336", "NEUTRO": "#B99A70"}.get(sentimento.strip().upper(), "#B99A70")
                        st.markdown(f"""
                        <div class="analise-card" style="margin-bottom:1rem; border-left: 3px solid #B99A70;">
                            <div style="font-family:'Space Grotesk'; font-weight:700; font-size:1rem; color:#F4F4F1; margin-bottom:0.5rem;">🏷️ {nome_marca}</div>
                            <div style="font-size:0.8rem; color:#B99A70; margin-bottom:0.8rem;">{sentimento.strip()} &nbsp;·&nbsp; {onde}</div>
                            <p style="margin:0.3rem 0; color:#F4F4F1;"><b>O que está acontecendo:</b> {acontecendo}</p>
                            <p style="margin:0.3rem 0; color:#F4F4F1;"><b>Para concorrentes:</b> {recomendacao}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.markdown(f'<p style="margin:0.5rem 0; color:#F4F4F1;">▸ <b>{partes[0]}</b> — {partes[1]}</p>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="analise-text">{marcas_destaque}</div>', unsafe_allow_html=True)
        else:
            st.info("Nenhuma marca identificada.")

        st.markdown("---")
        st.markdown('<div class="section-title">🎬 Top conteúdos</div>', unsafe_allow_html=True)
        for i, v in enumerate(videos_categoria[:10], 1):
            num_class = "rank-number-gold" if i <= 3 else "rank-number"
            st.markdown(f'<div class="rank-item"><div class="{num_class}">{i:02d}</div><div><div class="rank-title">{v["titulo"]}</div><div class="rank-meta">▶ {v["canal"]}</div></div></div>', unsafe_allow_html=True)

        if temas_categoria:
            st.markdown("---")
            st.markdown('<div class="section-title">📋 Temas em alta</div>', unsafe_allow_html=True)
            col3, col4 = st.columns(2)
            metade = len(temas_categoria) // 2
            with col3:
                for t in temas_categoria[:metade]:
                    st.markdown(f'<p style="margin:0.3rem 0; color:#F4F4F1;">▸ {t}</p>', unsafe_allow_html=True)
            with col4:
                for t in temas_categoria[metade:]:
                    st.markdown(f'<p style="margin:0.3rem 0; color:#F4F4F1;">▸ {t}</p>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="section-title">🔗 Pesquisar</div>', unsafe_allow_html=True)
        col5, col6, col7 = st.columns(3)
        with col5:
            st.markdown(f'<a href="https://www.youtube.com/results?search_query={categoria_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">▶ YouTube</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.google.com/search?q={categoria_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">🔍 Google</a>', unsafe_allow_html=True)
        with col6:
            st.markdown(f'<a href="https://www.tiktok.com/search?q={categoria_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">◐ TikTok</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.instagram.com/explore/tags/{categoria_url}/" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">◈ Instagram</a>', unsafe_allow_html=True)
        with col7:
            st.markdown(f'<a href="https://x.com/search?q={categoria_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">◉ X/Twitter</a>', unsafe_allow_html=True)
            st.markdown(f'<a href="https://www.reddit.com/search/?q={categoria_url}" target="_blank" style="color:#B99A70; text-decoration:none; display:block; margin:0.3rem 0;">◎ Reddit</a>', unsafe_allow_html=True)