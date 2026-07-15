from __future__ import annotations

import colorsys
import io
import statistics
import urllib.request
from collections import Counter
from typing import Any

from PIL import Image, ImageFilter, ImageStat


def _download(url: str, timeout: int = 12) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def analyze_thumbnail(url: str) -> dict[str, Any] | None:
    if not url:
        return None
    try:
        image = Image.open(io.BytesIO(_download(url))).convert("RGB")
        image.thumbnail((256, 144))
        gray = image.convert("L")
        stat = ImageStat.Stat(gray)
        brightness = float(stat.mean[0])
        contrast = float(stat.stddev[0])
        hsv_values = []
        small = image.resize((48, 27))
        for red, green, blue in small.getdata():
            _, saturation, _ = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
            hsv_values.append(saturation * 100)
        saturation = statistics.fmean(hsv_values) if hsv_values else 0
        edge = gray.filter(ImageFilter.FIND_EDGES).resize((48, 27))
        edge_mean = ImageStat.Stat(edge).mean[0]
        quantized = small.quantize(colors=5).convert("RGB")
        dominant = Counter(quantized.getdata()).most_common(3)
        return {
            "brightness": round(brightness, 1),
            "contrast": round(contrast, 1),
            "saturation": round(saturation, 1),
            "edgeDensity": round(float(edge_mean), 1),
            "dominantColors": [_hex(color) for color, _ in dominant],
        }
    except Exception:
        return None


def summarize_thumbnails(videos: list[dict[str, Any]], maximum: int = 12) -> dict[str, Any]:
    samples = []
    for video in videos[:maximum]:
        result = analyze_thumbnail(str(video.get("thumbnail") or ""))
        if result:
            samples.append({"videoId": video.get("id"), "title": video.get("title"), **result})
    if not samples:
        return {"samplesAnalyzed": 0, "notes": ["Não foi possível baixar thumbnails nesta execução."]}

    brightness = statistics.fmean(item["brightness"] for item in samples)
    contrast = statistics.fmean(item["contrast"] for item in samples)
    saturation = statistics.fmean(item["saturation"] for item in samples)
    edges = statistics.fmean(item["edgeDensity"] for item in samples)
    colors = Counter(color for item in samples for color in item["dominantColors"])
    notes = []
    notes.append("As thumbnails de destaque tendem a ser claras." if brightness >= 135 else "As thumbnails de destaque tendem a ser mais escuras.")
    notes.append("O contraste visual é forte." if contrast >= 55 else "O contraste visual é moderado; há espaço para testes mais marcantes.")
    notes.append("A paleta é bastante saturada." if saturation >= 45 else "A paleta usa saturação moderada.")
    notes.append("Há bastante informação visual." if edges >= 35 else "A composição tende a ser visualmente simples.")
    return {
        "samplesAnalyzed": len(samples),
        "averageBrightness": round(brightness, 1),
        "averageContrast": round(contrast, 1),
        "averageSaturation": round(saturation, 1),
        "averageEdgeDensity": round(edges, 1),
        "commonDominantColors": [color for color, _ in colors.most_common(6)],
        "notes": notes,
        "samples": samples,
    }
