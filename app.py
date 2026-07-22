import streamlit as st
import pandas as pd
import requests
import xml.etree.ElementTree as ET
import anthropic
import time
import numpy as np
from datetime import datetime, timezone, timedelta

st.set_page_config(page_title="Hot Topics Dashboard", layout="wide")

# ── Chaves via Streamlit Secrets ──────────────────────────────
YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")
REDDIT_CLIENT_ID = st.secrets.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = st.secrets.get("REDDIT_CLIENT_SECRET", "")
META_ACCESS_TOKEN = st.secrets.get("META_ACCESS_TOKEN", "")
TWITTER_BEARER_TOKEN = st.secrets.get("TWITTER_BEARER_TOKEN", "")
TIKTOK_API_KEY = st.secrets.get("TIKTOK_API_KEY", "")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

# ════════════════════════════════════════════════════════════
# FUNÇÕES DE COLETA
# ════════════════════════════════════════════════════════════

def coletar_google_trends(regiao="BR", max_resultados=10):
    try:
        url = f"https://trends.google.com/trending/rss?geo={regiao}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resposta = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(resposta.content)
        topicos = []
        for item in root.findall(".//item")[:max_resultados]:
            titulo = item.find("title").text
            topicos.append({
                "titulo": titulo,
                "plataforma": "google_trends",
                "metrica_principal": 0,
                "metrica_secundaria": 0
            })
        return topicos
    except:
        return []

def coletar_youtube(api_key, regiao="BR", max_resultados=10):
    if not api_key:
        return []
    try:
        from googleapiclient.discovery import build
        youtube = build("youtube", "v3", developerKey=api_key)
        resposta = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=regiao,
            maxResults=max_resultados
        ).execute()
        topicos = []
        for video in resposta["items"]:
            topicos.append({
                "titulo": video["snippet"]["title"],
                "plataforma": "youtube",
                "metrica_principal": int(video["statistics"].get("viewCount", 0)),
                "metrica_secundaria": int(video["statistics"].get("likeCount", 0))
            })
        return topicos
    except:
        return []

