"""PNG examples with a real BFS shortest path and per-generator contact sheets."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from .stats import GENS
from .validator import pick_start, reachable, shortest_path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "levels"


def draw(ax, name, seed):
    grid = GENS[name](seed=seed)
    dist, m = reachable(grid, pick_start(grid))
    colors = np.where(grid == 1, 0, np.where(dist >= 0, 1, 2))
    ax.imshow(colors, cmap=ListedColormap(["#15283b", "#e5edf0", "#f1b98b"]), vmin=0, vmax=2)
    path = shortest_path(dist, m["finish"])
    if path:
        ys, xs = zip(*path, strict=True)
        ax.plot(xs, ys, color="#31a6a0", linewidth=1.2)
        ax.scatter([xs[0]], [ys[0]], c="#15a14a", s=30, zorder=3)
        ax.scatter([xs[-1]], [ys[-1]], c="#d62f49", s=30, zorder=3)
    ax.set_title(f"{name} | seed={seed} | reach={m['reach_ratio']:.1%} | path={m['path_len']}", fontsize=9)
    ax.axis("off")
    return grid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", choices=[*GENS, "all"], default="all")
    ap.add_argument("--seeds", type=int, default=10)
    a = ap.parse_args()
    if a.seeds < 1:
        ap.error("--seeds must be positive")
    OUT.mkdir(parents=True, exist_ok=True)
    for name in GENS if a.gen == "all" else [a.gen]:
        for seed in range(a.seeds):
            fig, ax = plt.subplots(figsize=(8, 6))
            grid = draw(ax, name, seed)
            fig.tight_layout()
            fig.savefig(OUT / f"{name}_{seed}.png", dpi=120)
            np.save(OUT / f"{name}_{seed}.npy", grid, allow_pickle=False)
            plt.close(fig)
        rows = (a.seeds + 1) // 2
        fig, axes = plt.subplots(rows, 2, figsize=(12, rows * 4.5), squeeze=False)
        for seed, ax in enumerate(axes.flat):
            if seed < a.seeds:
                draw(ax, name, seed)
            else:
                ax.axis("off")
        fig.suptitle(
            f"{name}: seeds 0..{a.seeds - 1} | green=start, red=finish, teal=shortest path\n"
            "orange=unreachable floor; four-neighbour movement",
            fontsize=12,
        )
        fig.tight_layout(rect=(0, 0, 1, 0.97))
        fig.savefig(ROOT / "results" / f"gallery_{name}.png", dpi=120)
        plt.close(fig)


if __name__ == "__main__":
    main()
