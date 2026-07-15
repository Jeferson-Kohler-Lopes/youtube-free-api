from __future__ import annotations

import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
    "e", "em", "no", "na", "nos", "nas", "por", "para", "com", "sem", "que", "como",
    "mais", "menos", "se", "seu", "sua", "seus", "suas", "meu", "minha", "eu", "voce",
    "voces", "ele", "ela", "eles", "elas", "isso", "isto", "essa", "esse", "este", "esta",
    "ao", "aos", "ou", "ja", "the", "an", "and", "or", "to", "of", "in", "on", "for",
    "with", "without", "is", "are", "be", "this", "that", "how", "your", "you", "my",
    "our", "from", "at", "by", "it", "its", "why", "what", "when", "new", "video",
    "videos", "youtube", "parte", "part", "episodio", "episode", "ep", "shorts", "short",
    "live", "podcast", "oficial", "official", "feat", "ft", "canal", "channel",
}

NICHES = [
    {
        "id": "marketing",
        "label": "Marketing, vendas e negócios",
        "terms": ["marketing", "vendas", "vender", "trafego", "copy", "funil", "negocio", "empresa", "empreendedor", "cliente", "social media", "anuncio"],
        "english": ["digital marketing", "sales strategy", "business growth"],
    },
    {
        "id": "finance",
        "label": "Finanças e investimentos",
        "terms": ["dinheiro", "financas", "investimento", "investir", "acoes", "bolsa", "renda", "bitcoin", "economia", "patrimonio"],
        "english": ["personal finance", "investing", "wealth building"],
    },
    {
        "id": "health",
        "label": "Saúde, fitness e bem-estar",
        "terms": ["saude", "treino", "fitness", "emagrecer", "dieta", "nutricao", "medicina", "terapia", "bem estar", "exercicio"],
        "english": ["health education", "fitness", "wellness"],
    },
    {
        "id": "technology",
        "label": "Tecnologia e inteligência artificial",
        "terms": ["tecnologia", "inteligencia artificial", "chatgpt", "programacao", "software", "aplicativo", "automacao", "dados", "saas", "codigo"],
        "english": ["artificial intelligence", "software tools", "technology tutorials"],
    },
    {
        "id": "education",
        "label": "Educação e desenvolvimento profissional",
        "terms": ["curso", "aprender", "estudo", "carreira", "profissao", "concurso", "aula", "educacao", "oratória", "comunicacao"],
        "english": ["educational channel", "career development", "professional skills"],
    },
    {
        "id": "law",
        "label": "Direito e advocacia",
        "terms": ["direito", "advogado", "advocacia", "juridico", "lei", "processo", "tribunal", "justica"],
        "english": ["legal education", "law firm growth", "lawyer channel"],
    },
    {
        "id": "beauty",
        "label": "Beleza, moda e estilo",
        "terms": ["beleza", "maquiagem", "moda", "roupa", "cabelo", "pele", "estilo", "look"],
        "english": ["beauty", "fashion", "style tips"],
    },
    {
        "id": "food",
        "label": "Culinária e alimentação",
        "terms": ["receita", "cozinha", "comida", "bolo", "carne", "restaurante", "culinaria", "alimentacao"],
        "english": ["cooking channel", "recipes", "food creator"],
    },
    {
        "id": "automotive",
        "label": "Automóveis e motocicletas",
        "terms": ["carro", "moto", "motor", "oficina", "mecanica", "automotivo", "veiculo"],
        "english": ["automotive channel", "car reviews", "motorcycle channel"],
    },
    {
        "id": "gaming",
        "label": "Games e entretenimento",
        "terms": ["game", "games", "jogo", "jogos", "gamer", "gameplay", "stream", "filme", "serie"],
        "english": ["gaming channel", "gameplay", "entertainment creator"],
    },
    {
        "id": "spirituality",
        "label": "Espiritualidade e desenvolvimento pessoal",
        "terms": ["espiritual", "deus", "fe", "oracao", "energia", "autoconhecimento", "proposito", "mente", "emocao"],
        "english": ["spirituality", "personal growth", "self knowledge"],
    },
]

