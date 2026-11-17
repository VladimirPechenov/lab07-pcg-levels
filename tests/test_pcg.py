import numpy as np
import pytest

from pcg import bsp, cellular, repair
from pcg.stats import GENS, run
from pcg.validator import components, is_playable, pick_start, reachable, shortest_path


@pytest.mark.parametrize("gen", GENS.values())
@pytest.mark.parametrize("seed", [0, 7, 42, 99])
def test_determinism_and_local_rng(gen, seed):
    original = gen(seed=seed)
    gen(seed=seed + 1)
    np.random.seed(1337)
    assert np.array_equal(original, gen(seed=seed))
    assert original.shape == (48, 64)
    assert set(np.unique(original)) <= {0, 1}
    assert np.all(original[[0, -1], :] == 1)
    assert np.all(original[:, [0, -1]] == 1)


@pytest.mark.parametrize("gen", GENS.values())
def test_diversity(gen):
    assert not np.array_equal(gen(seed=7), gen(seed=8))


@pytest.mark.parametrize("gen", [bsp.generate, repair.generate])
def test_connected_on_100_seeds(gen):
    for seed in range(100):
        grid = gen(seed=seed)
        assert len(components(grid)) == 1
        assert is_playable(grid, min_reach=1.0)


def test_bfs_hand_computed_map_and_path():
    grid = np.array([[1, 1, 1, 1, 1], [1, 0, 0, 1, 1], [1, 1, 0, 1, 1], [1, 0, 1, 0, 1], [1, 1, 1, 1, 1]])
    dist, m = reachable(grid, (1, 1))
    assert m["floor_cells"] == 5 and m["reached"] == 3
    assert m["reach_ratio"] == 0.6 and m["path_len"] == 2 and m["finish"] == (2, 2)
    assert len(components(grid)) == 3
    assert shortest_path(dist, m["finish"]) == [(1, 1), (1, 2), (2, 2)]
    assert is_playable(grid, min_reach=0.6, min_path=2)
    assert not is_playable(grid, min_reach=0.61, min_path=2)


@pytest.mark.parametrize("start", [None, (0, 0)])
def test_all_walls(start):
    grid = np.ones((5, 5), dtype=np.int8)
    assert pick_start(grid) is None
    _, m = reachable(grid, start)
    assert m["reached"] == 0 and m["finish"] is None
    assert not is_playable(grid)


def test_ca_exact_one_step_rule():
    width, height, seed = 9, 8, 7
    original = (np.random.default_rng(seed).random((height, width)) < 0.45).astype(np.int8)
    original[0, :] = original[-1, :] = original[:, 0] = original[:, -1] = 1
    expected = np.ones_like(original)
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            count = int(original[y - 1 : y + 2, x - 1 : x + 2].sum()) - int(original[y, x])
            expected[y, x] = count >= (4 if original[y, x] else 5)
    assert np.array_equal(expected, cellular.generate(width, height, seed, iterations=1))


def test_repair_preserves_floor_and_input():
    grid = cellular.generate(seed=7)
    before = grid.copy()
    fixed = repair.connect_components(grid)
    assert np.array_equal(grid, before)
    assert np.all(fixed[grid == 0] == 0)
    assert len(components(fixed)) == 1


@pytest.mark.parametrize(
    "gen,kwargs",
    [
        (bsp.generate, {"width": 5}),
        (bsp.generate, {"min_leaf": 5}),
        (cellular.generate, {"fill": 2}),
        (cellular.generate, {"iterations": -1}),
    ],
)
def test_invalid_parameters(gen, kwargs):
    with pytest.raises(ValueError):
        gen(**kwargs)


def test_stats_empty_ca_and_seed_accounting():
    assert not is_playable(cellular.generate(fill=1))
    frame = run("bsp", 3)
    assert frame.seed.tolist() == [0, 1, 2]
    assert frame.gen_ms.ge(0).all()
    assert frame.sha256.nunique() == 3
