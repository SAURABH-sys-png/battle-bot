# BATTLECODE 2026
# Python Player API Reference

**Package:** `battlecode26`  
**Version:** `1.2.2`  
**Python version:** `3.12`  
**Reference source:** `wrappers.py` and `classes.py`

---

# 1. Introduction

This document explains the Python API available to a Battlecode 2026 player.

The API provides access to the game engine through a Python wrapper. Your bot uses these methods to:

- Read the current game state.
- Identify its team, unit type, location, and health.
- Move around the map.
- Sense nearby robots and map information.
- Attack other robots.
- Build and carry rats.
- Collect and transfer cheese.
- Place and remove dirt.
- Place and remove traps.
- Communicate with other robots.
- Display debugging information.

The Python API communicates with the underlying game engine through wrapper methods. These methods send requests using identifiers from `CrossPlayMethod` and receive responses through `send_wait_and_parse`.

## 1.1 Important Architecture

The supplied `wrappers.py` defines a class called:

```python
RobotController
```

Its methods are static methods.

The file also defines:

```python
rc = RobotController
```

This means you can use the shorter `rc` name to call the API.

For example:

```python
round_number = rc.get_round_num()
location = rc.get_location()
health = rc.get_health()
```

You do not need to create a `RobotController` object.

## 1.2 Basic Example

```python
from battlecode26 import *

def turn():
    current_round = rc.get_round_num()
    current_location = rc.get_location()

    log("Round:", current_round)
    log("Location:", current_location)

    if rc.can_move(Direction.NORTH):
        rc.move(Direction.NORTH)
```

The example demonstrates:

- Reading the current round.
- Reading the robot's location.
- Printing debugging information.
- Checking whether movement is possible.
- Moving the robot.

**Important:** This document describes the Python-facing API found in the supplied source files. It does not attempt to define every game rule, action cost, visibility restriction, or engine-side behavior.

---

# 2. Core API Types

Before using the RobotController methods, you should understand the types used by the API.

The main types are:

1. `Team`
2. `Direction`
3. `MapLocation`
4. `UnitType`
5. `TrapType`
6. `RobotInfo`
7. `MapInfo`
8. `Message`
9. `GameActionException`
10. `GameConstants`

---

# 3. Team

The `Team` enum identifies which team a robot belongs to.

It contains three values:

| Value | Description |
|---|---|
| `Team.A` | Team A |
| `Team.B` | Team B |
| `Team.NEUTRAL` | Neutral team |

## 3.1 Methods

### `opponent()`

Returns the opposing team.

```python
my_team = rc.get_team()
enemy_team = my_team.opponent()
```

### `ordinal()`

Returns the numerical enum value.

The supplied source defines:

| Team | Ordinal |
|---|---:|
| A | 0 |
| B | 1 |
| NEUTRAL | 2 |

## 3.2 Example

```python
team = rc.get_team()

if team == Team.A:
    log("I belong to Team A")

elif team == Team.B:
    log("I belong to Team B")
```

---

# 4. Direction

`Direction` represents the eight compass directions and the center direction.

It is one of the most frequently used types in Battlecode.

## 4.1 Direction Values

| Direction | dx | dy |
|---|---:|---:|
| NORTH | 0 | 1 |
| NORTHEAST | 1 | 1 |
| EAST | 1 | 0 |
| SOUTHEAST | 1 | -1 |
| SOUTH | 0 | -1 |
| SOUTHWEST | -1 | -1 |
| WEST | -1 | 0 |
| NORTHWEST | -1 | 1 |
| CENTER | 0 | 0 |

The `dx` and `dy` fields represent the direction's coordinate changes.

For example:

```python
Direction.NORTH.dx
```

returns `0`, while:

```python
Direction.NORTH.dy
```

returns `1`.

## 4.2 Direction Methods

### `opposite()`

Returns the opposite direction.

```python
direction = Direction.NORTH
opposite = direction.opposite()
```

Result:

```python
Direction.SOUTH
```

### `rotate_left()`

Rotates the direction to the left.

```python
direction = Direction.NORTH
new_direction = direction.rotate_left()
```

### `rotate_right()`

Rotates the direction to the right.

```python
direction = Direction.NORTH
new_direction = direction.rotate_right()
```

### `all_directions()`

Returns all direction enum members, including `CENTER`.

### `cardinal_directions()`

Returns the four cardinal directions:

- NORTH
- EAST
- SOUTH
- WEST

### `get_delta_x()`

Returns the horizontal coordinate change.

### `get_delta_y()`

Returns the vertical coordinate change.

### `ordinal()`

Returns the numerical enum value.

## 4.3 Example

```python
direction = Direction.EAST

x_change = direction.get_delta_x()
y_change = direction.get_delta_y()

log(x_change, y_change)
```

Expected output:

```text
1 0
```

---

# 5. MapLocation

`MapLocation` represents a coordinate on the game map.

It contains two fields:

```python
x
y
```

For example:

```python
location = MapLocation(5, 10)
```

This represents the coordinate `(5, 10)`.

## 5.1 Fields

| Field | Description |
|---|---|
| `x` | Horizontal coordinate |
| `y` | Vertical coordinate |

## 5.2 Methods

### `add(dir)`

Adds a direction to the current location.

```python
location = MapLocation(5, 10)

new_location = location.add(Direction.NORTH)
```

Result:

```python
MapLocation(5, 11)
```

### `subtract(dir)`

Subtracts a direction from the current location.

```python
location = MapLocation(5, 10)

new_location = location.subtract(Direction.NORTH)
```

### `translate(dx, dy)`

Moves a location by specified coordinate changes.

```python
location = MapLocation(5, 10)

new_location = location.translate(2, 3)
```

Result:

```python
MapLocation(7, 13)
```

## 5.3 Equality

The supplied implementation compares locations using their `x` and `y` values.

Example:

```python
a = MapLocation(5, 10)
b = MapLocation(5, 10)

if a == b:
    log("Same location")
```

---

