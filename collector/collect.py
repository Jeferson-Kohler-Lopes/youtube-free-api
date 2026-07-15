from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

try:
    import yt_dlp
except ImportError as exc:
    raise SystemExit("Instale as dependências com: pip install -r requirements.txt") from exc

from .analysis import (
    build_report,
    build_search_queries,
    channel_similarity,
    channel_summary_from_info,
    classify_niche,
    enrich_video_scores,
    extract_keywords,
    language_looks_english,
    normalize_text,
    video_from_info,
)
from .thumbnail import summarize_thumbnails


def normalize_channel_url(value: str) -> str:
    value = value.strip()
    if value.startswith("@"):
        value = f"https://www.youtube.com/{value}"
    elif not value.startswith("http"):
        value = f"https://www.youtube.com/@{value}"
    base = value.rstrip("/")
    if not any(segment in base for segment in ["/videos", "/shorts", "/streams", "/playlist"]):
        base += "/videos"
    return base


def ydl_options(maximum: int, flat: bool = True) -> dict[str, Any]:
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": True,
        "extract_flat": "in_playlist" if flat else False,
        "socket_timeout": 20,
        "retries": 3,
        "fragment_retries": 3,
        "noplaylist": False,
    }
    if maximum > 0:
        options["playlistend"] = maximum
    return options


def extract(url: str, maximum: int, flat: bool = True) -> dict[str, Any]:
    with yt_dlp.YoutubeDL(ydl_options(maximum, flat=flat)) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise RuntimeError(f"Não foi possível coletar: {url}")
    return info


