from debugging import *
from referee import World, Action, get_world, Ship


def move_simple():
    w = World(1, [], [], [], [Ship(5, 5, 0, 1, 1, 1)],
              [Ship(10, 10, 0, 2, 1, 0), Ship(15, 15, 0, 1, 2, 2)])

    step("START")
    pprint(w.pretty())

    a = [(Action.WAIT, 0)]
    w.set_actions(0, a * 2)
    w.set_actions(1, a)
    w.update()

    step("END")
    pprint(w.pretty())


def rotate_simple():
    w = World(1, [], [], [], [Ship(5, 5, 0, 1, 1, speed=2)],
              [Ship(10, 5, 3, 2, 1, speed=2)])
    w.prepare()

    step("START")
    pprint(w.pretty())

    a = [(Action.DROITE, 0)]
    b = [(Action.GAUCHE, 0)]
    w.set_actions(0, b)
    w.set_actions(1, a)

    w.update()

    step("END")
    pprint(w.pretty())

# move_simple()
rotate_simple()