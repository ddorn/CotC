import sys

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


class Coord:
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

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def to_cube(self):
        x = self.x
        y = self.y

        xp = x - (y - (y & 1)) / 2
        zp = y
        yp = -(xp + zp)

        return Cube(xp, yp, zp)

    def neighbor(self, orientation):
        if self.y & 1:
            dx, dy = Coord.DIRECTIONS_ODD[orientation]
        else:
            dx, dy = Coord.DIRECTIONS_EVEN[orientation]
        return Coord(self.x + dx, self.y + dy)

    def is_inside_map(self):
        return 0 <= self.x <= 22 and 0 <= self.y <= 20

    def distance_to(self, other):
        return self.to_cube().distance_to(other.to_cube())

    def __eq__(self, other):
        if other is None:
            return False
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return 'P({}, {})'.format(self.x, self.y)


class Cube:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def distance_to(self, other):
        return (abs(self.x - other.x) + abs(self.y - other.y) + abs(self.z - other.z)) / 2

    def __str__(self):
        return 'C({}, {}, {})'.format(self.x, self.y, self.z)


class EntityType:
    SHIP = "SHIP"
    BARREL = "BARREL"
    MINE = "MINE"
    CANNONBALL = "CANNONBALL"


class Entity:
    def __init__(self, type, x, y):
        self.type = type
        self.pos = Coord(x, y)


class Mine(Entity):
    def __init__(self, x, y):
        super().__init__(EntityType.MINE, x, y)

    def __repr__(self):
        return 'M({}, {})'.format(self.pos.x, self.pos.y)

    def explode(self, ships, force):
        victim = None

        for ship in ships:
            if self.pos == ship.bow() or self.pos == ship.stern() or self.pos == ship.pos:
                ship.damage(MINE_DAMAGE)
                victim = ship

        if force or victim is not None:

            for ship in ships:
                if ship != victim:
                    if ship.stern().distance_to(self.pos) <= 1 or ship.bow().distance_to(
                            self.pos) <= 1 or ship.pos.distance_to(self.pos) <= 1:
                        ship.damage(NEAR_MINE_DAMAGE)

    def copy(self):
        return Mine(self.pos.x, self.pos.y)


class CannonBall(Entity):
    def __init__(self, x, y, remaining_turns):
        super().__init__(EntityType.CANNONBALL, x, y)
        self.remaining_turns = remaining_turns

    def __repr__(self):
        return 'CB({}, {}, r{})'.format(self.pos.x, self.pos.y, self.remaining_turns)

    def copy(self):
        return CannonBall(self.pos.x, self.pos.y, self.remaining_turns)


class RumBarrel(Entity):
    def __init__(self, x, y, health):
        super().__init__(EntityType.BARREL, x, y)
        self.health = health

    def __repr__(self):
        return 'R({}, {}, h{})'.format(self.pos.x, self.pos.y, self.health)

    def copy(self):
        return RumBarrel(self.pos.x, self.pos.y, self.health)


class Action:
    WAIT = "WAIT"
    FASTER = "FASTER"
    SLOWER = "SLOWER"
    GAUCHE = "PORT"
    DROITE = "STARBOARD"
    FIRE = "FIRE"
    MINE = "MINE"


