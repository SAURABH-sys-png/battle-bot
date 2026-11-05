from battlecode26 import *


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
    """Try to spawn one baby rat. Returns True if one was spawned."""
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
