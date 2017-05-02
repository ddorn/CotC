import pygame
from _dummy_thread import start_new_thread
from collections import deque
from pygame import gfxdraw
from pygame.locals import *

from referee_opti import *

mode = 'graphics'

from v9_AG import *
from debugging import *
from math import pi, sqrt, cos, sin

pygame.init()
pygame.key.set_repeat(500, 50)

GRID_SIZE = 20
HEXA_WIDTH = sqrt(3) / 2 * GRID_SIZE
SCREEN_SIZE = (int(HEXA_WIDTH * 23.5 * 2 + 1 + 0), int(GRID_SIZE * 43 * 3 / 4))


# colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY_75 = (64, 64, 64)
GREY_25 = (192, 192, 192)
GREY_10 = (220, 220, 220)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
DK_GREEN = (0, 100, 0)
DK_RED = (100, 0, 0)
ORANGE = (255, 128, 20)

FONT = pygame.font.Font('segoeuil.ttf', 20)
SMALL_FONT = pygame.font.Font('segoeuil.ttf', 12)

screen = pygame.display.set_mode(SCREEN_SIZE)
worlds = [get_random_world()]


def to_screen_coord(pos):
    x, y = pos
    if y & 1:  #impair
        new_x = HEXA_WIDTH * 2 * (x + 1)
    else:
        new_x = HEXA_WIDTH + x * 2 * HEXA_WIDTH
    new_y = GRID_SIZE + 2 * y * GRID_SIZE * 3 / 4

    return (new_x, new_y)


def draw_hex(screen, pos, color=BLACK, fill=True, info=None):
    screen_pos = to_screen_coord(pos)

    points = []
    for i in range(6):
        angle_deg = 60 * i + 30
        angle_rad = pi / 180 * angle_deg
        point = (screen_pos[0] + GRID_SIZE * cos(angle_rad),
                 screen_pos[1] + GRID_SIZE * sin(angle_rad))
        points.append(point)

    if fill:
        gfxdraw.filled_polygon(screen, points, color)
    gfxdraw.aapolygon(screen, points, color)


    if info is not None:
        # dist to (5, 5)
        dist_text = FONT.render(str(info), True, BLACK)
        dist_rect = dist_text.get_rect()
        dist_rect.center = screen_pos
        screen.blit(dist_text, dist_rect)


def draw_grid(screen):
    for x in range(23):
        for y in range(21):
            draw_hex(screen, Coord(x, y), BLACK, False)


def draw_circle(screen, pos, color=RED, size=10, fill=True, info=None):
    screen_pos = to_screen_coord(pos)
    x = int(screen_pos[0])
    y = int(screen_pos[1])

    if fill:
        gfxdraw.filled_circle(screen, x, y, size, color)
    gfxdraw.aacircle(screen, x, y, size, color)

    if info is not None:
        # dist to (5, 5)
        dist_text = SMALL_FONT.render(str(info), True, BLACK)
        dist_rect = dist_text.get_rect()
        dist_rect.center = x, y
        screen.blit(dist_text, dist_rect)


def draw_world(screen, world: World):
    for ship in world.my_ships:
        draw_hex(screen, ship.pos, GREEN, info=ship.health)
        draw_hex(screen, ship.stern, GREEN, info=ship.health)
        draw_hex(screen, ship.bow, DK_GREEN, info=ship.speed)


    for ship in world.enemy_ships:
        draw_hex(screen, ship.pos, RED, info=ship.health)
        draw_hex(screen, ship.stern, RED, info=ship.health)
        draw_hex(screen, ship.bow, DK_RED, info=ship.speed)

    for mine in world.mines:
        draw_hex(screen, mine.pos, GREY_25)

    for barrel in world.barrels:
        draw_hex(screen, barrel.pos, BLUE, info=barrel.health)

    for boom in world.cannon_balls:
        if boom.remaining_turns != 0:
            draw_circle(screen, boom.pos, ORANGE, GRID_SIZE//2, 1, boom.remaining_turns)


def main():
    global new_world

    histo_pos = 0

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == QUIT:
                run = False

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    run = False

                if event.key == K_LEFT:
                    if histo_pos > 0:
                        histo_pos -= 1

                if event.key == K_RIGHT:
                    if histo_pos < len(worlds) - 1:
                        histo_pos += 1

                    else:
                        new_world = worlds[-1].copy()

                        en_actions = [(Action.FASTER, None) for _ in new_world.enemy_ships]
                        my_actions = [(Action.DROITE, None) for _ in new_world.my_ships]

                        new_world.prepare()
                        new_world.set_actions(0, en_actions)
                        new_world.set_actions(1, my_actions)

                        new_world.update()

                        worlds.append(new_world)

                        histo_pos = len(worlds) - 1

                if event.key == K_r:
                    worlds.clear()
                    worlds.append(get_random_world())
                    histo_pos = 0

        screen.fill(WHITE)
        draw_grid(screen)
        draw_world(screen, worlds[histo_pos])
        pygame.display.flip()

if __name__ == '__main__':
    main()
else:
    start_new_thread(main, tuple())