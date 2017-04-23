import sys
from collections import namedtuple
from functools import lru_cache

MAP_WIDTH = 23
MAP_HEIGHT = 21
COOLDOWN_CANNON = 2
COOLDOWN_MINE = 5
INITIAL_SHIP_HEALTH = 100
MAX_SHIP_HEALTH = 100
MIN_SHIPS = 1
MIN_RUM_BARRELS = 10
MAX_RUM_BARRELS = 26
MIN_RUM_BARREL_VALUE = 10
MAX_RUM_BARREL_VALUE = 20
REWARD_RUM_BARREL_VALUE = 30
MINE_VISIBILITY_RANGE = 5
FIRE_DISTANCE_MAX = 10
LOW_DAMAGE = 25
HIGH_DAMAGE = 50
MINE_DAMAGE = 25
NEAR_MINE_DAMAGE = 10
MAX_SHIPS = 3
CANNONS_ENABLED = True
MINES_ENABLED = True
MIN_MINES = 5
MAX_MINES = 10
MAX_SHIP_SPEED = 2

DEBUG = {"file": sys.stderr, 'flush': True}

debug = False
if debug and debug != 'AG':
    from debugging import *

DIRECTIONS_EVEN = ((1, 0),
                   (0, -1),
                   (-1, -1),
                   (-1, 0),
                   (-1, 1),
                   (0, 1))
DIRECTIONS_ODD = ((1, 0),
                  (1, -1),
                  (0, -1),
                  (-1, 0),
                  (0, 1),
                  (1, 1))


@lru_cache(2 ** 11)
def neighbor(x, y, o):
    if y % 2 == 0:
        dx, dy = DIRECTIONS_EVEN[o]
    else:
        dx, dy = DIRECTIONS_ODD[o]

    return Coord(dx + x, dy + y)


def is_inside_map(point):
    return 0 <= point.x <= 22 and 0 <= point.y <= 20


@lru_cache(2 ** 14)
def distance_to(ax, ay, bx, by):
    if ax < bx:
        return distance_to(bx, by, ax, ay)

    magic = ax - bx + (by - ay + ((ay & 1) - (by & 1))) / 2

    return (abs(magic) + abs(magic + ay - by) + abs(ay - by)) / 2


Coord = namedtuple('P', ['x', 'y'], verbose=False)


class EntityType:
    SHIP = "SHIP"
    BARREL = "BARREL"
    MINE = "MINE"
    CANNONBALL = "CANNONBALL"


class Mine:
    def __init__(self, x, y):
        self.pos = Coord(x, y)

    def __repr__(self):
        return 'M({}, {})'.format(self.pos.x, self.pos.y)

    def explode(self, ships, force):
        victim = None
        exploded = False

        for ship in ships:
            if ship.at(self.pos):
                ship.damage(MINE_DAMAGE)
                exploded = True
                victim = ship

        if force or victim is not None:

            for ship in ships:
                if ship != victim:
                    if distance_to(self.pos.x, self.pos.y, ship.stern.x, ship.stern.y) <= 1 \
                            or distance_to(ship.bow.x, ship.bow.y, self.pos.x, self.pos.y) <= 1 \
                            or distance_to(ship.pos.x, ship.pos.y, self.pos.x, self.pos.y) <= 1:
                        ship.damage(NEAR_MINE_DAMAGE)
                        exploded = True

        return exploded

    def copy(self):
        return Mine(self.pos.x, self.pos.y)


class CannonBall:
    def __init__(self, x, y, remaining_turns):
        self.pos = Coord(x, y)
        self.remaining_turns = remaining_turns

    def __repr__(self):
        return 'CB({}, {}, r{})'.format(self.pos.x, self.pos.y, self.remaining_turns)

    def copy(self):
        return CannonBall(self.pos.x, self.pos.y, self.remaining_turns)


class RumBarrel:
    def __init__(self, x, y, health):
        self.pos = Coord(x, y)
        self.health = health

    def __repr__(self):
        return 'R({}, {}, h{})'.format(self.pos.x, self.pos.y, self.health)

    def copy(self):
        return RumBarrel(self.pos.x, self.pos.y, self.health)


