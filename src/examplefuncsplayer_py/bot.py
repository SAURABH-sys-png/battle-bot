from battlecode26 import *

rc = RobotController


# ==================================================
# CONFIGURATION
# ==================================================

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

# Track previously visited positions.
position_visits = {}

# Penalty for revisiting positions.
VISIT_PENALTY = 5


# ==================================================
# UTILITIES AND LOGGING
# ==================================================

def key(loc):
    return (loc.x, loc.y)


def log_event(message):
    log(
        "[ROUND "
        + str(rc.get_round_num())
        + "] "
        + str(message)
    )


def get_visits(loc):
    return position_visits.get(key(loc), 0)


def record_position(loc):
    k = key(loc)
    position_visits[k] = position_visits.get(k, 0) + 1


# ==================================================
# POSITION-BASED MOVEMENT
# ==================================================

def move_towards(target):

    current = rc.get_location()

    candidates = []

    log_event(
        "Calculating movement from "
        + str(current)
        + " towards "
        + str(target)
    )

    # Evaluate all eight possible destinations.
    for direction in DIRECTIONS:

        next_location = current.add(direction)

        distance = distance_squared_to(
            next_location,
            target
        )

        visits = get_visits(next_location)

        score = distance + visits * VISIT_PENALTY

        candidates.append(
            (
                score,
                distance,
                visits,
                direction,
                next_location
            )
        )

    # Best destination first.
    candidates.sort(key=lambda item: item[0])

    # Try each candidate until a legal move succeeds.
    for score, distance, visits, direction, next_location in candidates:

        try:

            log_event(
                "Considering "
                + str(direction)
                + " | Destination="
                + str(next_location)
                + " | Distance="
                + str(distance)
                + " | Visits="
                + str(visits)
                + " | Score="
                + str(score)
            )

            if not rc.can_move(direction):

                log_event(
                    "BLOCKED: " + str(direction)
                )

                continue

            log_event(
                "MOVING "
                + str(direction)
                + " from "
                + str(current)
                + " to "
                + str(next_location)
            )

            rc.move(direction)

            actual_location = rc.get_location()

            if actual_location != current:

                record_position(actual_location)

                log_event(
                    "MOVE SUCCESSFUL: "
                    + str(current)
                    + " -> "
                    + str(actual_location)
                )

                return True

            log_event(
                "WARNING: Position did not change after move."
            )

        except GameActionException as e:

            log_event(
                "MOVEMENT GAME EXCEPTION: " + str(e)
            )

    log_event(
        "NO LEGAL MOVEMENT AVAILABLE from "
        + str(current)
    )

    return False


# ==================================================
# EXPLORATION
# ==================================================

def explore():

    current = rc.get_location()

    candidates = []

    log_event(
        "Exploring from " + str(current)
    )

    for direction in DIRECTIONS:

        next_location = current.add(direction)

        visits = get_visits(next_location)

        candidates.append(
            (visits, direction, next_location)
        )

    # Prefer positions visited fewer times.
    candidates.sort(key=lambda item: item[0])

    for visits, direction, next_location in candidates:

        try:

            log_event(
                "Exploration candidate: "
                + str(next_location)
                + " | Direction="
                + str(direction)
                + " | Visits="
                + str(visits)
            )

            if not rc.can_move(direction):

                log_event(
                    "Exploration blocked: "
                    + str(direction)
                )

                continue

            log_event(
                "EXPLORATION MOVE: "
                + str(current)
                + " -> "
                + str(next_location)
            )

            rc.move(direction)

            actual_location = rc.get_location()

            if actual_location != current:

                record_position(actual_location)

                log_event(
                    "EXPLORATION SUCCESS: "
                    + str(actual_location)
                )

                return True

        except GameActionException as e:

            log_event(
                "EXPLORATION GAME EXCEPTION: " + str(e)
            )

    log_event(
        "Exploration failed: no legal movement."
    )

    return False


# ==================================================
# CHEESE COLLECTION
# ==================================================

