"""Connect CA components in deterministic order using L-shaped corridors."""

from . import FLOOR
from .cellular import generate as raw_generate
from .validator import components


def connect_components(grid):
    result = grid.copy()
    groups = components(result)
    if not groups:
        result[1:-1, 1:-1] = FLOOR
        return result
    anchor = max(groups, key=len)[0]
    for group in groups:
        y1, x1 = anchor
        y2, x2 = group[0]
        result[y1, min(x1, x2) : max(x1, x2) + 1] = FLOOR
        result[min(y1, y2) : max(y1, y2) + 1, x2] = FLOOR
    return result


def generate(**kwargs):
    return connect_components(raw_generate(**kwargs))