def coletar_reddit(client_id, client_secret, max_resultados=10):
    if not client_id or not client_secret:
        return []
    try:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="HotTopics/1.0"
        )
        subreddits = ["brasil", "investimentos", "futebol", "tecnologia"]
        topicos = []
        for sub in subreddits:
            for post in reddit.subreddit(sub).hot(limit=max_resultados // len(subreddits)):
                topicos.append({
                    "titulo": post.title,
                    "plataforma": "reddit",
                    "metrica_principal": post.score,
                    "metrica_secundaria": post.num_comments
                })
        return topicos
    except:
        return []

def coletar_meta(access_token, max_resultados=10):
    if not access_token:
        return []
    try:
        url = "https://graph.facebook.com/v22.0/me/media"
        params = {
            "fields": "id,caption,like_count,comments_count",
            "limit": max_resultados,
            "access_token": access_token
        }
        resposta = requests.get(url, params=params, timeout=10).json()
        topicos = []
        for post in resposta.get("data", []):
            topicos.append({
                "titulo": post.get("caption", "")[:100],
                "plataforma": "instagram",
                "metrica_principal": post.get("like_count", 0),
                "metrica_secundaria": post.get("comments_count", 0)
            })
        return topicos
    except:
        return []

def coletar_twitter(bearer_token, max_resultados=10):
    if not bearer_token:
        return []
    try:
        headers = {"Authorization": f"Bearer {bearer_token}"}
        url = "https://api.twitter.com/1.1/trends/place.json"
        resposta = requests.get(url, headers=headers, params={"id": 455189}, timeout=10).json()
        topicos = []
        for trend in resposta[0]["trends"][:max_resultados]:
            topicos.append({
                "titulo": trend["name"],
                "plataforma": "twitter",
                "metrica_principal": trend.get("tweet_volume", 0) or 0,
                "metrica_secundaria": 0
            })
        return topicos
    except:
        return []

def coletar_tiktok(api_key, max_resultados=10):
    if not api_key:
        return []
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        url = "https://open.tiktokapis.com/v2/research/hashtag/query/"
        resposta = requests.get(url, headers=headers, timeout=10).json()
        topicos = []
        for hashtag in resposta.get("data", {}).get("hashtags", [])[:max_resultados]:
            topicos.append({
                "titulo": f"#{hashtag.get('hashtag_name', '')}",
                "plataforma": "tiktok",
                "metrica_principal": hashtag.get("view_count", 0),
                "metrica_secundaria": hashtag.get("video_count", 0)
            })
        return topicos
    except:
        return []

def classificar_pmg(topico):
    plataforma = topico["plataforma"]
    metrica = topico["metrica_principal"]
    if plataforma == "google_trends":
        return "P"
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
        headers = {"User-Agent": "Mozilla/5.0"}
        resposta = requests.get(url, headers=headers, timeout=10)
        root = ET.fromstring(resposta.content)
        noticias = []
        for item in root.findall(".//item")[:5]:
            titulo_noticia = item.find("title")
            if titulo_noticia is not None:
                noticias.append(titulo_noticia.text)
        return noticias
    except:
        return []

def gerar_analise_ia(topico):
    if not client:
        return "IA não configurada.", "IA não configurada."
    try:
        classificacao_texto = {"P": "emergente", "M": "crescendo", "G": "mainstream"}[topico["classificacao"]]
        plataforma = topico["plataforma"]
        titulo = topico["titulo"]
        metrica = topico.get("metrica_principal", 0)

        noticias = buscar_contexto_google_news(titulo)
        contexto_noticias = "\n".join([f"- {n}" for n in noticias]) if noticias else "Nenhuma notícia encontrada."

        if plataforma == "youtube":
            contexto_plataforma = f"Este tópico está em alta no YouTube com {metrica:,} visualizações."
        elif plataforma == "google_trends":
            contexto_plataforma = "Este tópico está entre os mais buscados no Google Trends Brasil agora."
        elif plataforma == "reddit":
            contexto_plataforma = f"Este tópico tem {metrica:,} upvotes no Reddit."
        elif plataforma == "instagram":
            contexto_plataforma = f"Este tópico tem {metrica:,} likes no Instagram."
        elif plataforma == "twitter":
            contexto_plataforma = f"Este tópico tem {metrica:,} tweets no X/Twitter."
        elif plataforma == "tiktok":
            contexto_plataforma = f"Este tópico tem {metrica:,} visualizações no TikTok."
        else:
            contexto_plataforma = f"Este tópico está em alta na plataforma {plataforma}."

        prompt_resumo = f"""Você é um analista sênior de social listening de uma agência de publicidade brasileira.

Analise o tópico "{titulo}" que está {classificacao_texto} nas redes sociais brasileiras.

Contexto da plataforma: {contexto_plataforma}

Notícias e menções reais encontradas agora sobre esse tópico:
{contexto_noticias}

Com base nesses dados reais, escreva uma análise em 3 frases que explique:
1. O que está acontecendo de fato com esse tópico agora
2. Por que ele está ganhando atenção neste momento específico
3. Qual é o perfil do público que está consumindo esse conteúdo

Seja específico, use os dados reais fornecidos. Não invente contexto. Se não houver informação suficiente, diga claramente o que não foi possível identificar."""

        prompt_recomendacao = f"""Você é um estrategista de marketing de uma agência de publicidade brasileira.

Tópico: "{titulo}"
Estágio: {classificacao_texto}
Plataforma de origem: {plataforma}
Contexto: {contexto_plataforma}

Notícias e menções reais:
{contexto_noticias}

Com base nesses dados reais, recomende em 3 frases diretas, sem títulos ou markdown:
1. Se a marca deve ENTRAR, OBSERVAR ou EVITAR — com justificativa baseada nos dados reais
2. Qual o risco ou oportunidade específica desse momento
3. Se ENTRAR, qual formato de conteúdo e em qual plataforma, com timing específico"""

        resp_resumo = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt_resumo}]
        )
        time.sleep(0.3)

        resp_rec = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt_recomendacao}]
        )

        return resp_resumo.content[0].text, resp_rec.content[0].text
    except Exception as e:
        return f"Erro: {e}", f"Erro: {e}"

# ════════════════════════════════════════════════════════════
# PIPELINE AUTOMÁTICO — atualiza a cada 1 hora
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

st.title("🔥 Hot Topics — Painel de Tendências")
st.caption("Monitoramento automatizado de tópicos em alta nas redes sociais")

aba1, aba2 = st.tabs(["📋 Painel Geral", "🔍 Análise por Tema"])

