"""Клеточный автомат: случайный шум → N итераций правила B5678/S45678 → пещеры."""

import numpy as np

from . import FLOOR, WALL


def generate(width=64, height=48, seed=0, fill=0.45, iterations=5, birth=5, survive=4) -> np.ndarray:
    if min(width, height) < 3 or not 0 <= fill <= 1 or iterations < 0:
        raise ValueError("dimensions >= 3, fill in [0, 1], iterations >= 0 required")
    if not 0 <= birth <= 8 or not 0 <= survive <= 8:
        raise ValueError("birth and survive must be in [0, 8]")
    rng = np.random.default_rng(seed)
    grid = (rng.random((height, width)) < fill).astype(np.int8)  # 1 = стена
    grid[0, :] = grid[-1, :] = grid[:, 0] = grid[:, -1] = WALL
    for _ in range(iterations):
        padded = np.pad(grid, 1, constant_values=WALL)
        neigh = sum(
            np.roll(np.roll(padded, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)
        )[1:-1, 1:-1]
        grid = np.where(grid == WALL, (neigh >= survive), (neigh >= birth)).astype(np.int8)
        grid[0, :] = grid[-1, :] = grid[:, 0] = grid[:, -1] = WALL
    return np.where(grid == 1, WALL, FLOOR).astype(np.int8)
