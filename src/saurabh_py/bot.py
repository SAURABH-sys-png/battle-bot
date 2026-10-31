from battlecode26 import *

rc = RobotController

turn_count = 0
pending_rat_spawn = False
baby_rats_spawned = 0
robot_states = {}

MAX_BABY_RATS = 10


directions = [
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


def minimum_by(items, score):
    best_item = None
    best_score = None

    for item in items:
        item_score = score(item)
        if best_item is None or item_score < best_score:
            best_item = item
            best_score = item_score

    return best_item


def get_robot_state():
    robot_id = rc.get_id()
    if robot_id not in robot_states:
        robot_states[robot_id] = {
            "rat_king_location": None,
            "enemy_king_location": None,
            "known_passable": {},
            "visited_locations": {},
            "explore_target": None,
        }
    return robot_states[robot_id]


def try_spawn_rat():
    global baby_rats_spawned

    if baby_rats_spawned >= MAX_BABY_RATS:
        return False

    current = rc.get_location()

    for location in rc.get_all_locations_within_radius_squared(current, 8):
        if rc.can_build_rat(location):
            rc.build_rat(location)
            baby_rats_spawned += 1
            return True

    return False


def location_key(location):
    return (location.x, location.y)


def direction_index(direction):
    for index in range(len(directions)):
        if directions[index] == direction:
            return index
    return 0


def update_known_map(state, map_infos, current):
    known_passable = state["known_passable"]
    known_passable[location_key(current)] = True
    for info in map_infos:
        known_passable[location_key(info.location)] = (
            info.is_passable and not info.is_wall
        )


def find_paths(current, robots, state):
    known_passable = state["known_passable"]
    start = location_key(current)
    blocked = {
        location_key(robot.location)
        for robot in robots
        if robot.id != rc.get_id()
    }
    queue = [start]
    first_steps = {start: None}
    distances = {start: 0}
    locations = {start: current}

    for key in queue:
        location = locations[key]
        for direction in directions:
            next_location = location.add(direction)
            next_key = location_key(next_location)

            if next_key in first_steps or not known_passable.get(next_key, False):
                continue
            if next_key in blocked:
                continue

            first_step = direction if key == start else first_steps[key]
            if key == start and not rc.can_move(direction):
                continue

            first_steps[next_key] = first_step
            distances[next_key] = distances[key] + 1
            locations[next_key] = next_location
            queue.append(next_key)

    return first_steps, distances


def move_towards(target, current, robots, state, target_radius_squared=0):
    first_steps, distances = find_paths(current, robots, state)
    target_keys = [
        key for key in first_steps
        if (key[0] - target.x) ** 2 + (key[1] - target.y) ** 2
        <= target_radius_squared
        and first_steps[key] is not None
    ]

    if target_keys:
        destination = minimum_by(target_keys, lambda key: distances[key])
        direction = first_steps[destination]
    else:
        reachable = [
            key for key in first_steps
            if first_steps[key] is not None
        ]
        if reachable:
            destination = minimum_by(
                reachable,
                lambda key: (
                    (key[0] - target.x) ** 2 + (key[1] - target.y) ** 2,
                    distances[key],
                ),
            )
            direction = first_steps[destination]
        else:
            direction = None

    if direction is None:
        best_direction = None
        best_distance = distance_squared(current, target)
        for candidate in directions:
            if not rc.can_move(candidate):
                continue
            next_location = current.add(candidate)
            next_distance = distance_squared(next_location, target)
            if next_distance < best_distance:
                best_direction = candidate
                best_distance = next_distance
        direction = best_direction

    if direction is None:
        return False

    rc.move(direction)
    return True


def explore(current, map_infos, robots, state, record_visit=True):
    update_known_map(state, map_infos, current)
    visited_locations = state["visited_locations"]
    current_key = location_key(current)
    if record_visit:
        visited_locations[current_key] = visited_locations.get(current_key, 0) + 1
    first_steps, distances = find_paths(current, robots, state)

    explore_target = state["explore_target"]
    if explore_target not in first_steps or explore_target == current_key:
        candidates = [
            key for key in first_steps
            if key != current_key
        ]
        if not candidates:
            state["explore_target"] = None
            return False

        direction_offset = (
            rc.get_round_num() + rc.get_id()
        ) % len(directions)
        explore_target = minimum_by(
            candidates,
            lambda key: (
                visited_locations.get(key, 0),
                -distances[key],
                (direction_index(first_steps[key]) - direction_offset)
                % len(directions),
            ),
        )
        state["explore_target"] = explore_target

    direction = first_steps.get(explore_target)
    if direction is None:
        state["explore_target"] = None
        return False

    rc.move(direction)
    return True


def process_rat_king():
    global pending_rat_spawn

    state = get_robot_state()
    curr_loc = rc.get_location()
    if baby_rats_spawned >= MAX_BABY_RATS:
        pending_rat_spawn = False
        explore(
            curr_loc,
            rc.sense_nearby_map_infos(),
            rc.sense_nearby_robots(),
            state,
        )
        return

    map_infos = rc.sense_nearby_map_infos()
    update_known_map(state, map_infos, curr_loc)
    cheese_tiles = [info for info in map_infos if info.cheese_amount > 0]

    if pending_rat_spawn and try_spawn_rat():
        pending_rat_spawn = False
        return

    for info in cheese_tiles:
        if rc.can_pick_up_cheese(info.location):
            rc.pick_up_cheese(info.location)
            pending_rat_spawn = True
            if try_spawn_rat():
                pending_rat_spawn = False
            return

    if cheese_tiles:
        target = minimum_by(
            cheese_tiles,
            lambda info: distance_squared(curr_loc, info.location),
        ).location
        if move_towards(target, curr_loc, rc.sense_nearby_robots(), state):
            return

    if explore(curr_loc, map_infos, rc.sense_nearby_robots(), state):
        return

    try_spawn_rat()


def process_baby_rat():
    state = get_robot_state()
    curr_loc = rc.get_location()
    my_team = rc.get_team()
    nearby_robots = rc.sense_nearby_robots()
    map_infos = rc.sense_nearby_map_infos()
    update_known_map(state, map_infos, curr_loc)
    current_key = location_key(curr_loc)
    visited_locations = state["visited_locations"]
    visited_locations[current_key] = visited_locations.get(current_key, 0) + 1

    for robot in nearby_robots:
        if robot.team == my_team and robot.type.is_rat_king_type():
            state["rat_king_location"] = robot.location
            break

    carried_cheese = rc.sense_robot(rc.get_id()).cheese_amount
    if process_enemy_rat_king(
        curr_loc,
        my_team,
        nearby_robots,
        state,
        pursue=carried_cheese <= 0,
    ):
        return

    if carried_cheese > 0:
        rat_king_location = state["rat_king_location"]
        if rat_king_location is None:
            explore(
                curr_loc,
                map_infos,
                nearby_robots,
                state,
                record_visit=False,
            )
            return

        king_distance = distance_squared(curr_loc, rat_king_location)
        if king_distance <= GameConstants.CHEESE_TRANSFER_RADIUS_SQUARED:
            if rc.can_transfer_cheese(rat_king_location, carried_cheese):
                rc.transfer_cheese(rat_king_location, carried_cheese)
                state["rat_king_location"] = None
            return

        if move_towards(
            rat_king_location,
            curr_loc,
            nearby_robots,
            state,
            GameConstants.CHEESE_TRANSFER_RADIUS_SQUARED,
        ):
            return

        explore(
            curr_loc,
            map_infos,
            nearby_robots,
            state,
            record_visit=False,
        )
        return

    cheese_tiles = [info for info in map_infos if info.cheese_amount > 0]

    for info in cheese_tiles:
        if rc.can_pick_up_cheese(info.location):
            rc.pick_up_cheese(info.location)
            return

    if cheese_tiles:
        target = minimum_by(
            cheese_tiles,
            lambda info: distance_squared(curr_loc, info.location),
        ).location
        if move_towards(target, curr_loc, nearby_robots, state):
            return

    explore(curr_loc, map_infos, nearby_robots, state, record_visit=False)


def process_enemy_rat_king(current, my_team, robots, state, pursue):
    enemy_location = state["enemy_king_location"]

    for robot in robots:
        if robot.team != my_team and robot.type.is_rat_king_type():
            enemy_location = robot.location
            state["enemy_king_location"] = enemy_location

            if rc.can_attack(enemy_location):
                rc.attack(enemy_location)
                return True

            if distance_squared(current, enemy_location) <= (
                GameConstants.ATTACK_DISTANCE_SQUARED
            ):
                return True

            if pursue and move_towards(
                enemy_location,
                current,
                robots,
                state,
                GameConstants.ATTACK_DISTANCE_SQUARED,
            ):
                return True
            return False

    if enemy_location is None:
        return False

    if distance_squared(current, enemy_location) <= (
        GameConstants.ATTACK_DISTANCE_SQUARED
    ):
        state["enemy_king_location"] = None
        return False

    if pursue and move_towards(
        enemy_location,
        current,
        robots,
        state,
        GameConstants.ATTACK_DISTANCE_SQUARED,
    ):
        return True

    return False


def turn():
    global turn_count
    turn_count += 1
    unit_type = rc.get_type()

    if unit_type.is_rat_king_type():
        process_rat_king()
    elif unit_type.is_baby_rat_type():
        process_baby_rat()