# ── ABA 1 — PAINEL GERAL ─────────────────────────────────────
with aba1:
    with st.spinner("Coletando dados em tempo real..."):
        dados = rodar_pipeline()

    fuso_brasilia = timezone(timedelta(hours=-3))
    hora_atualizacao = datetime.now(fuso_brasilia).strftime("%d/%m/%Y às %H:%M")
    st.success(f"✅ {len(dados)} tópicos monitorados — atualizado em {hora_atualizacao} (renova a cada 1h)")
    st.markdown("---")

    df = pd.DataFrame(dados)

    if not df.empty:
        total_p = len(df[df["classificacao"] == "P"])
        total_m = len(df[df["classificacao"] == "M"])
        total_g = len(df[df["classificacao"] == "G"])

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

        if "analises" not in st.session_state:
            st.session_state.analises = {}

        for idx, row in df_filtrado.iterrows():
            emoji = {"P": "🌱", "M": "📈", "G": "🔥"}[row["classificacao"]]
            with st.expander(f"{emoji} [{row['classificacao']}] {row['titulo']} — {row['plataforma']}"):
                chave = f"ia_{idx}"
                if chave in st.session_state.analises:
                    resumo, recomendacao = st.session_state.analises[chave]
                    st.markdown(f"**Resumo:** {resumo}")
                    st.markdown(f"**Recomendacao:** {recomendacao}")
                else:
                    if st.button("Gerar análise IA", key=chave):
                        with st.spinner("Gerando análise..."):
                            resumo, recomendacao = gerar_analise_ia(row.to_dict())
                            st.session_state.analises[chave] = (resumo, recomendacao)
                            st.rerun()
                    else:
                        st.caption("Clique em 'Gerar análise IA' para ver resumo e recomendação.")
    else:
        st.warning("Nenhum tópico encontrado. Verifique as chaves de API nos Secrets.")