class Action:
    WAIT = 'W'
    FASTER = 'F'
    SLOWER = 'S'
    GAUCHE = 'G'
    DROITE = 'D'
    FIRE = 'B'
    MINE = 'M'

    TRAD = {
        WAIT: "WAIT",
        FASTER: "FASTER",
        SLOWER: "SLOWER",
        GAUCHE: "PORT",
        DROITE: "STARBOARD",
        FIRE: "FIRE",
        MINE: "MINE"
    }

    @staticmethod
    def to_valable(action):
        return Action.TRAD[action]


class Ship:
    def __init__(self, x, y, ori, owner, speed=0, health=INITIAL_SHIP_HEALTH):
        self.pos = Coord(x, y)
        self.stern = neighbor(x, y, (ori + 3) % 6)
        self.bow = neighbor(x, y, ori)

        self.ori = ori
        self.speed = speed
        self.health = health
        self.owner = owner

        self.action = None
        self.target = Coord(-1, -1)
        self.initial_health = 0
        self.new_ori = 0
        self.mine_cooldown = 0
        self.canon_cooldown = 0
        self.new_pos_coord = None
        self.new_bow_coord = None
        self.new_stern_coord = None

    def __repr__(self):
        r = 'Ship({}, speed: {}, ori: {}, rhum: {}'.format(str(self.pos), self.speed, self.ori, self.health)
        r += ' action: {}, new_ori: {}, new_pos: {}, new_bow: {}, new_stern: {}'.format(self.action,
                                                                                        self.new_ori,
                                                                                        self.new_pos_coord,
                                                                                        self.new_bow_coord,
                                                                                        self.new_stern_coord)
        r += ')'
        return r

    def copy(self):
        return Ship(self.pos.x, self.pos.y, self.ori, self.owner, self.speed, self.health)

    def at(self, coord):
        return self.bow == coord or self.stern == coord or self.pos == coord

    def new_bow_intersect(self, ships):
        for ship in ships:
            if ship != self and (self.new_bow_coord == ship.new_bow_coord
                                 or self.new_bow_coord == ship.new_stern_coord
                                 or self.new_bow_coord == ship.new_pos_coord):
                return True
        return False

    def new_pos_intersect(self, ships):
        for p in (self.new_stern_coord, self.new_bow_coord, self.new_pos_coord):
            for ship in ships:
                if ship != self:
                    if p == ship.new_bow_coord or p == ship.new_stern_coord or p == ship.new_pos_coord:
                        return True
        return False

    def heal(self, health):
        self.health += health
        if self.health > MAX_SHIP_HEALTH:
            self.health = MAX_SHIP_HEALTH

    def damage(self, health):
        self.health -= health
        if self.health < 0:
            self.health = 0


