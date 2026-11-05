from battlecode26 import *


def process_rat_king():
    curr_loc = rc.get_location()
    if rc.can_move(Direction.NORTH):
        rc.move(Direction.NORTH)
    else:
        rc.move(Direction.SOUTH)