TRANSLATIONS = {
    "marketing": "digital marketing", "vendas": "sales", "vender": "selling", "trafego": "paid traffic",
    "funil": "sales funnel", "negocio": "business", "empresa": "business", "empreendedor": "entrepreneurship",
    "cliente": "client acquisition", "dinheiro": "money", "financas": "finance", "investimento": "investing",
    "saude": "health", "treino": "workout", "dieta": "diet", "nutricao": "nutrition",
    "tecnologia": "technology", "automacao": "automation", "programacao": "programming", "software": "software",
    "curso": "education", "carreira": "career", "direito": "law", "advogado": "lawyer", "advocacia": "law firm",
    "beleza": "beauty", "moda": "fashion", "receita": "recipes", "cozinha": "cooking", "carro": "cars",
    "moto": "motorcycles", "mecanica": "mechanics", "jogo": "gaming", "jogos": "gaming",
    "espiritual": "spirituality", "produtividade": "productivity", "comunicacao": "communication",
}


def normalize_text(value: str | None) -> str:
    value = value or ""
    normalized = unicodedata.normalize("NFD", value)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn").lower()


def tokenize(value: str | None) -> list[str]:
    text = re.sub(r"https?://\S+", " ", normalize_text(value))
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    tokens = []
    for token in text.split():
        token = token.strip("-")
        if len(token) >= 3 and token not in STOPWORDS and not token.isdigit():
            tokens.append(token)
    return tokens


def safe_number(value: Any) -> float:
    try:
        number = float(value or 0)
        return number if math.isfinite(number) else 0
    except (TypeError, ValueError):
        return 0


def iso_date_from_info(info: dict[str, Any]) -> str:
    timestamp = info.get("timestamp") or info.get("release_timestamp")
    if timestamp:
        return datetime.fromtimestamp(float(timestamp), tz=timezone.utc).isoformat()
    upload_date = str(info.get("upload_date") or info.get("release_date") or "")
    if re.fullmatch(r"\d{8}", upload_date):
        return datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc).isoformat()
    return ""


def format_duration(seconds: float | int | None) -> str:
    total = max(0, int(seconds or 0))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def best_thumbnail(info: dict[str, Any]) -> str:
    thumbnails = info.get("thumbnails") or []
    if thumbnails:
        candidates = sorted(
            (thumb for thumb in thumbnails if thumb.get("url")),
            key=lambda item: safe_number(item.get("width")) * safe_number(item.get("height")),
        )
        if candidates:
            return str(candidates[-1]["url"])
    return str(info.get("thumbnail") or "")


def video_from_info(info: dict[str, Any]) -> dict[str, Any]:
    video_id = str(info.get("id") or "")
    url = str(info.get("webpage_url") or info.get("url") or "")
    if video_id and (not url or not url.startswith("http")):
        url = f"https://www.youtube.com/watch?v={video_id}"
    duration = int(safe_number(info.get("duration")))
    published_at = iso_date_from_info(info)
    views = int(safe_number(info.get("view_count")))
    likes = int(safe_number(info.get("like_count")))
    comments = int(safe_number(info.get("comment_count")))
    if published_at:
        try:
            age_days = max(1, (datetime.now(timezone.utc) - datetime.fromisoformat(published_at)).total_seconds() / 86400)
        except ValueError:
            age_days = 1
    else:
        age_days = 1
    return {
        "id": video_id,
        "title": str(info.get("title") or "Vídeo sem título"),
        "description": str(info.get("description") or ""),
        "publishedAt": published_at,
        "thumbnail": best_thumbnail(info),
        "url": url,
        "tags": [str(tag) for tag in (info.get("tags") or []) if tag],
        "durationSeconds": duration,
        "durationLabel": format_duration(duration),
        "views": views,
        "likes": likes,
        "comments": comments,
        "viewsPerDay": round(views / age_days, 2),
        "engagementRate": round(((likes + comments) / views * 100), 3) if views else 0,
        "outlierScore": 0,
        "isShort": duration > 0 and duration <= 180,
        "channel": str(info.get("channel") or info.get("uploader") or ""),
        "channelId": str(info.get("channel_id") or info.get("uploader_id") or ""),
        "channelUrl": str(info.get("channel_url") or info.get("uploader_url") or ""),
    }


def median(values: Iterable[float]) -> float:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    return statistics.median(clean) if clean else 0


def average(values: Iterable[float]) -> float:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    return statistics.fmean(clean) if clean else 0


