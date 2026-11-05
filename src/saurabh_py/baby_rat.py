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
    Direction.CENTER,
]


def flee_from_cat():
    return 1


def squeek_to_distract():
    return 1


def has_cheese_nearby():
    return 1


def move_towards_location(cheese_location: MapLocation):
    return 1


def pick_cheese_nearby():
    for info in rc.sense_nearby_map_infos(radius_squared=2):
        if info.cheese_amount > 0 and rc.can_pick_up_cheese(info.location):
            rc.pick_up_cheese(info.location)
            return True
    return False


def dig_adjacent_dirt():
    for info in rc.sense_nearby_map_infos(radius_squared=2):
        if not info.is_dirt:
            continue
        loc = info.location
        if rc.can_remove_dirt(loc):
            rc.remove_dirt(loc)
            return True
    return False


def face_dirt_if_needed():
    if not rc.is_turning_ready():
        return
    for d in DIRECTIONS:
        if d == Direction.CENTER:
            continue
        loc = rc.adjacent_location(d)
        if rc.on_the_map(loc) and not rc.can_sense_location(loc):
            rc.turn(d)
            return


def pick_cheese(cheese_location: MapLocation):
    if rc.can_pick_up_cheese(cheese_location):
        rc.pick_up_cheese(cheese_location)
    else:
        move_towards_location(cheese_location)


def baby_rat_exploration(curr_dir: Direction):
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


def distance_squared_between(x1, y1, x2, y2):
    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy


_DIR_OFFSETS = {}


def direction_offset(d):
    if not _DIR_OFFSETS:
        me = rc.get_location()
        for dd in DIRECTIONS:
            loc = rc.adjacent_location(dd)
            _DIR_OFFSETS[dd] = (loc.x - me.x, loc.y - me.y)
    return _DIR_OFFSETS[d]


def direction_between(dx, dy):
    sx = (dx > 0) - (dx < 0)
    sy = (dy > 0) - (dy < 0)
    for d in DIRECTIONS:
        if direction_offset(d) == (sx, sy):
            return d
    return Direction.CENTER


def return_to_boss():
    boss_x = rc.read_shared_array(1)
    boss_y = rc.read_shared_array(2)
    # move towards boss_x
    me = rc.get_location()

    if distance_squared_between(me.x, me.y, boss_x, boss_y) <= 2:
        return Direction.CENTER

    head = direction_between(boss_x - me.x, boss_y - me.y)
    if rc.can_move(head):
        rc.move(head)
        return head

    right, left = head, head
    for i in range(3):
        right = right.rotate_right()
        left = left.rotate_left()
        for nxt in (right, left):
            if rc.can_move(nxt):
                rc.move(nxt)
                return nxt
    return None


def proces_baby_rat(cheese_count: int):
    if cheese_count > 0:
        return_to_boss()
    else:
        pick_cheese_nearby()
        baby_rat_exploration(rc.get_direction())

