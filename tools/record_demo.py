"""Record 30 actual generated maps with BFS traversal, plus measured summary."""

import json
from pathlib import Path

import imageio_ffmpeg
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from pcg.stats import GENS
from pcg.validator import pick_start, reachable, shortest_path

ROOT = Path(__file__).resolve().parents[1]
FONT = "C:/Windows/Fonts/arial.ttf"
OUT = ROOT / "videos" / "lab07_demo.mp4"


def font(size):
    return ImageFont.truetype(FONT, size)


def frame(name, seed, progress=1):
    grid = GENS[name](seed=seed)
    dist, m = reachable(grid, pick_start(grid))
    path = shortest_path(dist, m["finish"])
    im = Image.new("RGB", (1280, 880), "#f3f6f8")
    d = ImageDraw.Draw(im)
    d.text((30, 18), "ЛР 7 · Процедурная генерация уровней", font=font(30), fill="#15283b")
    d.text((30, 60), f"{name}  |  seed = {seed}  |  64 × 48", font=font(23), fill="#15283b")
    scale, ox, oy = 14, 30, 110
    for y in range(48):
        for x in range(64):
            color = "#15283b" if grid[y, x] else ("#e5edf0" if dist[y, x] >= 0 else "#f1b98b")
            d.rectangle(
                (ox + x * scale, oy + y * scale, ox + (x + 1) * scale - 1, oy + (y + 1) * scale - 1), fill=color
            )
    if path:
        points = [(ox + x * scale + scale // 2, oy + y * scale + scale // 2) for y, x in path]
        count = max(1, int(progress * len(points)))
        if count > 1:
            d.line(points[:count], fill="#31a6a0", width=3)
        for (x, y), color in [(points[0], "#15a14a"), (points[-1], "#d62f49")]:
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=color)
        x, y = points[count - 1]
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill="#e7b51a")
    lines = [
        "Проверка BFS",
        "",
        f"Доступно: {m['reach_ratio']:.1%}",
        f"Путь S → F: {m['path_len']}",
        "",
        "Зелёный: старт",
        "Красный: финиш",
        "Бирюзовый: путь",
        "Оранжевый:",
        "недоступный пол",
        "",
        "Соседи: 4",
        "Стены: 1, пол: 0",
        "",
        "Печенов В. В.",
        "ИВТ-465",
    ]
    for i, line in enumerate(lines):
        d.text((950, 118 + i * 32), line, font=font(21), fill="#15283b")
    d.text(
        (30, 805), "Детерминированные карты; показаны все seed 0–9 для каждого варианта.", font=font(23), fill="#15283b"
    )
    return im


def main():
    OUT.parent.mkdir(exist_ok=True)
    writer = imageio_ffmpeg.write_frames(
        str(OUT), (1280, 880), fps=10, codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p", quality=7
    )
    writer.send(None)
    try:
        for name in GENS:
            for seed in range(10):
                for t in range(30):
                    im = frame(name, seed, min(1, t / 23))
                    writer.send(im.tobytes())
        summary = pd.read_csv(ROOT / "results/summary.csv")
        im = Image.new("RGB", (1280, 880), "#f3f6f8")
        d = ImageDraw.Draw(im)
        d.text((60, 70), "Результаты: 100 seed на вариант", font=font(40), fill="#15283b")
        for i, row in summary.iterrows():
            y = 200 + i * 150
            d.text(
                (60, y),
                f"{row.gen}: проходимых {row.playable_pct:.0f}% | полностью связных {row.fully_connected_pct:.0f}%",
                font=font(29),
                fill="#15283b",
            )
            d.text(
                (60, y + 50),
                f"Доля пола {row.floor_ratio_mean:.3f} | доступно {row.reach_ratio_mean:.3f} | "
                f"генерация {row.gen_ms_mean:.3f} мс",
                font=font(24),
                fill="#15283b",
            )
        d.text((60, 720), "Проходимость: доступно ≥ 60% пола, длина пути ≥ 20 шагов.", font=font(27), fill="#15283b")
        d.text((60, 775), "CSV, тесты, исходные карты и отчёт находятся в репозитории.", font=font(27), fill="#15283b")
        for _ in range(70):
            writer.send(im.tobytes())
    finally:
        writer.close()
    (ROOT / "results/video.json").write_text(
        json.dumps(
            {
                "file": OUT.name,
                "fps": 10,
                "frames": 970,
                "seconds": 97,
                "maps": 30,
                "seeds": "0..9",
                "variants": list(GENS),
                "description": "BFS path animation over actual grids, no audio",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(OUT)


if __name__ == "__main__":
    main()