def enrich_video_scores(videos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normal_median = median(video["views"] for video in videos if not video["isShort"])
    short_median = median(video["views"] for video in videos if video["isShort"])
    overall_median = median(video["views"] for video in videos)
    for video in videos:
        reference = (short_median if video["isShort"] else normal_median) or overall_median
        video["outlierScore"] = round(video["views"] / reference, 3) if reference else 0
    return videos


def extract_keywords(videos: list[dict[str, Any]], maximum: int = 20) -> list[dict[str, Any]]:
    scores: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "weightedScore": 0})
    for video in videos:
        terms = set(tokenize(video.get("title")))
        for tag in video.get("tags") or []:
            terms.update(tokenize(tag))
        weight = max(0.5, min(8, safe_number(video.get("outlierScore")) or 1))
        for term in terms:
            scores[term]["count"] += 1
            scores[term]["weightedScore"] += weight
    ranked = [
        {"term": term, "count": int(values["count"]), "weightedScore": round(values["weightedScore"], 3)}
        for term, values in scores.items()
    ]
    return sorted(ranked, key=lambda item: (-item["weightedScore"], -item["count"], item["term"]))[:maximum]


def posting_frequency(videos: list[dict[str, Any]]) -> float | None:
    dated = [video for video in videos[:30] if video.get("publishedAt")]
    if len(dated) < 2:
        return None
    timestamps = sorted((datetime.fromisoformat(video["publishedAt"]).timestamp() for video in dated), reverse=True)
    intervals = [abs(timestamps[index - 1] - timestamps[index]) / 86400 for index in range(1, len(timestamps))]
    return round(average(intervals), 2) if intervals else None


def classify_niche(channel: dict[str, Any], keywords: list[dict[str, Any]]) -> dict[str, Any]:
    corpus = normalize_text(" ".join([
        str(channel.get("title") or ""),
        str(channel.get("description") or ""),
        " ".join(item["term"] for item in keywords),
    ]))
    token_set = set(tokenize(corpus))
    ranked = []
    for niche in NICHES:
        matched = [term for term in niche["terms"] if normalize_text(term) in corpus or normalize_text(term) in token_set]
        keyword_weight = sum(
            item["weightedScore"]
            for item in keywords
            if any(normalize_text(term) in item["term"] for term in niche["terms"])
        )
        ranked.append((len(matched) * 2 + keyword_weight, niche, matched))
    ranked.sort(key=lambda item: item[0], reverse=True)
    winner_score, winner, matched = ranked[0]
    runner_score = ranked[1][0] if len(ranked) > 1 else 0
    if winner_score <= 0:
        fallback = [TRANSLATIONS.get(item["term"], item["term"]) for item in keywords[:3]]
        return {
            "id": "general",
            "label": "Conteúdo especializado / nicho geral",
            "confidence": 0.35,
            "matchedTerms": [item["term"] for item in keywords[:5]],
            "englishSearchTerms": [f"{term} expert channel" for term in fallback] or ["educational creator channel"],
        }
    confidence = min(0.98, 0.55 + max(0, winner_score - runner_score) / max(10, winner_score * 2))
    return {
        "id": winner["id"],
        "label": winner["label"],
        "confidence": round(confidence, 3),
        "matchedTerms": matched[:8],
        "englishSearchTerms": winner["english"],
    }


def build_search_queries(niche: dict[str, Any], keywords: list[dict[str, Any]]) -> list[str]:
    translated = [TRANSLATIONS.get(item["term"], item["term"]) for item in keywords[:6]]
    translated = [term for term in translated if re.fullmatch(r"[a-z0-9\s-]+", term, re.I)]
    queries = list(niche.get("englishSearchTerms") or [])
    if translated:
        queries.append(" ".join(translated[:3]))
    unique = []
    for query in queries:
        query = query.strip()
        if query and query not in unique:
            unique.append(query)
    return unique[:3]


def language_looks_english(text: str) -> bool:
    normalized = f" {normalize_text(text)} "
    english = sum(term in normalized for term in [" the ", " and ", " how ", " with ", " your ", " for ", " to ", " of "])
    portuguese = sum(term in normalized for term in [" que ", " para ", " como ", " com ", " voce ", " dos ", " uma ", " nao "])
    return english >= portuguese


def channel_similarity(source_keywords: list[dict[str, Any]], candidate_videos: list[dict[str, Any]], occurrence: int = 1) -> float:
    source_terms = {item["term"] for item in source_keywords[:15]}
    candidate_terms = {item["term"] for item in extract_keywords(candidate_videos, 20)}
    overlap = len(source_terms.intersection(candidate_terms))
    titles = " ".join(video.get("title", "") for video in candidate_videos[:10])
    language = 20 if language_looks_english(titles) else -15
    return max(0, overlap * 7 + min(25, occurrence * 4) + language)


