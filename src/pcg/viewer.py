"""Interactive pygame view: arrows change seed, Tab changes generator, Esc quits."""

import numpy as np
import pygame

from .stats import GENS
from .validator import pick_start, reachable, shortest_path


def main():
    pygame.init()
    screen = pygame.display.set_mode((1024, 820))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 22)
    names = list(GENS)
    index, seed, dirty = 0, 0, True
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_TAB:
                    index = (index + 1) % len(names)
                    dirty = True
                elif event.key in (pygame.K_RIGHT, pygame.K_LEFT):
                    seed = max(0, seed + (1 if event.key == pygame.K_RIGHT else -1))
                    dirty = True
        if dirty:
            grid = GENS[names[index]](seed=seed)
            dist, m = reachable(grid, pick_start(grid))
            screen.fill("#15283b")
            for y, x in np.argwhere(grid == 0):
                color = "#e5edf0" if dist[y, x] >= 0 else "#f1b98b"
                pygame.draw.rect(screen, color, (x * 16, y * 16, 16, 16))
            path = shortest_path(dist, m["finish"])
            if len(path) > 1:
                pygame.draw.lines(screen, "#31a6a0", False, [(x * 16 + 8, y * 16 + 8) for y, x in path], 3)
                for cell, color in [(path[0], "#15a14a"), (path[-1], "#d62f49")]:
                    y, x = cell
                    pygame.draw.circle(screen, color, (x * 16 + 8, y * 16 + 8), 7)
            text = f"{names[index]} seed={seed} | reach={m['reach_ratio']:.1%} | path={m['path_len']}"
            screen.blit(font.render(text, True, "white"), (12, 770))
            screen.blit(font.render("Left/Right: seed | Tab: generator | Esc: quit", True, "white"), (12, 796))
            pygame.display.flip()
            dirty = False
        clock.tick(30)
    pygame.quit()


if __name__ == "__main__":
    main()
