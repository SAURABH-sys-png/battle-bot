from battlecode26 import *
import math


def best_nxt_move():
    return 1


def nearest_dir(r1, c1, r2, c2):
    angle = math.atan2(r2 - r1, c2 - c1)  # angle to the target, in radians
    k = round(angle / (math.pi / 4)) % 8  # which of the 8 45° slices it falls in
    return [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)][k]


def find_nxt_move(curr_loc: MapLocation, dest_loc: MapLocation):
    """ "Sweep line algorithm to find the shortest distance bw point a to b"""
    # we need to handle dirt or so in the order
    if curr_loc.x == dest_loc.x and curr_loc.y == dest_loc.y:
        return False
    dx, dy = nearest_dir(curr_loc.x, curr_loc.y, dest_loc.x, dest_loc.y)
    return move_by_delta(dx, dy)


def direction_from_delta(dx, dy):
    sx = (dx > 0) - (dx < 0)
    sy = (dy > 0) - (dy < 0)

    directions = {
        (0, 1): Direction.NORTH,
        (1, 1): Direction.NORTHEAST,
        (1, 0): Direction.EAST,
        (1, -1): Direction.SOUTHEAST,
        (0, -1): Direction.SOUTH,
        (-1, -1): Direction.SOUTHWEST,
        (-1, 0): Direction.WEST,
        (-1, 1): Direction.NORTHWEST,
    }
    return directions.get((sx, sy))


def move_by_delta(dx, dy):
    direction = direction_from_delta(dx, dy)
    if direction is None or not rc.can_move(direction):
        return False
    rc.move(direction)
    return True
