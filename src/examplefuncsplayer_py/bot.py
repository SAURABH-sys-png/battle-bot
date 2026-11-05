from battlecode26 import *
from rat_king import process_rat_king

DIRECTIONS = [
    Direction.NORTH,
    Direction.NORTHEAST,
    Direction.EAST,
    Direction.SOUTHEAST,
    Direction.SOUTH,
    Direction.SOUTHWEST,
    Direction.WEST,
    Direction.NORTHWEST,
]

turn_count = 0


def turn():
    global turn_count
    turn_count += 1

    if rc.get_type() == UnitType.RAT_KING:
        process_rat_king()