# 6. UnitType

`UnitType` describes the different robot types in the game.

The supplied 2026 API defines three types:

- `BABY_RAT`
- `RAT_KING`
- `CAT`

## 6.1 UnitType Attributes

| Attribute | BABY_RAT | RAT_KING | CAT |
|---|---:|---:|---:|
| Health | 100 | 500 | 10000 |
| Size | 1 | 3 | 2 |
| Vision radius squared | 20 | 25 | 17 |
| Vision angle | 90 | 360 | 180 |
| Action cooldown | 10 | 10 | 15 |
| Movement cooldown | 10 | 40 | 20 |
| Bytecode limit | 17500 | 20000 | 17500 |

These values are exposed as attributes of the unit type.

Example:

```python
unit_type = rc.get_type()

log(unit_type.health)
log(unit_type.size)
```

## 6.2 UnitType Methods

### `uses_bottom_left_location_for_distance()`

Returns whether the unit type uses the bottom-left location convention for distance calculations.

The supplied source indicates that this is true for `CAT`.

### `is_robot_type()`

Checks whether the unit is a robot type.

### `is_throwable_type()`

Checks whether the type can be thrown.

### `is_throwing_type()`

Checks whether the type is a throwing type.

### `is_baby_rat_type()`

Checks whether the type is `BABY_RAT`.

### `is_rat_king_type()`

Checks whether the type is `RAT_KING`.

### `is_cat_type()`

Checks whether the type is `CAT`.

### `ordinal()`

Returns the enum's numerical value.

## 6.3 Example

```python
my_type = rc.get_type()

if my_type.is_baby_rat_type():
    log("I am a baby rat")

elif my_type.is_rat_king_type():
    log("I am a rat king")

elif my_type.is_cat_type():
    log("I am a cat")
```

---

# 7. TrapType

`TrapType` describes the available trap types.

The supplied API defines:

- `RAT_TRAP`
- `CAT_TRAP`
- `NONE`

## 7.1 Trap Attributes

| Attribute | RAT_TRAP | CAT_TRAP | NONE |
|---|---:|---:|---:|
| Build cost | 30 | 10 | 0 |
| Damage | 50 | 100 | 0 |
| Stun time | 20 | 20 | 0 |
| Action cooldown | 15 | 10 | 0 |
| Maximum count | 25 | 10 | 0 |
| Trigger radius squared | 2 | 2 | 0 |

## 7.2 Available Attributes

Each trap type exposes:

```python
build_cost
damage
stun_time
action_cooldown
max_count
trigger_radius_squared
```

It also provides:

```python
ordinal()
```

Example:

```python
trap = TrapType.RAT_TRAP

log("Build cost:", trap.build_cost)
log("Damage:", trap.damage)
log("Maximum count:", trap.max_count)
```

---

# 8. RobotInfo

`RobotInfo` contains information about a robot detected by the sensing API.

It exposes the following fields:

| Field | Description |
|---|---|
| `id` | Robot ID |
| `team` | Robot's team |
| `type` | Robot's UnitType |
| `health` | Robot's health |
| `location` | Robot's location |
| `direction` | Robot's direction |
| `chirality` | Chirality value |
| `cheese_amount` | Cheese amount |
| `carrying_robot` | Information about the robot being carried |

## 8.1 Example

```python
robots = rc.sense_nearby_robots()

for robot in robots:
    log("Robot ID:", robot.id)
    log("Team:", robot.team)
    log("Type:", robot.type)
    log("Health:", robot.health)
    log("Location:", robot.location)
```

## 8.2 Detecting Enemies

```python
my_team = rc.get_team()

robots = rc.sense_nearby_robots()

for robot in robots:

    if robot.team != my_team:
        log("Enemy detected:", robot.id)
```

The `RobotInfo` object provides the information returned by the engine. It does not itself perform sensing.

---

# 9. MapInfo

`MapInfo` represents information about a map location.

It exposes these fields:

| Field | Description |
|---|---|
| `location` | Location represented by the object |
| `is_passable` | Whether the location is passable |
| `flying_robot` | Flying-robot information |
| `is_wall` | Whether the location is a wall |
| `is_dirt` | Whether the location contains dirt |
| `cheese_amount` | Cheese amount at the location |
| `trap` | Trap information |
| `has_cheese_mine` | Whether a cheese mine is present |

## 9.1 Example

```python
location = rc.get_location().add(Direction.NORTH)

if rc.can_sense_location(location):

    info = rc.sense_map_info(location)

    log("Passable:", info.is_passable)
    log("Wall:", info.is_wall)
    log("Dirt:", info.is_dirt)
    log("Cheese:", info.cheese_amount)
    log("Trap:", info.trap)
```

---

# 10. Message

`Message` represents a message received through the communication system.

The constructor in the supplied source is:

```python
Message(message_bytes, sender_id, round, source_loc)
```

It exposes:

| Field | Description |
|---|---|
| `bytes` | Message bytes |
| `sender_id` | Sender robot ID |
| `round` | Round associated with the message |
| `source_loc` | Message source location |

Example:

```python
messages = rc.read_squeaks(rc.get_round_num())

for message in messages:

    log("Sender:", message.sender_id)
    log("Round:", message.round)
    log("Location:", message.source_loc)
    log("Bytes:", message.bytes)
```

---

# 11. RobotController API

This is the main section of the reference.

`RobotController` contains the methods your bot uses to interact with the game.

The API methods are grouped into:

1. Game state and map information.
2. Movement and turning.
3. Sensing.
4. Combat and robot interactions.
5. Cheese, dirt, and traps.
6. Communication.
7. Indicators.
8. Other control methods.

All methods below are called through:

```python
rc.method_name(...)
```

---

# 12. Game State and Map Methods

## 12.1 `get_round_num()`

**Signature:**

```python
rc.get_round_num() -> int
```

Returns the current round number.

Example:

```python
round_number = rc.get_round_num()

log("Current round:", round_number)
```

## 12.2 `get_map_width()`