# ── ABA 2 — ANÁLISE POR TEMA ──────────────────────────────────
with aba2:
    st.subheader("🔍 Análise Completa por Tema")
    st.caption("Digite um tema para gerar um Hot Topics segmentado completo.")

    tema = st.text_input("Digite o tema:", placeholder="Ex: inteligência artificial, black friday...")

    if st.button("🔍 Analisar tema") and tema:
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

            try:
                url = "https://trends.google.com/trending/rss?geo=BR"
                headers = {"User-Agent": "Mozilla/5.0"}
                resposta = requests.get(url, headers=headers, timeout=10)
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

            volume_total = sum(d["volume"] for d in dados_plataformas.values())
            plataformas_ativas = sum(1 for d in dados_plataformas.values() if d["encontrado"])

            classificacao = "P"
            if client:
                try:
                    hoje = datetime.now(fuso_brasilia).strftime("%d/%m/%Y")
                    resp_pmg = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=50,
                        messages=[{"role": "user", "content": f"""Classifique o tema "{tema}" considerando: data de hoje: {hoje}, plataformas encontradas: {plataformas_ativas}, volume: {volume_total}. Considere sazonalidade e momentum. Responda APENAS: P, M ou G."""}]
                    )
                    classificacao = resp_pmg.content[0].text.strip().upper()
                    if classificacao not in ["P", "M", "G"]:
                        classificacao = "M" if plataformas_ativas >= 1 else "P"
                except:
                    classificacao = "G" if plataformas_ativas >= 2 else "M" if plataformas_ativas == 1 else "P"

            classificacao_mapa = {"P": ("🌱", "Emergente"), "M": ("📈", "Crescendo"), "G": ("🔥", "Mainstream")}
            emoji_pmg, classificacao_texto = classificacao_mapa[classificacao]

            resumo_ia = recomendacao_ia = sentimento_ia = tendencia_ia = hashtags_ia = ""
            if client:
                try:
                    # Busca contexto real do Google News para o tema
                    noticias_tema = buscar_contexto_google_news(tema)
                    contexto_noticias_tema = "\n".join([f"- {n}" for n in noticias_tema]) if noticias_tema else "Nenhuma notícia encontrada."

                    # Videos encontrados no YouTube
                    contexto_youtube = ""
                    if dados_plataformas.get("YouTube", {}).get("itens"):
                        videos_str = "\n".join([f"- {v}" for v in dados_plataformas["YouTube"]["itens"]])
                        contexto_youtube = f"\nVídeos em alta no YouTube sobre esse tema:\n{videos_str}"

                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=300,
                        messages=[{"role": "user", "content": f"""Você é um analista sênior de social listening de uma agência de publicidade brasileira.

Analise o tema "{tema}" que está {classificacao_texto} nas redes sociais brasileiras.

Notícias e menções reais encontradas agora:
{contexto_noticias_tema}
{contexto_youtube}

Com base nesses dados reais, escreva uma análise em 3 frases que explique:
1. O que está acontecendo de fato com esse tema agora
2. Por que ele está ganhando atenção neste momento específico
3. Qual é o perfil do público que está consumindo esse conteúdo

Seja específico. Não invente contexto. Se não houver informação suficiente, diga claramente."""}]
                    )
                    resumo_ia = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=300,
                        messages=[{"role": "user", "content": f"""Você é um estrategista de marketing de uma agência de publicidade brasileira.

Tema: "{tema}"
Estágio: {classificacao_texto}

Notícias e menções reais:
{contexto_noticias_tema}
{contexto_youtube}

Com base nesses dados reais, recomende em 3 frases diretas, sem títulos ou markdown:
1. Se a marca deve ENTRAR, OBSERVAR ou EVITAR — com justificativa baseada nos dados reais
2. Qual o risco ou oportunidade específica desse momento
3. Se ENTRAR, qual formato de conteúdo e em qual plataforma, com timing específico"""}]
                    )
                    recomendacao_ia = resp.content[0].text
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=10, messages=[{"role": "user", "content": f"""Sentimento público sobre "{tema}". Responda APENAS: POSITIVO, NEGATIVO ou NEUTRO."""}])
                    sentimento_ia = resp.content[0].text.strip().upper()
                    if sentimento_ia not in ["POSITIVO", "NEGATIVO", "NEUTRO"]:
                        sentimento_ia = "NEUTRO"
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=10, messages=[{"role": "user", "content": f"""Tendência para "{tema}" com sentimento {sentimento_ia}. Responda APENAS: MELHORANDO, PIORANDO ou ESTAVEL."""}])
                    tendencia_ia = resp.content[0].text.strip().upper()
                    if tendencia_ia not in ["MELHORANDO", "PIORANDO", "ESTAVEL"]:
                        tendencia_ia = "ESTAVEL"
                    time.sleep(0.5)

                    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=150, messages=[{"role": "user", "content": f"""Liste 8 hashtags e termos-chave sobre "{tema}" para redes sociais brasileiras. Formato: #hashtag1, #hashtag2, termo1..."""}])
                    hashtags_ia = resp.content[0].text

                except Exception as e:
                    resumo_ia = f"Erro IA: {e}"

            crescimento_pct = round(np.random.uniform(20, 60), 1) if plataformas_ativas > 0 else 0

        st.markdown("---")
        st.markdown(f"# {emoji_pmg} Hot Topics: **{tema}**")
        st.markdown(f"### Classificação: **{classificacao} — {classificacao_texto}**")
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Presença nas Plataformas")
            for plataforma, d in dados_plataformas.items():
                icone = "✅" if d["encontrado"] else "❌"
                st.markdown(f"{icone} **{plataforma}:** {d['detalhe']}")
            if "itens" in dados_plataformas.get("YouTube", {}):
                st.markdown("**Top vídeos:**")
                for v in dados_plataformas["YouTube"]["itens"]:
                    st.caption(f"• {v}")
        with col2:
            st.markdown("### Pesquisar nas Plataformas")
            for plataforma, link in links.items():
                st.markdown(f"[Ver **{plataforma}**]({link})")

        st.markdown("---")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("### Resumo e Contexto")
            st.markdown(resumo_ia)
            st.markdown("### Recomendacao de Marca")
            st.markdown(recomendacao_ia)
        with col4:
            sentimento_emoji = {"POSITIVO": "😊", "NEGATIVO": "😟", "NEUTRO": "😐"}.get(sentimento_ia, "😐")
            tendencia_emoji = {"MELHORANDO": "📈", "PIORANDO": "📉", "ESTAVEL": "➡️"}.get(tendencia_ia, "➡️")
            st.markdown("### Sentimento e Tendencia")
            st.markdown(f"**Sentimento atual:** {sentimento_emoji} {sentimento_ia}")
            st.markdown(f"**Tendencia:** {tendencia_emoji} {tendencia_ia}")
            st.markdown("### Previsao de Crescimento (7 dias)")
            seta = "📈" if crescimento_pct > 0 else "📉"
            st.markdown(f"{seta} **{crescimento_pct:+.1f}%** *(dados simulados)*")
            st.markdown("### Principais Termos e Hashtags")
            st.markdown(hashtags_ia)