def merge_video(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in extra.items():
        if value not in (None, "", [], 0):
            merged[key] = value
    return merged


def collect_channel(url: str, maximum: int, deep_all: bool = False, deep_limit: int = 30) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    normalized_url = normalize_channel_url(url)
    playlist = extract(normalized_url, maximum=maximum, flat=True)
    raw_entries = [entry for entry in (playlist.get("entries") or []) if entry]
    videos = [video_from_info(entry) for entry in raw_entries]
    videos = [video for video in videos if video.get("id")]
    if not videos:
        raise RuntimeError("O canal não retornou vídeos públicos. Confira a URL ou atualize o yt-dlp.")

    indices: list[int]
    if deep_all:
        indices = list(range(len(videos)))
    else:
        ranked = sorted(range(len(videos)), key=lambda index: videos[index].get("views", 0), reverse=True)[:deep_limit]
        newest = list(range(min(10, len(videos))))
        indices = sorted(set(ranked + newest))

    for index in indices:
        video_url = videos[index]["url"]
        try:
            full = extract(video_url, maximum=1, flat=False)
            videos[index] = merge_video(videos[index], video_from_info(full))
        except Exception:
            continue

    videos = enrich_video_scores(videos)
    videos.sort(key=lambda item: item.get("publishedAt") or "", reverse=True)
    channel = channel_summary_from_info(playlist, videos, normalized_url)
    return channel, videos


def search_candidates(queries: list[str], source_channel_url: str, per_query: int = 8) -> list[dict[str, Any]]:
    candidates: dict[str, dict[str, Any]] = {}
    source_normalized = normalize_text(source_channel_url)
    for query in queries[:3]:
        try:
            result = extract(f"ytsearch{per_query}:{query}", maximum=per_query, flat=True)
        except Exception:
            continue
        for entry in result.get("entries") or []:
            if not entry:
                continue
            channel_url = str(entry.get("channel_url") or entry.get("uploader_url") or "")
            channel_id = str(entry.get("channel_id") or entry.get("uploader_id") or "")
            channel_name = str(entry.get("channel") or entry.get("uploader") or "")
            key = channel_id or channel_url or channel_name
            if not key or source_normalized in normalize_text(channel_url):
                continue
            record = candidates.setdefault(key, {
                "url": channel_url,
                "id": channel_id,
                "title": channel_name,
                "occurrence": 0,
                "sampleTitles": [],
            })
            record["occurrence"] += 1
            if entry.get("title"):
                record["sampleTitles"].append(str(entry["title"]))
    return list(candidates.values())


def analyze_competitors(
    source_channel: dict[str, Any],
    source_videos: list[dict[str, Any]],
    queries: list[str],
    maximum_competitors: int,
    competitor_videos: int,
    manual_urls: list[str],
) -> list[dict[str, Any]]:
    source_keywords = extract_keywords(source_videos, 20)
    candidates = search_candidates(queries, source_channel.get("url", ""))
    for url in manual_urls:
        candidates.append({"url": url, "id": "", "title": "Referência manual", "occurrence": 5, "sampleTitles": [], "manual": True})

    deduped = {}
    for candidate in candidates:
        key = candidate.get("id") or candidate.get("url")
        if key:
            deduped[key] = candidate
    ranked_pre = sorted(
        deduped.values(),
        key=lambda item: (
            language_looks_english(" ".join(item.get("sampleTitles") or [])),
            item.get("occurrence", 0),
        ),
        reverse=True,
    )[: max(maximum_competitors * 3, maximum_competitors)]

    analyses = []
    for candidate in ranked_pre:
        if len(analyses) >= maximum_competitors:
            break
        url = candidate.get("url")
        if not url:
            continue
        try:
            channel, videos = collect_channel(url, maximum=competitor_videos, deep_all=False, deep_limit=8)
        except Exception:
            continue
        score = channel_similarity(source_keywords, videos, int(candidate.get("occurrence") or 1))
        if not language_looks_english(" ".join(video["title"] for video in videos[:10])) and not candidate.get("manual"):
            continue
        top = sorted(videos, key=lambda item: (item.get("outlierScore", 0), item.get("viewsPerDay", 0)), reverse=True)[:6]
        analyses.append({
            "channel": channel,
            "verifiedUnitedStates": False,
            "countryStatus": "estimated_english",
            "relevanceScore": round(score, 1),
            "topVideos": top,
            "keywords": extract_keywords(videos, 10),
            "originNote": "Canal em inglês encontrado por busca pública; país não confirmado sem API.",
        })
    analyses.sort(key=lambda item: item["relevanceScore"], reverse=True)
    return analyses


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analisa canais do YouTube sem usar a YouTube Data API.")
    parser.add_argument("channel", help="URL, @handle ou nome do canal")
    parser.add_argument("--max-videos", type=int, default=200, help="Máximo de vídeos do canal principal")
    parser.add_argument("--all-videos", action="store_true", help="Coletar toda a aba de vídeos; recomendado somente no computador")
    parser.add_argument("--max-competitors", type=int, default=3, help="Máximo de referências em inglês")
    parser.add_argument("--competitor-videos", type=int, default=20, help="Vídeos por canal de referência")
    parser.add_argument("--competitor-url", action="append", default=[], help="Canal de referência manual; pode repetir")
    parser.add_argument("--skip-competitors", action="store_true", help="Não pesquisar referências")
    parser.add_argument("--deep-all", action="store_true", help="Abrir cada vídeo individualmente para buscar metadados completos")
    parser.add_argument("--skip-thumbnails", action="store_true", help="Não baixar thumbnails para métricas visuais")
    parser.add_argument("--output", default="reports/latest.json", help="Arquivo JSON de saída")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    maximum = 0 if args.all_videos else max(10, min(args.max_videos, 2000))
    try:
        print("1/4 Coletando o canal principal...", file=sys.stderr)
        channel, videos = collect_channel(args.channel, maximum=maximum, deep_all=args.deep_all)
        preliminary_keywords = extract_keywords(videos, 20)
        niche = classify_niche(channel, preliminary_keywords)
        queries = build_search_queries(niche, preliminary_keywords)

        competitors = []
        if not args.skip_competitors and args.max_competitors > 0:
            print("2/4 Buscando referências em inglês...", file=sys.stderr)
            competitors = analyze_competitors(
                channel,
                videos,
                queries,
                maximum_competitors=max(0, min(args.max_competitors, 6)),
                competitor_videos=max(5, min(args.competitor_videos, 50)),
                manual_urls=args.competitor_url,
            )

        print("3/4 Analisando thumbnails de destaque...", file=sys.stderr)
        top_for_thumbnails = sorted(videos, key=lambda item: item.get("outlierScore", 0), reverse=True)[:12]
        thumbnail_insights = {} if args.skip_thumbnails else summarize_thumbnails(top_for_thumbnails)

        print("4/4 Gerando relatório...", file=sys.stderr)
        report = build_report(
            channel,
            videos,
            competitors,
            queries,
            thumbnail_insights=thumbnail_insights,
            requested_max=maximum or None,
        )
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Relatório salvo em {output}")
        return 0
    except KeyboardInterrupt:
        print("Execução interrompida.", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        print("Tente atualizar o coletor com: pip install -U yt-dlp", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