**Signature:**

```python
rc.get_map_width() -> int
```

Returns the width of the map.

## 12.3 `get_map_height()`

**Signature:**

```python
rc.get_map_height() -> int
```

Returns the height of the map.

Example:

```python
width = rc.get_map_width()
height = rc.get_map_height()

log("Map dimensions:", width, height)
```

## 12.4 `get_location()`

**Signature:**

```python
rc.get_location() -> MapLocation
```

Returns the current robot's location.

Example:

```python
location = rc.get_location()

log(location.x, location.y)
```

## 12.5 `get_direction()`

**Signature:**

```python
rc.get_direction() -> Direction
```

Returns the robot's current direction.

## 12.6 `get_id()`

**Signature:**

```python
rc.get_id() -> int
```

Returns the robot's ID.

## 12.7 `get_team()`

**Signature:**

```python
rc.get_team() -> Team
```

Returns the robot's team.

## 12.8 `get_type()`

**Signature:**

```python
rc.get_type() -> UnitType
```

Returns the robot's unit type.

## 12.9 `get_health()`

**Signature:**

```python
rc.get_health() -> int
```

Returns the robot's health.

## 12.10 `on_the_map(loc)`

**Signature:**

```python
rc.on_the_map(loc: MapLocation) -> bool
```

Checks whether a location is on the map.

Example:

```python
target = MapLocation(5, 5)

if rc.on_the_map(target):
    log("Location is on the map")
```

## 12.11 `is_location_occupied(loc)`

**Signature:**

```python
rc.is_location_occupied(loc: MapLocation) -> bool
```

Checks whether a location is occupied.

## 12.12 `adjacent_location(dir)`

**Signature:**

```python
rc.adjacent_location(dir: Direction) -> MapLocation
```

Returns the location adjacent to the robot in the specified direction.

Example:

```python
north_location = rc.adjacent_location(Direction.NORTH)
```

## 12.13 `get_all_locations_within_radius_squared(center, radius_squared)`

**Signature:**

```python
rc.get_all_locations_within_radius_squared(
    center: MapLocation,
    radius_squared: int
) -> list[MapLocation]
```

Returns locations within the specified squared radius of a center location.

## 12.14 `get_all_part_locations()`

**Signature:**

```python
rc.get_all_part_locations() -> list[MapLocation]
```

Returns all locations identified by the engine as part locations.

The supplied wrapper does not explain the exact meaning of "part locations."

---

# 13. Movement and Turning

Movement methods allow a robot to change its position or direction.

The API provides methods for checking movement, moving, turning, and checking cooldown readiness.

## 13.1 `can_move(dir)`

**Signature:**

```python
rc.can_move(dir: Direction) -> bool
```

Checks whether the robot can move in the specified direction.

Example:

```python
if rc.can_move(Direction.NORTH):
    log("North movement is possible")
```

## 13.2 `move(dir)`

**Signature:**

```python
rc.move(dir: Direction) -> None
```

Attempts to move the robot in the specified direction.

Example:

```python
if rc.can_move(Direction.EAST):
    rc.move(Direction.EAST)
```

## 13.3 `can_move_forward()`

**Signature:**

```python
rc.can_move_forward() -> bool
```

Checks whether the robot can move forward.

## 13.4 `move_forward()`

**Signature:**

```python
rc.move_forward() -> None
```

Attempts to move the robot forward.

## 13.5 `can_turn(dir=...)`

**Signature:**

```python
rc.can_turn(dir: Direction = ...) -> bool
```

Checks whether turning is possible.

The supplied wrapper supports both:

```python
rc.can_turn()
```

and:

```python
rc.can_turn(Direction.NORTH)
```

## 13.6 `turn(dir)`

**Signature:**

```python
rc.turn(dir: Direction) -> None
```

Attempts to turn the robot toward the specified direction.

Example:

```python
if rc.can_turn(Direction.WEST):
    rc.turn(Direction.WEST)
```

## 13.7 Movement Readiness

### `is_movement_ready()`

```python
rc.is_movement_ready() -> bool
```

Returns whether movement is ready.

### `is_turning_ready()`

```python
rc.is_turning_ready() -> bool
```

Returns whether turning is ready.

### `is_action_ready()`

```python
rc.is_action_ready() -> bool
```

Returns whether the action channel is ready.

## 13.8 Cooldown Methods

### `get_movement_cooldown_turns()`

```python
rc.get_movement_cooldown_turns() -> int
```

Returns the movement cooldown in turns.

### `get_turning_cooldown_turns()`

```python
rc.get_turning_cooldown_turns() -> int
```

Returns the turning cooldown in turns.

### `get_action_cooldown_turns()`

```python
rc.get_action_cooldown_turns() -> int
```

Returns the action cooldown in turns.

Example:

```python
if not rc.is_movement_ready():

    cooldown = rc.get_movement_cooldown_turns()

    log("Movement cooldown:", cooldown)
```

---

# 14. Sensing Methods

Sensing allows your robot to inspect its surroundings.

The API provides methods for sensing locations, robots, map information, and passability.

## 14.1 `can_sense_location(loc)`

**Signature:**

```python
rc.can_sense_location(loc: MapLocation) -> bool
```

Checks whether a particular location can be sensed.

Example:

```python
target = rc.get_location().add(Direction.NORTH)

if rc.can_sense_location(target):
    log("Location is within sensing range")
```

## 14.2 `can_sense_robot(id)`

**Signature:**

```python
rc.can_sense_robot(id: int) -> bool
```

Checks whether a robot with the specified ID can be sensed.

## 14.3 `can_sense_robot_at_location(loc)`

**Signature:**

```python
rc.can_sense_robot_at_location(loc: MapLocation) -> bool
```

Checks whether a robot at the specified location can be sensed.

## 14.4 `sense_map_info(loc)`

**Signature:**

```python
rc.sense_map_info(loc: MapLocation) -> MapInfo
```

Returns map information for a specific location.

Example:

```python
location = rc.get_location().add(Direction.NORTH)

if rc.can_sense_location(location):

    info = rc.sense_map_info(location)

    log("Wall:", info.is_wall)
    log("Dirt:", info.is_dirt)
```

## 14.5 `sense_nearby_map_infos(...)`

**Signature:**

```python
rc.sense_nearby_map_infos(
    center: MapLocation = ...,
    radius_squared: int = ...
) -> list[MapInfo]
```

Returns map information for nearby locations.

The supplied wrapper supports these forms:

```python
rc.sense_nearby_map_infos()
```

```python
rc.sense_nearby_map_infos(center)
```

```python
rc.sense_nearby_map_infos(radius_squared=20)
```

```python
rc.sense_nearby_map_infos(
    center,
    radius_squared=20
)
```

Example:

```python
map_infos = rc.sense_nearby_map_infos()

for info in map_infos:

    if info.is_wall:
        log("Wall at:", info.location)
```

## 14.6 `sense_nearby_robots(...)`

**Signature:**

```python
rc.sense_nearby_robots(
    center: MapLocation = ...,
    radius_squared: int = ...,
    team: Team = ...
) -> list[RobotInfo]
```

Returns information about nearby robots.

The supplied wrapper supports these forms:

```python
rc.sense_nearby_robots()
```

```python
rc.sense_nearby_robots(radius_squared=20)
```

```python
rc.sense_nearby_robots(
    radius_squared=20,
    team=Team.A
)
```

```python
rc.sense_nearby_robots(
    center,
    radius_squared=20,
    team=Team.A
)
```

**Important:** The wrapper explicitly rejects other argument combinations with `ValueError`.

Example:

```python
robots = rc.sense_nearby_robots()

for robot in robots:

    log(robot.id)
    log(robot.team)
    log(robot.location)
```

## 14.7 `sense_passability(loc)`

**Signature:**

```python
rc.sense_passability(loc: MapLocation) -> int
```

Returns the passability value for a location.

The wrapper declares the return type as `int`. It does not explain the passability scale or its full interpretation.

## 14.8 `sense_robot(id)`

**Signature:**

```python
rc.sense_robot(id: int) -> RobotInfo
```

Returns information about a robot using its ID.

## 14.9 `sense_robot_at_location(loc)`

**Signature:**

```python
rc.sense_robot_at_location(loc: MapLocation) -> RobotInfo
```

Returns information about a robot at a specific location.

---

# 15. Combat and Robot Interaction

These methods provide access to attacking, building rats, becoming a rat king, carrying rats, and throwing rats.

## 15.1 Attacking

### `can_attack(loc, cheese_amount=0)`

```python
rc.can_attack(
    loc: MapLocation,
    cheese_amount: int = 0
) -> bool
```

Checks whether an attack can be performed at the specified location.

The method accepts an optional cheese amount.

### `attack(loc, cheese_amount=0)`

```python
rc.attack(
    loc: MapLocation,
    cheese_amount: int = 0
) -> None
```

Attempts to attack the specified location.

Example:

```python
target = rc.get_location().add(Direction.EAST)

if rc.can_attack(target):
    rc.attack(target)
```

## 15.2 Becoming a Rat King

### `can_become_rat_king()`

```python
rc.can_become_rat_king() -> bool
```

Checks whether the robot can become a rat king.

### `become_rat_king()`

```python
rc.become_rat_king() -> None
```

Attempts to become a rat king.

Example:

```python
if rc.can_become_rat_king():
    rc.become_rat_king()
```

## 15.3 Building Rats

### `can_build_rat(loc)`

```python
rc.can_build_rat(loc: MapLocation) -> bool
```

Checks whether a rat can be built at the specified location.

### `build_rat(loc)`

```python
rc.build_rat(loc: MapLocation) -> None
```

Attempts to build a rat at the specified location.

Example:

```python
target = rc.get_location().add(Direction.NORTH)

if rc.can_build_rat(target):
    rc.build_rat(target)
```

## 15.4 Carrying Rats

### `can_carry_rat(loc)`

```python
rc.can_carry_rat(loc: MapLocation) -> bool
```

Checks whether a rat at the specified location can be carried.

### `carry_rat(loc)`

```python
rc.carry_rat(loc: MapLocation) -> None
```

Attempts to carry a rat at the specified location.

## 15.5 Dropping Rats

### `can_drop_rat(dir)`

```python
rc.can_drop_rat(dir: Direction) -> bool
```

Checks whether a carried rat can be dropped in the specified direction.

### `drop_rat(dir)`

```python
rc.drop_rat(dir: Direction) -> None
```

Attempts to drop a carried rat.

## 15.6 Throwing Rats

### `can_throw_rat()`

```python
rc.can_throw_rat() -> bool
```

Checks whether throwing a rat is possible.

### `throw_rat()`

```python
rc.throw_rat() -> None
```

Attempts to throw a rat.

## 15.7 Carrying and Throwing Status

### `is_being_carried()`

```python
rc.is_being_carried() -> bool
```

Checks whether the current robot is being carried.

### `is_being_thrown()`

```python
rc.is_being_thrown() -> bool
```

Checks whether the current robot is being thrown.

### `get_carrying()`

```python
rc.get_carrying() -> RobotInfo
```

Returns information about the robot currently being carried.

---

# 16. Cheese Methods

Cheese is a resource that can be collected and transferred.

The API exposes methods for picking up cheese, transferring cheese, and checking cheese amounts.

## 16.1 `can_pick_up_cheese(loc)`

```python
rc.can_pick_up_cheese(loc: MapLocation) -> bool
```

Checks whether cheese can be picked up at a location.

## 16.2 `pick_up_cheese(loc, amount=...)`

```python
rc.pick_up_cheese(
    loc: MapLocation,
    amount: int = ...
) -> None
```

Attempts to pick up cheese at the specified location.

The amount parameter is optional.

The supplied wrapper supports:

```python
rc.pick_up_cheese(location)
```

and:

```python
rc.pick_up_cheese(location, amount)
```

