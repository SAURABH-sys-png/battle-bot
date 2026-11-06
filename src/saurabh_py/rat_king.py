from battlecode26 import *
from algorithms import find_nxt_move

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


def rat_king_exploration(curr_dir: Direction):
    head = curr_dir
    intended_nxt_move = curr_dir
    if rc.can_move(head):
        rc.move(head)
        return head

    right, left = head, head
    for i in range(3):
        right = right.rotate_right()
        left = left.rotate_left()
        for nxt in (right, left):
            if rc.can_move(nxt):
                intended_nxt_move = nxt
                rc.move(intended_nxt_move)
                return intended_nxt_move

    nxt = right.rotate_right()
    if rc.can_move(nxt):
        intended_nxt_move = nxt
        rc.move(intended_nxt_move)
        return intended_nxt_move
    return None


RING = []
for dx in range(-2, 3):
    for dy in range(-2, 3):
        adx = abs(dx)
        ady = abs(dy)
        if adx == 2 or ady == 2:
            RING.append((dx, dy))


def spawn_baby_rat():
    if not rc.is_action_ready():
        return False
    if rc.get_global_cheese() < rc.get_current_rat_cost():
        return False

    me = rc.get_location()
    for dx, dy in RING:
        loc = me.translate(dx, dy)
        if rc.can_build_rat(loc):
            rc.build_rat(loc)
            log("spawned baby rat at", loc, "cost was", rc.get_current_rat_cost())
            return True
    return False


# we store the location of the base on last 2 indices
def process_rat_king(curr_loc: MapLocation):
    turn_count = rc.get_round_num()
    if turn_count == 1:
        spawn_baby_rat()
        rc.write_shared_array(0, curr_loc.x)
        rc.write_shared_array(1, curr_loc.y)
    if turn_count <= 15:
        # try to and forth to the base coordinates
        spawn_baby_rat()
        rat_king_exploration(rc.get_direction())
    else:
        base_loc = MapLocation(rc.read_shared_array(0), rc.read_shared_array(1))
        find_nxt_move(curr_loc, base_loc)
    return
