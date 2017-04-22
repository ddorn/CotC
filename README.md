# CotC
Code for CondinGame


### Utilisation

```
world = get_world()
actions = [(Action.WAIT, None), (Action.FIRE, Coord(5, 9)]  # list of tuples (action, target)
world.prepare()
world.set_actions(0, actions)  # adds actions for the ennemy
world.set_actions(1, actions)  # adds actions for you
world.update()  # simulate the turn
```