When an amount is supplied, the wrapper dispatches to a separate engine method.

## 16.3 `can_transfer_cheese(loc, cheese_amount)`

```python
rc.can_transfer_cheese(
    loc: MapLocation,
    cheese_amount: int
) -> bool
```

Checks whether the specified amount of cheese can be transferred to a location.

## 16.4 `transfer_cheese(loc, cheese_amount)`

```python
rc.transfer_cheese(
    loc: MapLocation,
    cheese_amount: int
) -> None
```

Attempts to transfer cheese.

Example:

```python
target = rc.get_location().add(Direction.NORTH)

if rc.can_transfer_cheese(target, 10):
    rc.transfer_cheese(target, 10)
```

## 16.5 Cheese Amount Methods

### `get_all_cheese()`

```python
rc.get_all_cheese() -> int
```

Returns the value reported by the all-cheese query.

### `get_global_cheese()`

```python
rc.get_global_cheese() -> int
```

Returns the global cheese amount.

### `get_raw_cheese()`

```python
rc.get_raw_cheese() -> int
```

Returns the raw cheese amount.

The supplied wrapper declares these return types but does not fully define the differences between their underlying values.

---

# 17. Dirt Methods

The API includes methods for checking, placing, and removing dirt.

## 17.1 `get_dirt()`

```python
rc.get_dirt() -> int
```

Returns the robot's dirt amount.

## 17.2 `can_place_dirt(loc)`

```python
rc.can_place_dirt(loc: MapLocation) -> bool
```

Checks whether dirt can be placed at the specified location.

## 17.3 `place_dirt(loc)`

```python
rc.place_dirt(loc: MapLocation) -> None
```

Attempts to place dirt at the specified location.

## 17.4 `can_remove_dirt(loc)`

```python
rc.can_remove_dirt(loc: MapLocation) -> bool
```

Checks whether dirt can be removed from a location.

## 17.5 `remove_dirt(loc)`

```python
rc.remove_dirt(loc: MapLocation) -> None
```

Attempts to remove dirt from the specified location.

Example:

```python
target = rc.get_location().add(Direction.NORTH)

if rc.can_remove_dirt(target):
    rc.remove_dirt(target)
```

---

# 18. Trap Methods

The API provides separate methods for rat traps and cat traps.

## 18.1 Rat Traps

### `can_place_rat_trap(loc)`

```python
rc.can_place_rat_trap(loc: MapLocation) -> bool
```

Checks whether a rat trap can be placed.

### `place_rat_trap(loc)`

```python
rc.place_rat_trap(loc: MapLocation) -> None
```

Attempts to place a rat trap.

### `can_remove_rat_trap(loc)`

```python
rc.can_remove_rat_trap(loc: MapLocation) -> bool
```

Checks whether a rat trap can be removed.

### `remove_rat_trap(loc)`

```python
rc.remove_rat_trap(loc: MapLocation) -> None
```

Attempts to remove a rat trap.

## 18.2 Cat Traps

### `can_place_cat_trap(loc)`

```python
rc.can_place_cat_trap(loc: MapLocation) -> bool
```

Checks whether a cat trap can be placed.

### `place_cat_trap(loc)`

```python
rc.place_cat_trap(loc: MapLocation) -> None
```

Attempts to place a cat trap.

### `can_remove_cat_trap(loc)`

```python
rc.can_remove_cat_trap(loc: MapLocation) -> bool
```

Checks whether a cat trap can be removed.

### `remove_cat_trap(loc)`

```python
rc.remove_cat_trap(loc: MapLocation) -> None
```

Attempts to remove a cat trap.

## 18.3 Trap Count Methods

### `get_number_rat_traps()`

```python
rc.get_number_rat_traps() -> int
```

Returns the number of rat traps reported by the engine.

### `get_number_cat_traps()`

```python
rc.get_number_cat_traps() -> int
```

Returns the number of cat traps reported by the engine.

### `get_current_rat_cost()`

```python
rc.get_current_rat_cost() -> int
```

Returns the current rat-building cost.

---

# 19. Communication Methods

The API provides two communication mechanisms in the supplied wrapper:

1. Shared array.
2. Squeak messages.

## 19.1 Shared Array

The supplied constants define:

```python
SHARED_ARRAY_SIZE = 64
COMM_ARRAY_MAX_VALUE = 1023
```

### `read_shared_array(index)`

```python
rc.read_shared_array(index: int) -> int
```

Reads a value from a shared-array index.

Example:

```python
value = rc.read_shared_array(0)

log("Shared value:", value)
```

### `write_shared_array(index, value)`

```python
rc.write_shared_array(
    index: int,
    value: int
) -> None
```

Writes a value to a shared-array index.

Example:

```python
rc.write_shared_array(0, 100)
```

## 19.2 Squeak Messages

### `squeak(squeak)`

```python
rc.squeak(squeak: int) -> None
```

Sends an integer squeak value.

Example:

```python
rc.squeak(123)
```

### `read_squeaks(roundNum)`

```python
rc.read_squeaks(roundNum: int) -> list[Message]
```

Reads squeak messages for the specified round.

Example:

```python
current_round = rc.get_round_num()

messages = rc.read_squeaks(current_round)

for message in messages:

    log("Message from:", message.sender_id)
    log("Message round:", message.round)
    log("Message data:", message.bytes)
```

The supplied constants include:

```python
MESSAGE_ROUND_DURATION = 5
MAX_MESSAGES_SENT_ROBOT = 1
SQUEAK_RADIUS_SQUARED = 16
```

These are reference values from `GameConstants`.

---

# 20. Indicator Methods

Indicators help display information about a bot during debugging or visualization.

The API provides methods for dots, lines, strings, and timeline markers.

## 20.1 `set_indicator_dot(loc, r, g, b)`

```python
rc.set_indicator_dot(
    loc: MapLocation,
    r: int,
    g: int,
    b: int
) -> None
```

Sets a colored indicator dot at a location.

Example:

```python
location = rc.get_location()

rc.set_indicator_dot(
    location,
    255,
    0,
    0
)
```

## 20.2 `set_indicator_string(text)`

```python
rc.set_indicator_string(text: str) -> None
```

Sets an indicator string.

Example:

```python
rc.set_indicator_string("Searching for enemies")
```

The supplied constants define:

```python
INDICATOR_STRING_MAX_LENGTH = 256
```

## 20.3 `set_indicator_line(startLoc, endLoc, r, g, b)`

```python
rc.set_indicator_line(
    startLoc: MapLocation,
    endLoc: MapLocation,
    r: int,
    g: int,
    b: int
) -> None
```

Draws a colored line between two locations.

Example:

```python
start = rc.get_location()
end = start.add(Direction.NORTH)

rc.set_indicator_line(
    start,
    end,
    0,
    255,
    0
)
```

## 20.4 `set_timeline_marker(text, r, g, b)`

```python
rc.set_timeline_marker(
    text: str,
    r: int,
    g: int,
    b: int
) -> None
```

Adds a colored timeline marker.

The supplied constants define:

```python
TIMELINE_LABEL_MAX_LENGTH = 64
```

---

# 21. Other RobotController Methods

## 21.1 `get_backstabbing_team()`

```python
rc.get_backstabbing_team() -> Team
```

Returns the backstabbing team reported by the engine.

The wrapper does not further define the meaning of this value.

## 21.2 `is_cooperation()`

```python
rc.is_cooperation() -> bool
```

Returns the cooperation flag reported by the engine.

The wrapper does not further explain its meaning.

## 21.3 `disintegrate()`

```python
rc.disintegrate() -> None
```

Attempts to disintegrate the current robot.

## 21.4 `resign()`

```python
rc.resign() -> None
```

Resigns from the game.

---

# 22. Global Helper Functions

In addition to `RobotController`, the supplied wrapper exposes several global helper functions.

These are available through the Python game environment.

## 22.1 `log(*messages)`

**Signature:**

```python
log(*messages) -> None
```

Converts the supplied arguments to strings, joins them with spaces, and sends the result to the engine log.

Example:

```python
log("Round:", rc.get_round_num())
log("Location:", rc.get_location())
log("Health:", rc.get_health())
```

## 22.2 `bottom_left_distance_squared_to(loc1, loc2)`

**Signature:**

```python
bottom_left_distance_squared_to(loc1, loc2) -> int
```

Returns a squared-distance value using the bottom-left location convention.

## 22.3 `direction_to(loc1, loc2)`

**Signature:**

```python
direction_to(loc1, loc2) -> Direction
```

Returns the direction from one location toward another.

Example:

```python
a = MapLocation(2, 2)
b = MapLocation(5, 2)

direction = direction_to(a, b)

log(direction)
```

## 22.4 `distance_squared_to(loc1, loc2)`

**Signature:**

```python
distance_squared_to(loc1, loc2) -> int
```

Returns the squared distance between two locations.

## 22.5 `is_adjacent_to(loc1, loc2)`

**Signature:**

```python
is_adjacent_to(loc1, loc2) -> bool
```

Checks whether two locations are adjacent.

## 22.6 `is_within_distance_squared(...)`

**Signature:**

```python
is_within_distance_squared(
    loc1,
    loc2,
    distance_squared,
    theta=360,
    use_bottom_left=False
) -> bool
```

Checks whether two locations satisfy a squared-distance condition, with optional angle and bottom-left location settings.

Parameters:

| Parameter | Description |
|---|---|
| `loc1` | First location |
| `loc2` | Second location |
| `distance_squared` | Squared-distance threshold |
| `theta` | Optional angle parameter; defaults to 360 |
| `use_bottom_left` | Whether to use bottom-left distance convention |

The supplied wrapper does not fully document the angle reference or boundary behavior.

## 22.7 `get_all_type_locations(unit_type, center)`

**Signature:**

```python
get_all_type_locations(
    unit_type,
    center
) -> list[MapLocation]
```

Returns locations for the specified unit type around a center.

---

# 23. GameActionException

The API defines:

```python
GameActionException
```

It also defines the enum:

```python
GameActionExceptionType
```

A `GameActionException` stores its exception category in:

```python
exception.type
```

The exception also has string and representation methods.

## 23.1 Exception Types

| Exception type | Value | Meaning suggested by name |
|---|---:|---|
| `INTERNAL_ERROR` | 0 | Internal error |
| `NOT_ENOUGH_RESOURCE` | 1 | Not enough resources |
| `CANT_MOVE_THERE` | 2 | Cannot move there |
| `IS_NOT_READY` | 3 | Robot or action is not ready |
| `CANT_SENSE_THAT` | 4 | Cannot sense the requested target |
| `OUT_OF_RANGE` | 5 | Target is out of range |
| `CANT_DO_THAT` | 6 | Action cannot be performed |
| `NO_ROBOT_THERE` | 7 | No robot at the specified location |
| `ROUND_OUT_OF_RANGE` | 8 | Requested round is out of range |

The descriptions are interpretations of the enum names, not extended formal definitions from the wrapper source.

---

# 24. GameConstants

`GameConstants` exposes reference values used by the game.

**Important:** The supplied `classes.py` docstring explicitly states that modifying these constants on the Python side does not affect the actual game.

Use them as reference values rather than as configuration variables.

## 24.1 General Game Constants

| Constant | Value |
|---|---:|
| `SPEC_VERSION` | 1 |
| `GAME_DEFAULT_SEED` | 6370 |
| `GAME_MAX_NUMBER_OF_ROUNDS` | 2000 |
| `MAX_TEAM_EXECUTION_TIME` | 1200000000000 |
| `EXCEPTION_BYTECODE_PENALTY` | 500 |

## 24.2 Map Constants

