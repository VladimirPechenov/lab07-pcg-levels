"""Measured experiment: each seed is generated once, timings exclude validation."""

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd

from . import FLOOR, bsp, cellular, repair
from .validator import components, pick_start, reachable

GENS = {"bsp": bsp.generate, "ca": cellular.generate, "ca_connected": repair.generate}
OUT = Path(__file__).resolve().parents[2] / "results"


def run(gen, n):
    if n < 1:
        raise ValueError("n must be positive")
    rows = []
    for seed in range(n):
        t = time.perf_counter_ns()
        grid = GENS[gen](seed=seed)
        elapsed = (time.perf_counter_ns() - t) / 1e6
        start = pick_start(grid)
        _, m = reachable(grid, start)
        rows.append(
            {
                "gen": gen,
                "seed": seed,
                "gen_ms": elapsed,
                "floor_ratio": float((grid == FLOOR).mean()),
                "floor_cells": m["floor_cells"],
                "reached": m["reached"],
                "reach_ratio": m["reach_ratio"],
                "path_len": m["path_len"],
                "components": len(components(grid)),
                "start": str(start),
                "finish": str(m["finish"]),
                "playable": m["reach_ratio"] >= 0.6 and m["path_len"] >= 20,
                "fully_connected": m["floor_cells"] > 0 and m["reach_ratio"] == 1.0,
                "sha256": hashlib.sha256(grid.tobytes()).hexdigest(),
            }
        )
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", choices=[*GENS, "all"], default="all")
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    names = list(GENS) if a.gen == "all" else [a.gen]
    summary = []
    for name in names:
        df = run(name, a.n)
        df.to_csv(OUT / f"stats_{name}.csv", index=False)
        row = {
            "gen": name,
            "n": a.n,
            "playable_pct": 100 * df.playable.mean(),
            "fully_connected_pct": 100 * df.fully_connected.mean(),
        }
        for col in ["floor_ratio", "reach_ratio", "path_len", "components", "gen_ms"]:
            row[col + "_mean"] = df[col].mean()
            row[col + "_std"] = df[col].std(ddof=0)
        summary.append(row)
    pd.DataFrame(summary).to_csv(OUT / "summary.csv", index=False)
    manifest = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "n": a.n,
        "seeds": f"0..{a.n - 1}",
        "width": 64,
        "height": 48,
        "bsp": {"min_leaf": 10, "depth": 5, "min_room": 4},
        "ca": {"fill": 0.45, "iterations": 5, "birth": 5, "survive": 4},
        "playable": {"min_reach": 0.6, "min_path": 20},
        "std_ddof": 0,
        "timing": "perf_counter_ns; generation only; CA-connected includes repair; no warmup",
    }
    (OUT / "experiment.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(pd.DataFrame(summary).to_string(index=False))


if __name__ == "__main__":
    main()
