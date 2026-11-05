from battlecode26 import *

rc = RobotController

KING_PRESENT_INDEX = 0
KING_X_INDEX = 1
KING_Y_INDEX = 2
CHEESE_TARGET_PRESENT_INDEX = 3
CHEESE_TARGET_X_INDEX = 4
CHEESE_TARGET_Y_INDEX = 5
ENEMY_KING_PRESENT_INDEX = 6
ENEMY_KING_X_INDEX = 7
ENEMY_KING_Y_INDEX = 8

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


def distance_squared(first, second):
    dx = first.x - second.x
    dy = first.y - second.y
    return dx * dx + dy * dy


def target_location(x, y):
    return MapLocation(x, y)


def share_cheese_target(location):
    rc.write_shared_array(CHEESE_TARGET_X_INDEX, location.x)
    rc.write_shared_array(CHEESE_TARGET_Y_INDEX, location.y)
    rc.write_shared_array(CHEESE_TARGET_PRESENT_INDEX, 1)


def move_toward(target):
    current = rc.get_location()
    current_distance = distance_squared(current, target)
    best_direction = None
    best_distance = current_distance
    start = (rc.get_round_num() + rc.get_id()) % len(DIRECTIONS)

    for offset in range(len(DIRECTIONS)):
        direction = DIRECTIONS[(start + offset) % len(DIRECTIONS)]
        if not rc.can_move(direction):
            continue

        next_location = current.add(direction)
        next_distance = distance_squared(next_location, target)
        if next_distance < best_distance:
            best_direction = direction
            best_distance = next_distance

    if best_direction is not None:
        rc.move(best_direction)
        return True

    return False


def roam():
    start = (rc.get_round_num() * 5 + rc.get_id()) % len(DIRECTIONS)
    for offset in range(len(DIRECTIONS)):
        direction = DIRECTIONS[(start + offset) % len(DIRECTIONS)]
        if rc.can_move(direction):
            rc.move(direction)
            return True
    return False


def attack_visible_enemy(robots):
    my_team = rc.get_team()

    for robot in robots:
        if (
            robot.team != my_team
            and not robot.type.is_cat_type()
            and rc.can_attack(robot.location)
        ):
            rc.attack(robot.location)
            return True

    return False


def flee_visible_cat(robots):
    my_team = rc.get_team()
    current = rc.get_location()
    cats = []

    for robot in robots:
        if robot.team != my_team and robot.type.is_cat_type():
            cats.append(robot)

    if not cats:
        return False

    start = (rc.get_round_num() + rc.get_id()) % len(DIRECTIONS)
    best_direction = None
    best_distance = -1
    best_exposed = True

    for offset in range(len(DIRECTIONS)):
        direction = DIRECTIONS[(start + offset) % len(DIRECTIONS)]
        if not rc.can_move(direction):
            continue

        destination = current.add(direction)
        nearest_cat_distance = None
        exposed = False

        for cat in cats:
            distance = distance_squared(destination, cat.location)
            if nearest_cat_distance is None or distance < nearest_cat_distance:
                nearest_cat_distance = distance
            if destination == cat.location.add(cat.direction):
                exposed = True

        if best_direction is None:
            best_direction = direction
            best_distance = nearest_cat_distance
            best_exposed = exposed
        elif best_exposed and not exposed:
            best_direction = direction
            best_distance = nearest_cat_distance
            best_exposed = exposed
        elif exposed == best_exposed and nearest_cat_distance > best_distance:
            best_direction = direction
            best_distance = nearest_cat_distance

    if best_direction is None:
        return False

    rc.move(best_direction)
    return True


def nearest_cheese(map_infos, current):
    best_info = None
    best_distance = None

    for info in map_infos:
        if info.cheese_amount <= 0:
            continue

        distance = distance_squared(current, info.location)
        if best_info is None or distance < best_distance:
            best_info = info
            best_distance = distance

    return best_info


def collect_or_seek_cheese(map_infos, report_to_king=False):
    current = rc.get_location()
    cheese = nearest_cheese(map_infos, current)

    if cheese is not None:
        if report_to_king:
            share_cheese_target(cheese.location)
        if rc.can_pick_up_cheese(cheese.location):
            rc.pick_up_cheese(cheese.location)
            return True
        if move_toward(cheese.location):
            return True

    return False


def try_build_rat():
    current = rc.get_location()
    locations = rc.get_all_locations_within_radius_squared(current, 8)

    for location in locations:
        if rc.can_build_rat(location):
            rc.build_rat(location)
            return True

    return False


def process_rat_king():
    current = rc.get_location()
    rc.write_shared_array(KING_X_INDEX, current.x)
    rc.write_shared_array(KING_Y_INDEX, current.y)
    rc.write_shared_array(KING_PRESENT_INDEX, 1)

    robots = rc.sense_nearby_robots()
    if flee_visible_cat(robots):
        return
    if attack_visible_enemy(robots):
        return

    for robot in robots:
        if robot.team != rc.get_team() and robot.type.is_rat_king_type():
            rc.write_shared_array(ENEMY_KING_X_INDEX, robot.location.x)
            rc.write_shared_array(ENEMY_KING_Y_INDEX, robot.location.y)
            rc.write_shared_array(ENEMY_KING_PRESENT_INDEX, 1)

    if try_build_rat():
        return

    map_infos = rc.sense_nearby_map_infos()
    if collect_or_seek_cheese(map_infos, report_to_king=True):
        return

    if rc.read_shared_array(CHEESE_TARGET_PRESENT_INDEX) == 1:
        target = target_location(
            rc.read_shared_array(CHEESE_TARGET_X_INDEX),
            rc.read_shared_array(CHEESE_TARGET_Y_INDEX),
        )
        if rc.can_sense_location(target):
            if rc.sense_map_info(target).cheese_amount <= 0:
                rc.write_shared_array(CHEESE_TARGET_PRESENT_INDEX, 0)
            elif move_toward(target):
                return
        elif move_toward(target):
            return

    roam()


def process_baby_rat():
    robots = rc.sense_nearby_robots()
    if flee_visible_cat(robots):
        return
    if attack_visible_enemy(robots):
        return

    current = rc.get_location()
    carried = rc.sense_robot(rc.get_id()).cheese_amount
    if carried > 0 and rc.read_shared_array(KING_PRESENT_INDEX) == 1:
        king = target_location(
            rc.read_shared_array(KING_X_INDEX),
            rc.read_shared_array(KING_Y_INDEX),
        )
        if rc.can_transfer_cheese(king, carried):
            rc.transfer_cheese(king, carried)
            return
        if move_toward(king):
            return
        roam()
        return

    if rc.read_shared_array(ENEMY_KING_PRESENT_INDEX) == 1:
        enemy_king = target_location(
            rc.read_shared_array(ENEMY_KING_X_INDEX),
            rc.read_shared_array(ENEMY_KING_Y_INDEX),
        )
        if move_toward(enemy_king):
            return

    map_infos = rc.sense_nearby_map_infos()
    if collect_or_seek_cheese(map_infos):
        return

    roam()


def turn():
    unit_type = rc.get_type()
    if unit_type.is_rat_king_type():
        process_rat_king()
    elif unit_type.is_baby_rat_type():
        process_baby_rat()