| Constant | Value |
|---|---:|
| `MAP_MIN_HEIGHT` | 20 |
| `MAP_MAX_HEIGHT` | 60 |
| `MAP_MIN_WIDTH` | 20 |
| `MAP_MAX_WIDTH` | 60 |
| `MAX_DIRT_PERCENTAGE` | 50 |
| `MAX_WALL_PERCENTAGE` | 20 |
| `MIN_CHEESE_MINE_SPACING_SQUARED` | 25 |

## 24.3 Indicator Constants

| Constant | Value |
|---|---:|
| `INDICATOR_STRING_MAX_LENGTH` | 256 |
| `TIMELINE_LABEL_MAX_LENGTH` | 64 |

## 24.4 Team and Rat King Constants

| Constant | Value |
|---|---:|
| `INITIAL_TEAM_CHEESE` | 2500 |
| `NUMBER_INITIAL_RAT_KINGS` | 1 |
| `MAX_NUMBER_OF_RAT_KINGS` | 5 |
| `MAX_NUMBER_OF_RAT_KINGS_AFTER_CUTOFF` | 2 |
| `RAT_KING_CUTOFF_ROUND` | 1200 |
| `RAT_KING_CHEESE_CONSUMPTION` | 2 |
| `RAT_KING_HEALTH_LOSS` | 10 |
| `RAT_KING_UPGRADE_CHEESE_COST` | 50 |

## 24.5 Cheese Constants

| Constant | Value |
|---|---:|
| `CHEESE_COOLDOWN_PENALTY` | 0.01 |
| `CHEESE_MINE_SPAWN_PROBABILITY` | 0.01 |
| `CHEESE_SPAWN_RADIUS` | 4 |
| `CHEESE_SPAWN_AMOUNT` | 20 |
| `CHEESE_TRANSFER_RADIUS_SQUARED` | 9 |
| `CHEESE_PICK_UP_RADIUS_SQUARED` | 2 |

## 24.6 Building Constants

| Constant | Value |
|---|---:|
| `BUILD_ROBOT_RADIUS_SQUARED` | 4 |
| `BUILD_ROBOT_BASE_COST` | 10 |
| `BUILD_ROBOT_COST_INCREASE` | 10 |
| `NUM_ROBOTS_FOR_COST_INCREASE` | 4 |
| `BUILD_DISTANCE_SQUARED` | 2 |
| `RAT_KING_BUILD_DISTANCE_SQUARED` | 8 |
| `BUILD_ROBOT_COOLDOWN` | 10 |

## 24.7 Attack and Damage Constants

| Constant | Value |
|---|---:|
| `ATTACK_DISTANCE_SQUARED` | 2 |
| `RAT_KING_ATTACK_DISTANCE_SQUARED` | 8 |
| `THROW_DAMAGE` | 20 |
| `THROW_DAMAGE_PER_TILE` | 5 |
| `RAT_BITE_DAMAGE` | 10 |
| `CAT_SCRATCH_DAMAGE` | 50 |
| `CAT_POUNCE_MAX_DISTANCE_SQUARED` | 9 |
| `HEALTH_GRAB_THRESHOLD` | 0 |

## 24.8 Dirt and Trap-Related Constants

| Constant | Value |
|---|---:|
| `DIG_DIRT_CHEESE_COST` | 5 |
| `PLACE_DIRT_CHEESE_COST` | 3 |
| `DIG_COOLDOWN` | 25 |
| `CAT_DIG_ADDITIONAL_COOLDOWN` | 5 |

## 24.9 Communication Constants

| Constant | Value |
|---|---:|
| `MESSAGE_ROUND_DURATION` | 5 |
| `MAX_MESSAGES_SENT_ROBOT` | 1 |
| `SQUEAK_RADIUS_SQUARED` | 16 |
| `SHARED_ARRAY_SIZE` | 64 |
| `COMM_ARRAY_MAX_VALUE` | 1023 |

## 24.10 Cooldown Constants

| Constant | Value |
|---|---:|
| `COOLDOWN_LIMIT` | 10 |
| `COOLDOWNS_PER_TURN` | 10 |
| `TURNING_COOLDOWN` | 10 |
| `CHEESE_TRANSFER_COOLDOWN` | 10 |
| `MOVE_STRAFE_COOLDOWN` | 18 |

## 24.11 Carrying and Throwing Constants

| Constant | Value |
|---|---:|
| `CARRY_COOLDOWN_MULTIPLIER` | 1.5 |
| `MAX_CARRY_TOWER_HEIGHT` | 2 |
| `MAX_CARRY_DURATION` | 10 |
| `SAME_ROBOT_CARRY_COOLDOWN_TURNS` | 2 |
| `THROW_DURATION` | 4 |
| `HIT_GROUND_COOLDOWN` | 10 |
| `HIT_TARGET_COOLDOWN` | 30 |

## 24.12 Other Constants

| Constant | Value |
|---|---:|
| `CAT_SLEEP_TIME` | 2 |

---

# 25. Practical Coding Patterns

This chapter combines the API methods into simple patterns that can be used when writing a bot.

These are examples of API usage, not complete strategies.

## 25.1 Basic Turn Structure

A simple turn function might look like this:

```python
def turn():

    current_round = rc.get_round_num()
    location = rc.get_location()
    unit_type = rc.get_type()

    log("Round:", current_round)
    log("Location:", location)
    log("Unit:", unit_type)
```

## 25.2 Check Before Moving

Use the movement check before calling the movement method.

```python
def move_north():

    if rc.can_move(Direction.NORTH):

        rc.move(Direction.NORTH)

    else:

        log("Cannot move north")
```

## 25.3 Find an Enemy

Use nearby robot sensing and compare teams.

```python
def find_enemy():

    my_team = rc.get_team()

    robots = rc.sense_nearby_robots()

    for robot in robots:

        if robot.team != my_team:

            log("Enemy found:", robot.id)

            return robot

    return None
```

## 25.4 Attack an Enemy

```python
def attack_enemy():

    enemy = find_enemy()

    if enemy is None:
        return

    if rc.can_attack(enemy.location):

        rc.attack(enemy.location)
```

