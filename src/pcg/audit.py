"""Verify committed experiment artifacts against regenerated maps and summary."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

from .stats import GENS
from .validator import components, pick_start, reachable

ROOT = Path(__file__).resolve().parents[2]


def main():
    summary = pd.read_csv(ROOT / "results/summary.csv").set_index("gen")
    assert set(summary.index) == set(GENS)
    total = 0
    for name, generate in GENS.items():
        df = pd.read_csv(ROOT / f"results/stats_{name}.csv")
        assert df.seed.tolist() == list(range(100)), name
        assert df.gen.eq(name).all()
        assert df.gen_ms.ge(0).all()
        for row in df.itertuples():
            grid = generate(seed=row.seed)
            assert hashlib.sha256(grid.tobytes()).hexdigest() == row.sha256, (name, row.seed)
            _, m = reachable(grid, pick_start(grid))
            for key in ["floor_cells", "reached", "reach_ratio", "path_len"]:
                assert np.isclose(getattr(row, key), m[key]), (name, row.seed, key)
            assert row.components == len(components(grid))
            assert np.isclose(row.floor_ratio, (grid == 0).mean())
            assert row.playable == (m["reach_ratio"] >= 0.6 and m["path_len"] >= 20)
            assert row.fully_connected == (m["floor_cells"] > 0 and m["reach_ratio"] == 1)
            if row.seed < 10:
                saved = np.load(ROOT / f"results/levels/{name}_{row.seed}.npy", allow_pickle=False)
                assert np.array_equal(grid, saved)
                assert (ROOT / f"results/levels/{name}_{row.seed}.png").is_file()
            total += 1
        saved_summary = summary.loc[name]
        assert saved_summary["n"] == 100
        assert np.isclose(saved_summary.playable_pct, df.playable.mean() * 100)
        assert np.isclose(saved_summary.fully_connected_pct, df.fully_connected.mean() * 100)
        for key in ["floor_ratio", "reach_ratio", "path_len", "components", "gen_ms"]:
            assert np.isclose(saved_summary[key + "_mean"], df[key].mean())
            assert np.isclose(saved_summary[key + "_std"], df[key].std(ddof=0))
    print(f"OK: {total} grids and CSV rows; 30 NPY/PNG pairs; summary matches measurements")


if __name__ == "__main__":
    main()