class World:
    def __init__(self, my_ship_count, barrels, cannon_balls, mines, my_ships, enemy_ships):
        self.my_ship_count = my_ship_count
        self.barrels = barrels
        self.cannon_balls = cannon_balls
        self.mines = mines
        self.my_ships = my_ships
        self.enemy_ships = enemy_ships

        self.cannon_ball_explosions = []

    def pretty(self):
        return {
            "Barrels :": self.barrels,
            "Cannon balls :": self.cannon_balls,
            "Mines :": self.mines,
            "My ships :": self.my_ships,
            "Enemies :": self.enemy_ships
        }

    def copy(self):
        return World(self.my_ship_count,
                     [b.copy() for b in self.barrels],
                     [b.copy() for b in self.cannon_balls],
                     [m.copy() for m in self.mines],
                     [s.copy() for s in self.my_ships],
                     [s.copy() for s in self.enemy_ships])

    def ships(self):
        return self.my_ships + self.enemy_ships

    def set_actions(self, guy, actions):
        if guy:
            ships = self.my_ships
        else:
            ships = self.enemy_ships
        assert len(ships) == len(actions)

        for i, (action, target) in enumerate(actions):
            ship = ships[i]

            if action == Action.FASTER:
                ship.action = Action.FASTER
            elif action == Action.SLOWER:
                ship.action = Action.SLOWER
            elif action == Action.GAUCHE:
                ship.action = Action.GAUCHE
            elif action == Action.DROITE:
                ship.action = Action.DROITE
            elif action == Action.MINE:
                if MINES_ENABLED:
                    ship.action = Action.MINE
            elif action == Action.WAIT:
                pass
            elif action == Action.FIRE:
                if CANNONS_ENABLED:
                    ship.target = target
                    ship.action = Action.FIRE
            else:
                raise ValueError

    def decrement_rhum(self):
        for ship in self.ships():
            ship.damage(1)

    def update_initial_rum(self):
        for ship in self.ships():
            ship.initial_health = ship.health

    def move_cannonbals(self):
        to_del = []
        for i, ball in enumerate(self.cannon_balls):
            if ball.remaining_turns == 0:
                to_del.append(i)
                continue

            elif ball.remaining_turns > 0:
                ball.remaining_turns -= 1

            if ball.remaining_turns == 0:
                self.cannon_ball_explosions.append(ball.pos)

        for i, key in enumerate(to_del):
            del self.cannon_balls[key - i]

    def apply_actions(self):
        for ship in self.ships():
            if ship.mine_cooldown > 0:
                ship.mine_cooldown -= 1
            if ship.canon_cooldown > 0:
                ship.canon_cooldown -= 1
            ship.new_ori = ship.ori

            if ship.action is not None:
                if ship.action == Action.FASTER:
                    ship.speed = min(MAX_SHIP_SPEED, ship.speed + 1)
                elif ship.action == Action.SLOWER:
                    ship.speed = max(0, ship.speed - 1)
                elif ship.action == Action.GAUCHE:
                    ship.new_ori = (ship.ori + 1) % 6
                elif ship.action == Action.DROITE:
                    ship.new_ori = (ship.ori + 5) % 6
                elif ship.action == Action.MINE:
                    if ship.mine_cooldown == 0:
                        target = neighbor(ship.stern.x, ship.stern.y, (ship.ori + 3) % 6)

                        if is_inside_map(target):
                            cell_free_of_barrels = all(bar.pos != target for bar in self.barrels)
                            cell_free_of_mines = all(bar.pos != target for bar in self.mines)
                            cell_free_of_ships = all(not s.at(target) for s in self.ships() if s != ship)

                            if cell_free_of_barrels and cell_free_of_mines and cell_free_of_ships:
                                ship.mine_cooldown = COOLDOWN_MINE
                                mine = Mine(target.x, target.y)
                                self.mines.append(mine)
                elif ship.action == Action.FIRE:
                    dist = distance_to(ship.bow.x, ship.bow.y, ship.target.x, ship.target.y)
                    travel_time = int(1 + round(dist / 3))
                    self.cannon_balls.append(CannonBall(ship.target.x, ship.target.y, travel_time))

    def check_all_collisions(self):
        for ship in self.ships():

            to_del = []
            for i, barrel in enumerate(self.barrels):
                if ship.at(barrel.pos):
                    ship.heal(barrel.health)
                    to_del.append(i)

            for nb_deleted, key in enumerate(to_del):
                del self.barrels[key - nb_deleted]

        to_del = []
        for nb_deleted, mine in enumerate(self.mines):
            mine_damages = mine.explode(self.ships(), False)

            if mine_damages:
                to_del.append(nb_deleted)

        for nb_deleted, key in enumerate(to_del):
            del self.mines[key - nb_deleted]

    def move_ships(self):
        for i in range(1, MAX_SHIP_SPEED + 1):
            for ship in self.ships():

                ship.new_pos_coord = ship.pos
                ship.new_bow_coord = ship.bow
                ship.new_stern_coord = ship.stern

                if i > ship.speed:
                    continue

                new_coord = neighbor(ship.pos.x, ship.pos.y, ship.ori)

                if is_inside_map(new_coord):
                    ship.new_pos_coord = new_coord
                    ship.new_bow_coord = neighbor(new_coord.x, new_coord.y, ship.ori)
                    ship.new_stern_coord = neighbor(new_coord.x, new_coord.y, (ship.ori + 3) % 6)
                else:
                    # stop ship
                    ship.speed = 0

            if debug == 'MOVE':
                step('COLI', 1)
                pprint(self.pretty())

            # Check ship and obstacles collisions
            collisions = []
            collision_detected = True
            while collision_detected:
                collision_detected = False
                for ship in self.ships():
                    if ship.new_bow_intersect(self.ships()):
                        collisions.append(ship)

                for ship in collisions:
                    # revert last move
                    ship.new_pos_coord = ship.pos
                    ship.new_bow_coord = ship.bow
                    ship.new_stern_coord = ship.stern

                    # stop ships
                    ship.speed = 0

                    collision_detected = True
                collisions.clear()

            # move ships to their new location
            for ship in self.ships():
                ship.pos = ship.new_pos_coord
                ship.stern = neighbor(ship.pos.x, ship.pos.y, (ship.ori + 3) % 6)
                ship.bow = neighbor(ship.pos.x, ship.pos.y, ship.ori)

            # check mines / rhum
            self.check_all_collisions()

    def rotate_ships(self):

        if debug == 'ROTATE':
            step('ENTRY', 1)
            pprint(self.ships())

        # rotate
        for ship in self.ships():
            ship.new_pos_coord = ship.pos
            ship.new_bow_coord = neighbor(ship.pos.x, ship.pos.y, ship.new_ori)
            ship.new_stern_coord = neighbor(ship.pos.x, ship.pos.y, (ship.new_ori + 3) % 6)

        if debug == 'ROTATE':
            step('COLISION CHECK', 1)
            pprint(self.ships())

        # check collisions
        collision_detected = True
        collisions = []
        while collision_detected:
            collision_detected = False

            for ship in self.ships():
                if ship.new_pos_intersect(self.ships()):
                    collisions.append(ship)

            for ship in collisions:
                ship.new_ori = ship.ori
                ship.new_bow_coord = neighbor(ship.pos.x, ship.pos.y, ship.new_ori)
                ship.new_stern_coord = neighbor(ship.pos.x, ship.pos.y, (ship.new_ori + 3) % 6)
                ship.speed = 0
                collision_detected = True
            collisions.clear()

        if debug == 'ROTATE':
            step('COLI END', 1)
            pprint(self.ships())

        # apply rotation
        for ship in self.ships():
            ship.ori = ship.new_ori
            ship.bow = ship.new_bow_coord
            ship.stern = ship.new_stern_coord

        # check mines / rhum
        self.check_all_collisions()

        if debug == 'ROTATE':
            step('EXIT', 1)
            pprint(self.ships())

    def game_is_over(self):
        return not (self.enemy_ships and self.my_ships)

    def explode_ships(self):
        to_del = []
        for i, pos in enumerate(self.cannon_ball_explosions):
            for ship in self.ships():
                if pos == ship.bow or pos == ship.stern:
                    ship.damage(LOW_DAMAGE)
                    to_del.append(i)
                    break
                elif pos == ship.pos:
                    ship.damage(HIGH_DAMAGE)
                    to_del.append(i)
                    break

        for i, key in enumerate(to_del):
            del self.cannon_ball_explosions[key - i]

    def explode_mines(self):
        to_del_booms = []
        to_del_mines = []
        for i, pos in enumerate(self.cannon_ball_explosions):
            for j, mine in enumerate(self.mines):
                if pos == mine.pos:
                    mine.explode(self.ships(), True)
                    to_del_booms.append(i)
                    to_del_mines.append(j)
                    break

        for i, key in enumerate(to_del_booms):
            del self.cannon_ball_explosions[key - i]
        for i, key in enumerate(to_del_mines):
            del self.mines[key - i]

    def explode_barrels(self):

        to_del_boom = []

        for i, pos in enumerate(self.cannon_ball_explosions):
            miam_boom = None
            for j, rum in enumerate(self.barrels):
                if pos == rum.pos:
                    to_del_boom.append(i)
                    miam_boom = j
                    break

            if miam_boom is not None:
                del self.barrels[miam_boom]

        for i, key in enumerate(to_del_boom):
            del self.cannon_balls[key - i]

    def prepare(self):
        self.my_ship_count = len(self.my_ships)
        for ship in self.ships():
            ship.action = None
        self.cannon_ball_explosions.clear()

    def update(self):

        self.move_cannonbals()
        self.decrement_rhum()
        self.update_initial_rum()

        self.apply_actions()
        self.move_ships()
        self.rotate_ships()

        self.explode_ships()
        self.explode_mines()
        self.explode_barrels()

        # For each sunk ship, create a new rum barrel with the amount of rum
        # the ship had at the begin of the turn (up to 30).
        for ship in self.ships():
            if ship.health <= 0:
                if ship.initial_health > REWARD_RUM_BARREL_VALUE:
                    reward = REWARD_RUM_BARREL_VALUE
                else:
                    reward = ship.initial_health

                if reward > 0:
                    self.barrels.append(RumBarrel(ship.pos.x, ship.pos.y, reward))

        to_del = []
        for i, ship in enumerate(self.my_ships):
            if ship.health <= 0:
                if debug == 'SINK':
                    print(blue(ship))
                to_del.append(i)
        for i, key in enumerate(to_del):
            del self.my_ships[key - i]

        to_del.clear()
        for i, ship in enumerate(self.enemy_ships):
            if ship.health <= 0:
                to_del.append(i)
        for i, key in enumerate(to_del):
            del self.enemy_ships[key - i]

        if self.game_is_over():
            return 'Game over'