This example assumes the enemy information is still valid when the attack is attempted. The `can_attack` method is used as the immediate legality check.

## 25.5 Inspect Nearby Map Tiles

```python
def inspect_map():

    map_infos = rc.sense_nearby_map_infos()

    for info in map_infos:

        log("Location:", info.location)
        log("Passable:", info.is_passable)
        log("Wall:", info.is_wall)
        log("Dirt:", info.is_dirt)
        log("Cheese:", info.cheese_amount)
```

## 25.6 Check Whether a Location Is on the Map

```python
def check_location(x, y):

    location = MapLocation(x, y)

    if rc.on_the_map(location):

        log("Valid map location")

    else:

        log("Outside the map")
```

## 25.7 Read Shared Information

```python
def read_team_data():

    value = rc.read_shared_array(0)

    log("Team data:", value)
```

## 25.8 Write Shared Information

```python
def write_team_data(value):

    rc.write_shared_array(0, value)
```

## 25.9 Display Debugging Information

```python
def debug_information():

    location = rc.get_location()

    rc.set_indicator_string(
        "Round: " + str(rc.get_round_num())
    )

    rc.set_indicator_dot(
        location,
        255,
        0,
        0
    )
```

---

# 26. Important Wrapper Details

The following details come directly from the supplied `wrappers.py` implementation.

## 26.1 RobotController Uses Static Methods

The wrapper defines `RobotController` with static methods.

It also provides:

```python
rc = RobotController
```

Therefore, use:

```python
rc.get_location()
```

rather than creating an instance.

## 26.2 Engine Communication

The wrapper imports:

```python
CrossPlayMethod
send_wait_and_parse
```

from its crossplay module.

Each RobotController method sends a request to the engine using the corresponding method identifier.

The wrapper is therefore an interface to the engine rather than an independent implementation of the game rules.

## 26.3 `can_turn` Supports Two Forms

Both forms are supported:

```python
rc.can_turn()
```

```python
rc.can_turn(Direction.NORTH)
```

## 26.4 `pick_up_cheese` Supports Two Forms

Both forms are supported:

```python
rc.pick_up_cheese(location)
```

```python
rc.pick_up_cheese(location, amount)
```

The wrapper uses different engine method identifiers depending on whether the amount is supplied.

## 26.5 `sense_nearby_map_infos` Argument Combinations

The supplied wrapper supports:

```python
rc.sense_nearby_map_infos()
```

```python
rc.sense_nearby_map_infos(center)
```

```python
rc.sense_nearby_map_infos(radius_squared=20)
```

```python
rc.sense_nearby_map_infos(
    center,
    radius_squared=20
)
```

## 26.6 `sense_nearby_robots` Argument Combinations

The supplied wrapper supports:

```python
rc.sense_nearby_robots()
```

```python
rc.sense_nearby_robots(radius_squared=20)
```

```python
rc.sense_nearby_robots(
    radius_squared=20,
    team=Team.A
)
```

```python
rc.sense_nearby_robots(
    center,
    radius_squared=20,
    team=Team.A
)
```

Other combinations raise `ValueError`.

## 26.7 GameConstants Are Reference Values

The `GameConstants` docstring states that modifying these constants on the Python side does not affect the game.

---

# 27. What This API Reference Does Not Establish

The supplied `wrappers.py` and `classes.py` provide the Python-facing interface and the data exposed by the package.

They do not, by themselves, fully establish:

- The complete legality conditions for every action.
- Every action's exact resource cost.
- Every action's cooldown interactions.
- The complete sensing and visibility rules.
- Every distance and angle boundary condition.
- The full meaning of every engine-side field.
- The exact behavior of every game mechanic.
- Whether a method's behavior has changed in another package version.

For those details, consult the official Battlecode 2026 rules and the matching engine implementation.

This distinction is important: a method signature tells you how to call a method, but does not necessarily explain all the rules governing that method.

---

# 28. Recommended Learning Order

If you are learning the 2026 API, the following order is recommended.

| Step | Topic | Why it matters |
|---|---|---|
| 1 | `Direction`, `MapLocation`, `Team`, `UnitType` | These types are used throughout the API. |
| 2 | Game state methods | Learn how to identify your robot and its position. |
| 3 | Movement and cooldowns | Learn how to move and manage readiness. |
| 4 | Sensing methods | Learn how to inspect the map and nearby robots. |
| 5 | `RobotInfo` and `MapInfo` | Understand the information returned by sensing. |
| 6 | Combat and robot interactions | Learn how to attack, build, carry, and throw. |
| 7 | Cheese, dirt, and traps | Understand the resource and trap interfaces. |
| 8 | Shared arrays and squeaks | Learn how robots can communicate. |
| 9 | Indicators and logging | Make debugging easier. |
| 10 | Constants and exceptions | Improve understanding of game limits and error handling. |

---

# 29. Final Reference Summary

The supplied `battlecode26 1.2.2` Python wrapper exposes the following major API groups.

| Category | Main functionality |
|---|---|
| Game state | Round, map dimensions, robot identity, health, location |
| Map | Location checks, occupancy, adjacent locations |
| Movement | Move, move forward, turn, readiness, cooldowns |
| Sensing | Nearby robots, map information, robot information, passability |
| Combat | Attack, rat king transformation |
| Robot interactions | Build, carry, drop, throw |
| Cheese | Pick up, transfer, inspect amounts |
| Dirt | Place and remove dirt |
| Traps | Place and remove rat traps and cat traps |
| Communication | Shared array and squeak messages |
| Indicators | Dots, lines, strings, timeline markers |
| Helpers | Distance, direction, adjacency, location queries |
| Exceptions | Game action exception categories |
| Constants | Map, resource, cooldown, combat, and communication values |

**Main takeaway:** `RobotController` is the primary interface between your Python bot and the Battlecode 2026 game engine. Learn the core types first, then movement and sensing, followed by actions and communication. Always use the supplied wrapper signatures and verify game-rule details against the official 2026 specification.