class Ship(Entity):
    def __init__(self, x, y, ori, owner, id, speed=0, health=INITIAL_SHIP_HEALTH):
        super().__init__(EntityType.SHIP, x, y)
        self.id = id
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
        return Ship(self.pos.x, self.pos.y, self.ori, self.owner, self.id, self.speed, self.health)

    def stern(self):
        return self.pos.neighbor((self.ori + 3) % 6)

    def bow(self):
        return self.pos.neighbor(self.ori)

    def at(self, coord):
        return self.bow() == coord or self.stern() == coord or self.pos == coord

    def new_bow_intersect(self, ships):
        return any(ship.at(self.new_bow_coord) for ship in ships if ship != self)

    def new_pos_intersect(self, ships):
        for p in (self.new_stern_coord, self.new_bow_coord, self.pos):
            for ship in ships:
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

    @property
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
        for ship in self.ships:
            ship.damage(1)

    def update_initial_rum(self):
        for ship in self.ships:
            ship.initial_health = ship.health

    def move_cannonbals(self):
        for ball in self.cannon_balls[:]:
            if ball.remaining_turns == 0:
                self.cannon_balls.remove(ball)
                continue

            elif ball.remaining_turns > 0:
                ball.remaining_turns -= 1

            if ball.remaining_turns == 0:
                self.cannon_ball_explosions.append(ball.pos)

    def apply_actions(self):
        for ship in self.ships:
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
                        target = ship.stern().neighbor((ship.ori + 3) % 6)

                        if target.is_inside_map():
                            cell_free_of_barrels = all(bar.pos != target for bar in self.barrels)
                            cell_free_of_mines = all(bar.pos != target for bar in self.mines)
                            cell_free_of_ships = all(not s.at(target) for s in self.ships if s != ship)

                            if cell_free_of_barrels and cell_free_of_mines and cell_free_of_ships:
                                ship.mine_cooldown = COOLDOWN_MINE
                                mine = Mine(target.x, target.y)
                                self.mines.append(mine)
                elif ship.action == Action.FIRE:
                    dist = ship.bow().distance_to(ship.target)
                    travel_time = int(1 + round(dist / 3))
                    self.cannon_balls.append(CannonBall(ship.target.x, ship.target.y, travel_time))

    def check_collisions(self, ship):
        for barrel in self.barrels[:]:
            if ship.at(barrel.pos):
                ship.heal(barrel.health)
                self.barrels.remove(barrel)

        for mine in self.mines[:]:
            mine_damages = mine.explode(self.ships, False)

            if mine_damages:
                mine.remove(mine)

    def move_ships(self):
        for i in range(1, MAX_SHIP_SPEED + 1):
            for ship in self.ships:

                ship.new_pos_coord = ship.pos
                ship.new_bow_coord = ship.bow()
                ship.new_stern_coord = ship.stern()

                if i > ship.speed:
                    continue

                new_coord = ship.pos.neighbor(ship.ori)

                if new_coord.is_inside_map():
                    ship.new_pos_coord = new_coord
                    ship.new_bow_coord = new_coord.neighbor(ship.ori)
                    ship.new_stern_coord = new_coord.neighbor((ship.ori + 3) % 6)
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
                for ship in self.ships:
                    if ship.new_bow_intersect(self.ships):
                        collisions.append(ship)

                for ship in collisions:
                    # revert last move
                    ship.new_pos_coord = ship.pos
                    ship.new_bow_coord = ship.bow()
                    ship.new_stern_coord = ship.stern()

                    # stop ships
                    ship.speed = 0

                    collision_detected = True
                collisions.clear()

            # move ships to their new location
            for ship in self.ships:
                ship.pos = ship.new_pos_coord

            # check mines / rhum
            for ship in self.ships:
                self.check_collisions(ship)

    def rotate_ships(self):

        if debug == 'ROTATE':
            step('ENTRY', 1)
            pprint(self.ships)

        # rotate
        for ship in self.ships:
            ship.new_bow_coord = ship.pos.neighbor(ship.new_ori)
            ship.new_stern_coord = ship.pos.neighbor((ship.new_ori + 3) % 6)

        if debug == 'ROTATE':
            step('COLISION CHECK', 1)
            pprint(self.ships)

        # check collisions
        collision_detected = True
        collisions = []
        while collision_detected:
            collision_detected = False

            for ship in self.ships:
                if ship.new_pos_intersect(self.ships):
                    collisions.append(ship)

            for ship in collisions:
                ship.new_ori = ship.ori
                ship.new_bow_coord = ship.pos.neighbor(ship.new_ori)
                ship.new_stern_coord = ship.pos.neighbor((ship.new_ori + 3) % 6)
                ship.speed = 0
                collision_detected = True
            collisions.clear()

        if debug == 'ROTATE':
            step('COLI END', 1)
            pprint(self.ships)

        # apply rotation
        for ship in self.ships:
            ship.ori = ship.new_ori

        # check mines / rhum
        for ship in self.ships:
            self.check_collisions(ship)

        if debug == 'ROTATE':
            step('EXIT', 1)
            pprint(self.ships)

    def game_is_over(self):
        return not (self.enemy_ships and self.my_ships)

    def explode_ships(self):
        for pos in self.cannon_ball_explosions[:]:
            for ship in self.ships:
                if pos == ship.bow() or pos == ship.stern():
                    ship.damage(LOW_DAMAGE)
                    self.cannon_ball_explosions.remove(pos)
                    break
                elif pos == ship.pos:
                    ship.damage(HIGH_DAMAGE)
                    self.cannon_ball_explosions.remove(pos)
                    break

    def explode_mines(self):

        for pos in self.cannon_ball_explosions[:]:
            for mine in self.mines[:]:
                if pos == mine.pos:
                    mine.explode(self.ships, True)
                    self.cannon_ball_explosions.remove(pos)
                    self.mines.remove(mine)
                    break

    def explode_barrels(self):

        for pos in self.cannon_ball_explosions[:]:
            for rum in self.barrels[:]:
                if pos == rum.pos:
                    self.cannon_ball_explosions.remove(pos)
                    self.barrels.remove(rum)
                    break

    def prepare(self):
        for ship in self.my_ships + self.enemy_ships:
            ship.action = None
        self.cannon_ball_explosions.clear()

    def update(self):
        if debug == 'AG':
            global SIMULS
            SIMULS += 1
            print('SIMUATION', **DEBUG)

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
        for ship in self.ships:
            if ship.health <= 0:
                if ship.initial_health > REWARD_RUM_BARREL_VALUE:
                    reward = REWARD_RUM_BARREL_VALUE
                else:
                    reward = ship.initial_health

                if reward > 0:
                    self.barrels.append(RumBarrel(ship.pos.x, ship.pos.y, reward))

        for ship in self.my_ships[:]:
            if ship.health <= 0:
                if debug == 'SINK':
                    print(blue(ship))
                self.my_ships.remove(ship)

        for ship in self.enemy_ships[:]:
            if ship.health <= 0:
                self.enemy_ships.remove(ship)

        if self.game_is_over():
            raise InterruptedError('End reached')


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
            ships[arg_4].append(Ship(x, y, arg_1, arg_4, entity_id, arg_2, arg_3))

    world = World(my_ship_count, rhum, cannons, mines, ships_1, ships_0)
    return world


profile = False
if profile:
    from random import choice
    import copy

    actions = [Action.WAIT, Action.FASTER, Action.SLOWER, Action.GAUCHE, Action.DROITE, Action.FIRE]
    for _ in range(5):
        world = get_world()
        for sim in range(20):
            w = copy.deepcopy(world)
            for i in range(20):
                w.prepare()
                w.set_actions(0, [(choice(actions), Coord(-1, -1)) for _ in range(len(w.enemy_ships))])
                w.set_actions(1, [(choice(actions), Coord(-1, -1)) for _ in range(len(w.my_ships))])
                try:
                    w.update()
                except InterruptedError:
                    print('PERDU')
                    break
                # print(w.pretty())