def get_world():
    rhum = []
    mines = []
    cannons = []
    ships_0 = []
    ships_1 = []
    ships = [ships_0, ships_1]


    my_ship_count = int(input())  # the number of remaining ships
    entity_count = int(input())  # the number of entities (e.g. ships, mines or cannonballs)
    for i in range(entity_count):
        entity_id, entity_type, x, y, arg_1, arg_2, arg_3, arg_4 = input().split()
        entity_id = int(entity_id)
        x = int(x)
        y = int(y)
        arg_1 = int(arg_1)
        arg_2 = int(arg_2)
        arg_3 = int(arg_3)
        arg_4 = int(arg_4)

        if entity_type == EntityType.BARREL:
            rhum.append(RumBarrel(x, y, arg_1))
        elif entity_type == EntityType.CANNONBALL:
            cannons.append(CannonBall(x, y, arg_2))
        elif entity_type == EntityType.MINE:
            mines.append(Mine(x, y))
        elif entity_type == EntityType.SHIP:
            ships[arg_4].append(Ship(x, y, arg_1, arg_4, arg_2, arg_3))

    world = World(my_ship_count, rhum, cannons, mines, ships_1, ships_0)
    return world


mode = None
from random import randrange


def get_random_world():
    my_ships = []
    my_ship_count = randrange(1, 4)
    en_ships = []
    en_ship_count = randrange(1, 4)
    mines = []
    nb_mines = randrange(15)
    barrels = []
    nb_barrel = randrange(20)
    canon_balls = []
    nb_canon_bals = randrange(20)

    used_cases = [[0 for y in range(21)] for x in range(23)]

    # generate de mémoir ilk
    nb = 0
    while nb < my_ship_count + en_ship_count:
        ship = Ship(randrange(1, 22), randrange(1, 20), randrange(6), 1, randrange(3), randrange(1, 101))

        # verify if there's something where the ship is
        bow = neighbor(ship.pos.x, ship.pos.y, ship.ori)
        stern = neighbor(ship.pos.x, ship.pos.y, (ship.ori + 3) % 6)
        if used_cases[bow.x][bow.y] or used_cases[ship.pos.x][ship.pos.y] or used_cases[stern.x][stern.y]:
            # if there can't be a ship here : try another
            continue

        # occupy his cases
        used_cases[bow.x][bow.y] = 1
        used_cases[ship.pos.x][ship.pos.y] = 1
        used_cases[stern.x][stern.y] = 1

        # add it
        if nb < my_ship_count:
            my_ships.append(ship)
        else:
            en_ships.append(ship)
        nb += 1

    # generate mine
    nb = 0
    while nb < nb_mines:

        # verify case is empty
        mine = Mine(randrange(23), randrange(21))
        if used_cases[mine.pos.x][mine.pos.y]:
            continue

        nb += 1

        # add mine and occupy case
        used_cases[mine.pos.x][mine.pos.y] = 1
        mines.append(mine)

    nb = 0
    while nb < nb_barrel:
        rum = RumBarrel(randrange(23), randrange(21), randrange(10, 21))

        if used_cases[rum.pos.x][rum.pos.y]:
            continue

        nb += 1

        used_cases[rum.pos.x][rum.pos.y] = 1
        barrels.append(rum)

    nb = 0
    while nb < nb_canon_bals:
        boom = CannonBall(randrange(23), randrange(21), randrange(5))

        nb += 1

        # no test for empty case : bullet are over the see
        canon_balls.append(boom)

    return World(my_ship_count, barrels, canon_balls, mines, my_ships, en_ships)