def collect_cheese():

    log_event(
        "Searching for collectible cheese."
    )

    infos = rc.sense_nearby_map_infos()

    cheese_tiles = [
        info for info in infos
        if info.cheese_amount > 0
    ]

    cheese_tiles.sort(
        key=lambda info: info.cheese_amount,
        reverse=True
    )

    if not cheese_tiles:

        log_event(
            "No cheese available nearby."
        )

        return False

    for info in cheese_tiles:

        try:

            log_event(
                "Found cheese at "
                + str(info.location)
                + " | Amount="
                + str(info.cheese_amount)
            )

            if rc.can_pick_up_cheese(info.location):

                log_event(
                    "PICKING UP CHEESE at "
                    + str(info.location)
                )

                rc.pick_up_cheese(info.location)

                log_event(
                    "CHEESE PICKUP SUCCESSFUL"
                )

                return True

            else:

                log_event(
                    "Cannot collect cheese at "
                    + str(info.location)
                )

        except GameActionException as e:

            log_event(
                "CHEESE GAME EXCEPTION: " + str(e)
            )

    return False


# ==================================================
# RAT SPAWNING
# ==================================================

def spawn_rat():

    current = rc.get_location()

    log_event(
        "Searching for a valid rat spawning position around "
        + str(current)
    )

    possible_locations = (
        rc.get_all_locations_within_radius_squared(
            current,
            8
        )
    )

    for loc in possible_locations:

        try:

            if rc.can_build_rat(loc):

                log_event(
                    "SPAWNING RAT at " + str(loc)
                )

                rc.build_rat(loc)

                log_event(
                    "RAT SPAWN SUCCESSFUL at " + str(loc)
                )

                return True

        except GameActionException as e:

            log_event(
                "SPAWNING GAME EXCEPTION: " + str(e)
            )

    log_event(
        "Unable to spawn rat. Waiting for resources or space."
    )

    return False


# ==================================================
# RAT KING STRATEGY
# ==================================================

def rat_king_turn():

    current = rc.get_location()

    log_event(
        "RAT KING TURN | Position=" + str(current)
    )

    # Sense visible map information.
    map_infos = rc.sense_nearby_map_infos()

    log_event(
        "Visible map tiles: " + str(len(map_infos))
    )

    # Find visible cheese mines.
    mines = [
        info for info in map_infos
        if info.has_cheese_mine
    ]

    # No mine visible: explore.
    if not mines:

        log_event(
            "NO CHEESE MINE VISIBLE. Starting exploration."
        )

        explore()
        return

    # Select nearest visible mine.
    nearest_mine = None
    nearest_distance = None

    for mine in mines:
        distance = distance_squared_to(current, mine.location)
        if nearest_mine is None or distance < nearest_distance:
            nearest_mine = mine
            nearest_distance = distance

    mine_location = nearest_mine.location

    distance = distance_squared_to(
        current,
        mine_location
    )

    log_event(
        "NEAREST MINE: "
        + str(mine_location)
        + " | Distance squared="
        + str(distance)
    )

    # Move towards the mine.
    if distance > 2:

        log_event(
            "MINE NOT REACHED. Calculating next movement."
        )

        move_towards(mine_location)
        return

    # Reached the mine area. Stop moving.
    log_event(
        "CHEESE MINE REACHED. RAT KING MOVEMENT DISABLED."
    )

    # Collect cheese.
    if collect_cheese():
        return

    # Spawn rats.
    spawn_rat()

    log_event(
        "RAT KING STAYS AT THE CHEESE MINE."
    )


# ==================================================
# MAIN TURN
# ==================================================

def turn():

    try:

        my_type = rc.get_type()
        my_location = rc.get_location()

        log_event(
            "========================================"
        )

        log_event(
            "NEW TURN | TYPE="
            + str(my_type)
            + " | LOCATION="
            + str(my_location)
        )

        # Baby rats remain stationary.
        if my_type == UnitType.BABY_RAT:

            log_event(
                "BABY RAT: Stationary mode. No movement."
            )

            return

        # Rat King strategy.
        if my_type == UnitType.RAT_KING:

            rat_king_turn()
            return

        log_event(
            "No strategy defined for this robot type."
        )

    except GameActionException as e:

        log(
            "[GAME ACTION EXCEPTION] " + str(e)
        )

    except Exception as e:

        log(
            "[UNEXPECTED PYTHON EXCEPTION] " + str(e)
        )