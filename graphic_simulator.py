import pygame
from _dummy_thread import start_new_thread
from pygame import gfxdraw
from pygame.locals import *
from referee_opti import *
from debugging import *
from math import pi, sqrt, cos, sin


GRID_SIZE = 15
HEXA_WIDTH = sqrt(3) / 2 * GRID_SIZE
SCREEN_SIZE = (int(HEXA_WIDTH * 24 * 2), int(GRID_SIZE * 3 / 4 * 22 * 2))


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


screen = pygame.display.set_mode(SCREEN_SIZE)
world_to_draw = get_random_world()
last_world = get_random_world()

def to_screen_coord(pos):
    x, y = pos
    if y & 1:  #impair
        new_x = HEXA_WIDTH * 2 * (x + 1)
    else:
        new_x = HEXA_WIDTH + x * 2 * HEXA_WIDTH
    new_y = GRID_SIZE + 2 * y * GRID_SIZE * 3 / 4

    return (new_x, new_y)


def draw_hex(screen, pos, color=BLACK, fill=True):
    pos = to_screen_coord(pos)

    points = []
    for i in range(6):
        angle_deg = 60 * i + 30
        angle_rad = pi / 180 * angle_deg
        point = (pos[0] + GRID_SIZE * cos(angle_rad),
                 pos[1] + GRID_SIZE * sin(angle_rad))
        points.append(point)

    if fill:
        gfxdraw.filled_polygon(screen, points, color)
    gfxdraw.aapolygon(screen, points, color)


def draw_grid(screen):
    for x in range(23):
        for y in range(21):
            draw_hex(screen, Coord(x, y), BLACK, False)


def update(world):
    global world_to_draw, last_world

    last_world = world_to_draw
    world_to_draw = world
    pprint(world.pretty())


def draw_world(screen, world: World):
    for ship in world.my_ships:
        draw_hex(screen, ship.pos, GREEN)
        draw_hex(screen, ship.stern, GREEN)
        draw_hex(screen, ship.bow, DK_GREEN)

    for ship in world.enemy_ships:
        draw_hex(screen, ship.pos, RED)
        draw_hex(screen, ship.stern, RED)
        draw_hex(screen, ship.bow, DK_RED)

    for mine in world.mines:
        draw_hex(screen, mine.pos, GREY_25)

    for barrel in world.barrels:
        draw_hex(screen, barrel.pos, BLUE)


def main():
    global last_world, world_to_draw
    
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == QUIT:
                run = False

            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    run = False

                if event.key == K_r:
                    update(get_random_world())

                if event.key == K_u:
                    last_world = world_to_draw.copy()

                    en_actions = [(Action.FASTER, None) for _ in world_to_draw.enemy_ships]
                    my_actions = [(Action.DROITE, None) for _ in world_to_draw.my_ships]

                    world_to_draw.prepare()
                    world_to_draw.set_actions(0, en_actions)
                    world_to_draw.set_actions(1, my_actions)
                    try:
                        world_to_draw.update()
                    except InterruptedError:
                        print('DEAD')

                if event.key == K_l:
                    last_world, world_to_draw = world_to_draw, last_world

        screen.fill(WHITE)
        draw_grid(screen)
        draw_world(screen, world_to_draw)
        pygame.display.flip()

if __name__ == '__main__':
    main()
else:
    start_new_thread(main, tuple())