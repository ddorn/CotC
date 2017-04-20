# CotC
Code for CondinGame

### There's a bug, but I dont know where...
World.move_ships ?


### Utilisation

```
world = get_world()
actions = [(Action.Wait, None), (Action.Fire, Coord(5, 9)]  # list of tuples (action, target)
world.set_actions(0, actions)  # adds actions for the ennemy
world.set_actions(1, actions)  # adds actions for you
world.update()  # simulate the turn
```