def duration_bucket(video: dict[str, Any]) -> str:
    seconds = int(video.get("durationSeconds") or 0)
    if video.get("isShort"):
        return "Shorts (até 3 min)"
    if seconds < 300:
        return "Até 5 min"
    if seconds < 600:
        return "5–10 min"
    if seconds < 1200:
        return "10–20 min"
    return "Mais de 20 min"


def build_insights(channel: dict[str, Any], videos: list[dict[str, Any]], keywords: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not videos:
        return []
    top = sorted(videos, key=lambda item: (item.get("outlierScore", 0), item.get("viewsPerDay", 0)), reverse=True)[:20]
    buckets: dict[str, list[float]] = defaultdict(list)
    for video in top:
        buckets[duration_bucket(video)].append(safe_number(video.get("outlierScore")))
    best_duration = max(buckets, key=lambda key: average(buckets[key])) if buckets else "Sem dados suficientes"
    questions = sum(bool(re.search(r"\?|\bcomo\b|\bpor que\b|\bwhy\b|\bhow\b", normalize_text(video["title"]))) for video in top)
    numbered = sum(bool(re.match(r"^\s*\d+\b", video["title"])) for video in top)
    short_share = sum(bool(video.get("isShort")) for video in videos) / len(videos)
    frequency = posting_frequency(videos)
    best_terms = ", ".join(item["term"] for item in keywords[:5])
    return [
        {
            "title": "Faixa de duração com maior sinal",
            "finding": f"{best_duration} apresenta o melhor desempenho relativo entre os conteúdos de destaque.",
            "action": "Teste uma série de quatro vídeos nessa faixa antes de mudar toda a estratégia de duração.",
        },
        {
            "title": "Estrutura de títulos",
            "finding": f"{questions} dos {len(top)} destaques usam pergunta ou linguagem explicativa; {numbered} começam com número.",
            "action": "Use promessa específica, mecanismo claro e consequência prática. Evite títulos genéricos.",
        },
        {
            "title": "Temas que concentram resultado",
            "finding": f"Os termos com maior peso são: {best_terms}." if best_terms else "Não houve volume suficiente para destacar temas.",
            "action": "Transforme cada tema vencedor em introdução, erros, estudo de caso, comparação e passo a passo.",
        },
        {
            "title": "Cadência recente",
            "finding": f"O intervalo médio recente é de {frequency:.1f} dias." if frequency else "Não há datas suficientes para calcular a cadência.",
            "action": "Mantenha uma frequência sustentável e concentre os testes em tema, título e thumbnail.",
        },
        {
            "title": "Papel dos Shorts",
            "finding": f"{round(short_share * 100)}% dos vídeos analisados foram classificados como Shorts.",
            "action": "Compare Shorts e vídeos longos separadamente, pois os padrões de visualização são diferentes.",
        },
        {
            "title": "Meta de vídeo fora da curva",
            "finding": f"O canal {channel.get('title', '')} possui conteúdos que superam a própria mediana.",
            "action": "Crie continuações dos vídeos acima de 2x da mediana, mantendo a promessa e alterando o ângulo.",
        },
    ]


def clean_topic(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[-_:|]+", " ", value)).strip()[:75]


def generate_ideas(source_top: list[dict[str, Any]], keywords: list[dict[str, Any]], competitors: list[dict[str, Any]]) -> list[dict[str, str]]:
    ideas: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(title: str, angle: str, thumbnail: str, based_on: str, potential: str = "alto") -> None:
        key = normalize_text(title)
        if key not in seen:
            seen.add(key)
            ideas.append({
                "title": title,
                "angle": angle,
                "thumbnailText": thumbnail,
                "basedOn": based_on,
                "potential": potential,
            })

    for item in keywords[:10]:
        topic = item["term"].title()
        add(
            f"Como dominar {topic} sem cometer os erros mais comuns",
            "Tutorial prático com quebra de objeções.",
            f"{topic}: SEM ERROS",
            "Tema recorrente entre os vídeos com melhor desempenho.",
        )
        add(
            f"7 erros de {topic} que estão prejudicando seus resultados",
            "Lista com dor, diagnóstico e correção.",
            "VOCÊ FAZ ISSO?",
            "Transformação do tema vencedor em formato de lista.",
        )

    for video in source_top[:7]:
        topic = clean_topic(video["title"])
        add(
            f"{topic}: o que mudou e o que eu faria hoje",
            "Atualização de um conteúdo que já provou demanda.",
            "EU FARIA ASSIM",
            f"Continuação de “{video['title']}” ({video.get('outlierScore', 0):.1f}x da mediana).",
            "alto" if video.get("outlierScore", 0) >= 2 else "médio",
        )

    for competitor in competitors:
        for video in competitor.get("topVideos", [])[:3]:
            add(
                f"A versão brasileira de: {clean_topic(video['title'])}",
                "Adaptar a tese estrangeira ao contexto, exemplos e linguagem do público brasileiro.",
                "ISSO CHEGOU AO BRASIL",
                f"Referência encontrada em inglês no canal {competitor['channel']['title']}.",
                "alto" if video.get("outlierScore", 0) >= 1.5 else "médio",
            )
    return ideas[:30]


def channel_summary_from_info(info: dict[str, Any], videos: list[dict[str, Any]], source_url: str) -> dict[str, Any]:
    first = next((entry for entry in videos if entry), {})
    channel_id = str(info.get("channel_id") or info.get("uploader_id") or first.get("channelId") or "")
    title = str(info.get("channel") or info.get("uploader") or info.get("title") or first.get("channel") or "Canal")
    description = str(info.get("description") or "")
    thumbnail = best_thumbnail(info)
    if not thumbnail and first:
        thumbnail = str(first.get("thumbnail") or "")
    channel_url = str(info.get("channel_url") or info.get("uploader_url") or source_url)
    return {
        "id": channel_id or normalize_text(title).replace(" ", "-"),
        "title": title,
        "description": description,
        "customUrl": "",
        "country": None,
        "publishedAt": "",
        "thumbnail": thumbnail,
        "subscriberCount": int(safe_number(info.get("channel_follower_count"))),
        "viewCount": int(sum(video.get("views", 0) for video in videos)),
        "videoCount": int(safe_number(info.get("playlist_count")) or len(videos)),
        "uploadsPlaylistId": "",
        "url": channel_url or source_url,
    }


def build_report(
    channel: dict[str, Any],
    videos: list[dict[str, Any]],
    competitors: list[dict[str, Any]],
    search_queries: list[str],
    thumbnail_insights: dict[str, Any] | None = None,
    requested_max: int | None = None,
) -> dict[str, Any]:
    videos = enrich_video_scores(videos)
    videos.sort(key=lambda item: item.get("publishedAt") or "", reverse=True)
    keywords = extract_keywords(videos, 20)
    niche = classify_niche(channel, keywords)
    top_videos = sorted(videos, key=lambda item: (item.get("outlierScore", 0), item.get("viewsPerDay", 0)), reverse=True)[:20]
    report = {
        "version": "2.0-no-api",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "collectionMethod": "yt-dlp + análise local; nenhuma YouTube Data API utilizada",
        "channel": channel,
        "niche": niche,
        "videosAnalyzed": len(videos),
        "totalPublicVideosReported": channel.get("videoCount") or len(videos),
        "truncated": bool(requested_max and (channel.get("videoCount") or 0) > requested_max),
        "medianViews": round(median(video["views"] for video in videos), 2),
        "averageViews": round(average(video["views"] for video in videos), 2),
        "averageViewsPerDay": round(average(video["viewsPerDay"] for video in videos), 2),
        "postingFrequencyDays": posting_frequency(videos),
        "keywords": keywords,
        "topVideos": top_videos,
        "recentVideos": videos[:12],
        "competitors": competitors,
        "insights": build_insights(channel, videos, keywords),
        "ideas": generate_ideas(top_videos, keywords, competitors),
        "searchQueries": search_queries,
        "thumbnailInsights": thumbnail_insights or {},
        "limitations": [
            "Esta edição não usa a YouTube Data API nem exige chave do Google.",
            "A coleta depende da estrutura pública das páginas do YouTube e pode exigir atualização do yt-dlp quando o site mudar.",
            "O país dos canais de referência não pode ser confirmado; o sistema prioriza conteúdo em inglês e trata a origem como estimativa.",
            "Curtidas, comentários, tags e descrições podem estar ausentes quando o YouTube não os expõe ao coletor.",
            "CTR, retenção, impressões, receita e fontes de tráfego continuam indisponíveis sem acesso autorizado ao YouTube Studio.",
            "A análise visual das thumbnails usa brilho, contraste, saturação e composição básica; não interpreta texto ou rostos com precisão de IA.",
        ],
    }
    return report
