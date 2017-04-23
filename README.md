# CotC
Code for CodinGame
(pseudo : [Jarjar1er](https://www.codingame.com/profile/dfba845bc6de865d26bf09344068009e0165161))


## Referee
####Utilisation
```
world = get_world()
actions = [(Action.WAIT, None), (Action.FIRE, Coord(5, 9)]  # list of tuples (action, target)
world.prepare()
world.set_actions(0, actions)  # adds actions for the ennemy
world.set_actions(1, actions)  # adds actions for you
world.update()  # simulate the turn
```
#### Known bugs
 * If a ship takes a mine, it's destroyed.

**Do not hesitate to contact me** (Je parle français !) to show a bug, sugest an optimisation,
thanks me or just talk :D

## Graphic
##### Dependances
This works with pygame, if you have troubles installing it, try [this](https://youtu.be/MdGoAnFP-mU).

##### Commands
* `R` creates a new random world
* `U` makes actions (they're hardcoded) and updates this world 
* `L` goes back in the history of what you simulate. Yes, t's a time machine.