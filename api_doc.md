# BATTLECODE 2026
# Python Player API Reference (verified against the engine)

| Item | Value |
|---|---|
| Python package | `battlecode26` **1.2.2** (`.venv/lib/python3.12/site-packages/battlecode26`) |
| Game engine | `battlecode26-java` **1.2.6** (see `engine_version.txt`) |
| Python version | 3.12 |
| Sources checked | Python: `wrappers.py`, `classes.py`, `crossplay.py`, `runner.py`. Engine: `RobotController.java`, `RobotControllerImpl.java`, `InternalRobot.java`, `GameWorld.java`, `GameConstants.java`, `UnitType.java`, `TrapType.java`, `MapLocation.java`, `CrossPlay.java` (from `~/.gradle/caches/.../battlecode26-java-1.2.6-sources.jar`) |

> **How to read this document.** The Python package is only a thin bridge: every
> `rc.*` call is sent to the Java engine, and the engine decides what happens.
> Whenever the Python package and the engine disagree, **the engine is what
> actually runs**, and this document gives the engine's behavior. Section 3
> lists every disagreement that was found.

---

# 0. Quick Answers

## 0.1 How do I get the current bot's location?

```python
def turn():
    me = rc.get_location()          # -> MapLocation
    x, y = me.x, me.y
    log("I am at", me)              # prints e.g. "I am at [12, 7]"
```

- **Returns:** a `MapLocation` (fields `x`, `y`). Valid coordinates are `0 <= x < rc.get_map_width()` and `0 <= y < rc.get_map_height()`. `(0, 0)` is the bottom-left corner and `NORTH` is `+y`.
- **Which tile is returned:**
  - `BABY_RAT` (1x1): the tile it stands on.
  - `RAT_KING` (3x3): the **center** tile of its 3x3 body.
  - `CAT` (2x2): the **bottom-left** tile of its 2x2 body.
- **All tiles of your body:** `rc.get_all_part_locations()` returns a `list[MapLocation]` (1 tile for a baby rat, 9 for a rat king, 4 for a cat).
- **Only call it inside `turn()`** (or code called from `turn()`). Calling any `rc.*` method at the top level of a file, while the bot is being loaded, raises `GameActionException(CANT_DO_THAT)`. See section 1.4.
- Another robot's location: `rc.sense_nearby_robots()` gives `RobotInfo` objects, and each one has a `.location`.

## 0.2 How much can I store in the shared array?

| Property | Value (engine) |
|---|---|
| Number of slots | **64** (`GameConstants.SHARED_ARRAY_SIZE`), indices `0` to `63` |
| Value range per slot | **0 to 1023** (`COMM_ARRAY_MAX_VALUE`), which is 10 bits |
| Total capacity | 64 × 10 bits = **640 bits** (80 bytes) |
| Initial value | every slot starts at `0` |
| Lifetime | never reset; values persist for the whole match |
| Scope | **one array per team**. Your team cannot read the enemy's array, and they cannot read yours |
| Who can write | **only `RAT_KING`s**. A baby rat calling `write_shared_array` raises `GameActionException(CANT_DO_THAT)` |
| Who can read | every robot on the team (baby rats and rat kings) |
| Cost | no cooldown and no cheese cost |
| Visibility of a write | immediate: robots that act after the write in the same round already see the new value |

Rules that are easy to get wrong:
- `write_shared_array(index, value)` raises `CANT_DO_THAT` if `index` is not in 0..63 **or** `value` is not in 0..1023. Negative numbers are rejected, so pack data into unsigned 10-bit fields.
- `read_shared_array(index)` is **not bounds-checked** by the engine. An out-of-range index causes a Java `ArrayIndexOutOfBoundsException` on the engine side, not a clean `GameActionException`. Always keep the index in 0..63.
- **A full map location does not fit in one slot.** x and y each go up to 59, which needs 6 bits each (12 bits in total), but a slot holds only 10. Either use two slots (one for `x`, one for `y`; see 17.4), or store a coarse location in one slot: `(x // 2) * 32 + (y // 2)` is at most 29·32+29 = 957, which fits.

---

# 1. Architecture and Sandbox Rules

## 1.1 `rc` is a class with static methods

`wrappers.py` defines `class RobotController` with only `@staticmethod`s, plus the alias `rc = RobotController`. Never create an instance; just call `rc.get_location()`.

Each call sends a JSON request over a socket to the Java engine (`send_wait_and_parse`) and waits for the reply. Returned engine objects are turned into the Python classes in `classes.py`.

## 1.2 What a bot file looks like

```python
from battlecode26 import *     # gives rc, Direction, MapLocation, Team, UnitType, ...

def turn():                    # REQUIRED. Called once per round for each of your robots.
    if rc.get_type().is_baby_rat_type():
        ...
```

A bot **must** define `turn()`, otherwise `SyntaxError("Couldn't find turn() function.")` is raised.

## 1.3 Each robot has its own private Python globals

Every robot runs in its own `RobotRunner` with its **own globals dictionary**. A module-level variable in `bot.py` is private to that one robot. It persists across that robot's turns, but it is **not** shared with your other robots. Use the shared array (rat kings write) or squeaks to communicate.

Tip: keep per-robot state in a mutable container (for example `state = {"target": None}` and then `state["target"] = loc`). Mutating it needs no `global` statement.

## 1.4 What is allowed while the file is loading (top-level code)

While your module is imported (before the first `turn()`), the engine accepts only these calls:
`log`, `distance_squared_to`, `bottom_left_distance_squared_to`, `direction_to`, `is_adjacent_to`, `is_within_distance_squared`, `get_all_type_locations`.

Any `rc.*` call at the top level raises `GameActionException(CANT_DO_THAT, "... can only be called in the turn() function.")`.

## 1.5 Imports

Only these modules can be imported: `random`, `math`, `enum`, `battlecode26`, and **your own files in the same package** (for example `import path_finding`). Relative imports (`from . import x`) are not supported. Every `import` statement re-executes the imported file, so import at the top of the file only, not inside `turn()`. Circular imports raise `ImportError`.

## 1.6 Builtins that are NOT available in the sandbox

The sandbox only provides RestrictedPython's `safe_builtins` + `limited_builtins` plus `range`, `enumerate`, `set`, `frozenset`, `sorted`, `open`.

| Available | `abs`, `bool`, `bytes`, `callable`, `chr`, `complex`, `divmod`, `enumerate`, `float`, `frozenset`, `hash`, `hex`, `id`, `int`, `isinstance`, `issubclass`, `len`, `list`, `oct`, `ord`, `pow`, `range`, `repr`, `round`, `set`, `setattr`, `delattr`, `slice`, `sorted`, `str`, `tuple`, `zip` |
|---|---|
| **NOT available** | **`min`, `max`, `sum`, `any`, `all`, `map`, `filter`, `reversed`, `dict()`, `print`** |

Using a missing builtin raises `NameError`. Workarounds: write your own `if a < b` comparisons, use `log()` instead of `print`, and use `{}` dict literals instead of `dict()` (literals are syntax, not a builtin).

## 1.7 Bytecode limits

Your Python code is instrumented, and each Python bytecode instruction costs 1 unit. `rc.*` calls have no extra charge beyond the Python instructions they run. If a robot runs out, its turn ends with `"Ran out of bytecode"`. The per-turn limits come from `UnitType.bytecode_limit`: `BABY_RAT` 17500, `RAT_KING` 20000.

## 1.8 `MapLocation` cannot be used in sets or as dict keys

The Python `MapLocation` defines `__eq__` but not `__hash__`, so `{loc}` or `seen[loc] = 1` raises `TypeError: unhashable type: 'MapLocation'`. Use tuples instead: `seen.add((loc.x, loc.y))`.

---

# 2. Coordinate System

- `x` grows to the **east** (right) and `y` grows to the **north** (up).
- `(0, 0)` is the bottom-left corner of the map.
- Map width and height are each between 20 and 60 (`MAP_MIN_*` / `MAP_MAX_*`).
- "Distance" is almost always **squared Euclidean distance**: `dx*dx + dy*dy`. The 8 neighbors of a tile are at distance² 1 (orthogonal) or 2 (diagonal).
- Multi-tile robots (rat king 3x3, cat 2x2) occupy several tiles. Distances for the cat are measured from the center of its 2x2 block (see `bottom_left_distance_squared_to`).

---

# 3. Known Discrepancies and Bugs (read this first)

## 3.1 Methods that are broken in this version

| Method | Problem | What happens | What to do |
|---|---|---|---|
| `rc.set_indicator_dot(loc, r, g, b)` | The engine handler checks for **3** parameters, but Python sends 4 (and the handler reads 4) | Engine throws an uncaught `CrossPlayException("Invalid number of parameters ... expected 3, got 4")`. This is not a `GameActionException` and it terminates that robot's engine thread | **Do not call it.** Use `rc.set_indicator_line(loc, loc, r, g, b)` to draw a single-tile mark instead |
| `is_within_distance_squared(...)` | Python sends 5 parameters (`loc1, loc2, dist², theta, use_bottom_left`), but the engine method it calls needs 6 (it also needs a **facing `Direction`**) | Same uncaught `CrossPlayException` | **Do not call it.** Compute `dx*dx + dy*dy <= r2` yourself |

## 3.2 Return types that differ from the Python type hints

| Method | Python hint | Real return value |
|---|---|---|
| `rc.sense_passability(loc)` | `int` | **`bool`** |
| `rc.squeak(value)` | `None` | **always `None`** in Python. The engine returns `True`/`False` but the wrapper drops it, so you cannot tell whether the squeak was sent |
| `bottom_left_distance_squared_to(a, b)` | `int` | **`float`** |
| `rc.get_backstabbing_team()` | `Team` | `Team`, or **`None`** while still in cooperation mode |
| `rc.get_carrying()` | `RobotInfo` | `RobotInfo`, or **`None`** if not carrying |
| `rc.sense_robot_at_location(loc)` | `RobotInfo` | `RobotInfo`, or **`None`** if the tile is empty |
| `Message.source_loc` | `MapLocation` | **a raw `dict`** like `{"type": 3, "x": 5, "y": 7}`. Read `m.source_loc["x"]`, `m.source_loc["y"]` |

## 3.3 Python-side stat tables are stale

`UnitType`, `TrapType` and `GameConstants` in Python are local copies of the numbers. They are **not** read from the engine. `rc.get_type()` returns the Python enum member, so `rc.get_type().health` gives the **stale** value. The engine values are what the game actually uses:

| Value | Python says | **Engine (real)** |
|---|---:|---:|
| `UnitType.RAT_KING.health` | 500 | **600** |
| `UnitType.CAT.health` | 10000 | **4000** |
| `UnitType.CAT.action_cooldown` | 15 | **30** |
| `TrapType.RAT_TRAP.build_cost` | 30 | **20** |
| `TrapType.RAT_TRAP.stun_time` | 20 | **30** |
| `GameConstants.BUILD_ROBOT_RADIUS_SQUARED` | 4 | **8** |
| `GameConstants.PLACE_DIRT_CHEESE_COST` | 3 | **0** |
| `GameConstants.THROW_DAMAGE` | 20 | **10** |
| `GameConstants.THROW_DAMAGE_PER_TILE` | 5 | **4** |
| `GameConstants.CAT_SCRATCH_DAMAGE` | 50 | **20** |
| `GameConstants.CAT_POUNCE_MAX_DISTANCE_SQUARED` | 9 | **13** |
| `GameConstants.HIT_TARGET_COOLDOWN` | 30 | **20** |
| `GameConstants.CHEESE_SPAWN_RADIUS` | 4 | renamed `SQ_CHEESE_SPAWN_RADIUS` = 4 |
| `CAT_TRAP_ROUNDS_AFTER_BACKSTAB` | missing | **100** |
| `CAT_BUILD_DISTANCE_SQUARED` | missing | **4.5** |
| `THROW_RAT_COOLDOWN` | missing | **20** |
| `TILES_FLOWN_PER_TURN` | missing | **2** |

## 3.4 Engine quirks worth knowing

- `CARRY_COOLDOWN_MULTIPLIER = 1.5` is cast to `int` (giving 1) before it is used, so **carrying a rat does not increase any cooldown** in engine 1.2.6.
- `can_move(Direction.CENTER)` returns `True` and `move(Direction.CENTER)` "succeeds": it keeps you in place but still charges movement cooldown. Never pass `CENTER` to `move`.
- `is_adjacent_to(a, a)` is `True` (a tile counts as adjacent to itself).
- Javadoc for `can_build_rat` says "radius sqrt(4)", but the code uses `BUILD_ROBOT_RADIUS_SQUARED = 8` measured from the king's center.

---

# 4. Core Types

## 4.1 `Team`

| Member | `ordinal()` |
|---|---:|
| `Team.A` | 0 |
| `Team.B` | 1 |
| `Team.NEUTRAL` | 2 (cats belong to this team) |

| Method | Input | Output | Notes |
|---|---|---|---|
| `team.opponent()` | none | `Team` | A↔B. `NEUTRAL.opponent()` is `NEUTRAL` |
| `team.ordinal()` | none | `int` | see table above |

```python
enemy = rc.get_team().opponent()
```

## 4.2 `Direction`

| Member | dx | dy | `ordinal()` |
|---|---:|---:|---:|
| `NORTH` | 0 | +1 | 0 |
| `NORTHEAST` | +1 | +1 | 1 |
| `EAST` | +1 | 0 | 2 |
| `SOUTHEAST` | +1 | -1 | 3 |
| `SOUTH` | 0 | -1 | 4 |
| `SOUTHWEST` | -1 | -1 | 5 |
| `WEST` | -1 | 0 | 6 |
| `NORTHWEST` | -1 | +1 | 7 |
| `CENTER` | 0 | 0 | 8 |

Fields: `d.dx` (int) and `d.dy` (int).

| Method | Input | Output | Notes |
|---|---|---|---|
| `d.opposite()` | none | `Direction` | 180° turn. `CENTER` → `CENTER` |
| `d.rotate_left()` | none | `Direction` | 45° **counter-clockwise** (NORTH → NORTHWEST). `CENTER` → `CENTER` |
| `d.rotate_right()` | none | `Direction` | 45° **clockwise** (NORTH → NORTHEAST). `CENTER` → `CENTER` |
| `d.get_delta_x()` | none | `int` | same as `d.dx` |
| `d.get_delta_y()` | none | `int` | same as `d.dy` |
| `d.ordinal()` | none | `int` | 0..8 as above |
| `Direction.all_directions()` | none | `list[Direction]` | all **9** members, *including* `CENTER`. Call it **on the class**: `Direction.NORTH.all_directions()` raises `TypeError` |
| `Direction.cardinal_directions()` | none | `list[Direction]` | `[NORTH, EAST, SOUTH, WEST]`. Call it on the class |

The Java `Direction.fromDelta(dx, dy)` does **not** exist in Python.

## 4.3 `MapLocation`

`MapLocation(x: int, y: int)`, with fields `x` and `y`. Calling `str()` gives `"[x, y]"`; `repr()` gives `"MapLocation(x, y)"`.

| Method | Input | Output | Notes |
|---|---|---|---|
| `loc.add(dir)` | `Direction` | new `MapLocation` | `(x+dx, y+dy)`. Does not check map bounds |
| `loc.subtract(dir)` | `Direction` | new `MapLocation` | `(x-dx, y-dy)` |
| `loc.translate(dx, dy)` | `int, int` | new `MapLocation` | `(x+dx, y+dy)` |
| `a == b` | `MapLocation` | `bool` | equal when x and y match. Comparing with a non-`MapLocation` gives `False` |

Not available on the Python object (unlike Java): `distance_squared_to`, `direction_to`, `is_adjacent_to`, `is_within_distance_squared`. Use the **global helper functions** in section 15, or do the arithmetic yourself, which is cheaper because it needs no engine round-trip. The object is **not hashable** (section 1.8).

## 4.4 `UnitType`

| Attribute (Python name) | BABY_RAT | RAT_KING | CAT |
|---|---:|---:|---:|
| `health` (starting/max HP) | 100 | **600** (Python says 500) | **4000** (Python says 10000) |
| `size` (side length; tiles = size²) | 1 | 3 | 2 |
| `vision_cone_radius_squared` | 20 | 25 | 17 |
| `vision_cone_angle` (degrees, centered on facing direction) | **90** | 360 | 180 |
| `action_cooldown` (added per attack) | 10 | 10 | **30** (Python says 15) |
| `movement_cooldown` (added per move) | 10 (forward) / 18 (any other direction) | 40 | 20 |
| `bytecode_limit` | 17500 | 20000 | 17500 |

> The Python attribute names are `vision_cone_radius_squared` and `vision_cone_angle`
> (not "vision radius" / "vision angle"). Bold numbers are the engine values (section 3.3).

| Method | Output | True for |
|---|---|---|
| `t.uses_bottom_left_location_for_distance()` | `bool` | `CAT` (even size) |
| `t.is_robot_type()` | `bool` | all three |
| `t.is_throwable_type()` | `bool` | `BABY_RAT` |
| `t.is_throwing_type()` | `bool` | `BABY_RAT` |
| `t.is_baby_rat_type()` | `bool` | `BABY_RAT` |
| `t.is_rat_king_type()` | `bool` | `RAT_KING` |
| `t.is_cat_type()` | `bool` | `CAT` |
| `t.ordinal()` | `int` | BABY_RAT 0, RAT_KING 1, CAT 2 |

For the tiles a unit type would occupy, use the global `get_all_type_locations(unit_type, center)` (section 15).

## 4.5 `TrapType`

| Attribute | RAT_TRAP | CAT_TRAP | NONE |
|---|---:|---:|---:|
| `build_cost` (cheese) | **20** (Python says 30) | 10 | 0 |
| `damage` | 50 | 100 | 0 |
| `stun_time` (victim's movement cooldown is **set** to this) | **30** (Python says 20) | 20 | 0 |
| `action_cooldown` (added to the builder) | 15 | 10 | 0 |
| `max_count` (active traps per team) | 25 | 10 | 0 |
| `trigger_radius_squared` | 2 | 2 | 0 |

Also `trap.ordinal()` gives RAT_TRAP 0, CAT_TRAP 1, NONE 2.

- Rat traps are triggered by enemy **rats** (baby rats and rat kings). Cat traps are triggered by **cats**. Your own team never triggers your traps.
- When an enemy triggers one of your **rat traps**, your team is marked as the backstabber (see `is_cooperation`).

## 4.6 `RobotInfo` (a snapshot of a robot; it is not updated later)

| Field (Python) | Type | Meaning |
|---|---|---|
| `id` | `int` | unique robot ID |
| `team` | `Team` | `A`, `B`, or `NEUTRAL` (cats) |
| `type` | `UnitType` | |
| `health` | `int` | current HP |
| `location` | `MapLocation` | designated center (see 0.1) |
| `direction` | `Direction` | facing direction |
| `chirality` | `int` | used by cats only |
| `cheese_amount` | `int` | **raw** cheese that robot carries |
| `carrying_robot` | `RobotInfo` or `None` | robot it is carrying |

The Python field is `id` (lowercase), not `ID`. There are no getter methods; read the fields directly.

## 4.7 `MapInfo` (one tile)

| Field | Type | Meaning |
|---|---|---|
| `location` | `MapLocation` | the tile |
| `is_passable` | `bool` | `False` if wall, dirt, **or a thrown rat is flying over it**. Standing robots do **not** make a tile impassable (check occupancy separately) |
| `flying_robot` | `RobotInfo` or `None` | a thrown rat currently over this tile |
| `is_wall` | `bool` | permanent wall |
| `is_dirt` | `bool` | dirt (removable, see section 9) |
| `cheese_amount` | `int` | cheese lying on the tile |
| `trap` | `TrapType` | **only your own team's traps are visible**. Enemy traps always show as `TrapType.NONE` |
| `has_cheese_mine` | `bool` | a cheese mine that periodically spawns cheese nearby |

These are plain attributes, not methods: `info.is_wall`, not `info.is_wall()`.

## 4.8 `Message` (a squeak)

| Field | Type | Meaning |
|---|---|---|
| `bytes` | `int` | the 32-bit integer that was squeaked |
| `sender_id` | `int` | ID of the sender |
| `round` | `int` | round it was sent |
| `source_loc` | **`dict`** | `{"type": 3, "x": ..., "y": ...}`. **Not** a `MapLocation` (wrapper bug). Convert with `MapLocation(m.source_loc["x"], m.source_loc["y"])` |

`Message` is not injected as a builtin; it is available through `from battlecode26 import *`.

## 4.9 `GameActionException`

Raised by `rc.*` methods when an action is illegal. Fields: `e.type` (a `GameActionExceptionType`) and the message `str(e)`.

```python
try:
    rc.move(Direction.NORTH)
except GameActionException as e:
    log("move failed:", e.type, e)
```

| `GameActionExceptionType` | value | Typical cause |
|---|---:|---|
| `INTERNAL_ERROR` | 0 | engine bug |
| `NOT_ENOUGH_RESOURCE` | 1 | (not used by the 1.2.6 RobotController; missing cheese raises `CANT_DO_THAT`) |
| `CANT_MOVE_THERE` | 2 | target tile occupied or impassable |
| `IS_NOT_READY` | 3 | cooldown ≥ 10, or you are being carried/thrown |
| `CANT_SENSE_THAT` | 4 | location off-map or outside your vision cone, or robot not visible |
| `OUT_OF_RANGE` | 5 | target outside action range, or a move would leave the map |
| `CANT_DO_THAT` | 6 | everything else (wrong unit type, not enough cheese, bad index, ...) |
| `NO_ROBOT_THERE` | 7 | (not used by the 1.2.6 RobotController) |
| `ROUND_OUT_OF_RANGE` | 8 | (not used by the 1.2.6 RobotController) |

Calling the `can_*` version first is cheaper and avoids the exception.

---

# 5. Game-State Methods

| Method | Input | Output | Details |
|---|---|---|---|
| `rc.get_round_num()` | none | `int` | current round; the **first round is 1** |
| `rc.get_map_width()` | none | `int` | valid x: `0 .. width-1` |
| `rc.get_map_height()` | none | `int` | valid y: `0 .. height-1` |
| `rc.get_id()` | none | `int` | this robot's ID |
| `rc.get_team()` | none | `Team` | |
| `rc.get_type()` | none | `UnitType` | the robot's current type (changes from `BABY_RAT` to `RAT_KING` after `become_rat_king`) |
| `rc.get_health()` | none | `int` | current HP |
| `rc.get_location()` | none | `MapLocation` | designated center (see 0.1) |
| `rc.get_all_part_locations()` | none | `list[MapLocation]` | **every tile this robot occupies**: 1 (baby rat), 9 (rat king), 4 (cat) |
| `rc.get_direction()` | none | `Direction` | facing direction (it controls the vision cone) |
| `rc.is_cooperation()` | none | `bool` | `True` while both teams are in cooperation mode; `False` after any backstab (see below) |
| `rc.get_backstabbing_team()` | none | `Team` or `None` | the team that backstabbed first; `None` while still cooperating |
| `rc.get_number_rat_traps()` | none | `int` | number of **your team's** active rat traps (max 25) |
| `rc.get_number_cat_traps()` | none | `int` | number of **your team's** active cat traps (max 10) |

**Backstab:** the game starts in cooperation mode. It ends permanently the first time a team bites an enemy non-cat robot, grabs an enemy rat, or has one of its rat traps triggered by an enemy. That team becomes the "backstabbing team".

---

# 6. Cheese and Resource Queries

| Method | Input | Output | Details |
|---|---|---|---|
| `rc.get_raw_cheese()` | none | `int` | cheese **this robot is carrying**. Always 0 for a rat king, because a king's cheese goes straight to the team pool |
| `rc.get_global_cheese()` | none | `int` | the **team's shared cheese pool** (starts at 2500) |
| `rc.get_all_cheese()` | none | `int` | `raw + global`: everything this robot can spend |
| `rc.get_dirt()` | none | `int` | the **team's** dirt stock (shared by the team, not per robot). Removing dirt adds 1; placing dirt uses 1 |
| `rc.get_current_rat_cost()` | none | `int` | cheese a king needs to spawn the next baby rat: `10 + 10 × floor(your_baby_rat_count / 4)` |

**Spending order:** when a baby rat pays for something (traps, digging, bite cheese), the cost is taken from its raw cheese first, and any remainder comes from the team pool.

**Rat king upkeep:** each king eats `RAT_KING_CHEESE_CONSUMPTION = 2` cheese per round from the team pool. In any round where the pool has fewer than 2 cheese, the king loses `RAT_KING_HEALTH_LOSS = 10` HP instead.

**Carry penalty:** a baby rat's movement **and** action cooldown costs are multiplied by `(1 + 0.01 × raw_cheese)`. Turning is not affected.

---

# 7. Vision and Sensing

A location is **sensable** when it is on the map, within `vision_cone_radius_squared` of you, **and** within `vision_cone_angle / 2` degrees of your facing direction. A baby rat only sees a 90° cone in front of it; the king sees all around (360°). Your own tile is always sensable.

| Method | Input | Output | Raises / returns False when |
|---|---|---|---|
| `rc.on_the_map(loc)` | `MapLocation` | `bool` | never raises. Checks only map bounds |
| `rc.can_sense_location(loc)` | `MapLocation` | `bool` | `False` if off-map or outside the vision cone |
| `rc.is_location_occupied(loc)` | `MapLocation` | `bool` (robot there?) | raises `CANT_SENSE_THAT` if the tile is not sensable |
| `rc.can_sense_robot_at_location(loc)` | `MapLocation` | `bool` | `True` only if sensable **and** a robot is there. Never raises |
| `rc.sense_robot_at_location(loc)` | `MapLocation` | `RobotInfo` or `None` | raises `CANT_SENSE_THAT` if not sensable; `None` if empty. For a multi-tile robot, any of its tiles returns it |
| `rc.can_sense_robot(id)` | `int` | `bool` | `False` if the robot does not exist, **is currently being thrown**, or its location is not sensable |
| `rc.sense_robot(id)` | `int` | `RobotInfo` | raises `CANT_SENSE_THAT` whenever `can_sense_robot(id)` is `False` |
| `rc.sense_passability(loc)` | `MapLocation` | **`bool`** | `True` = no wall, no dirt, no flying rat. Raises `CANT_SENSE_THAT` if not sensable |
| `rc.sense_map_info(loc)` | `MapLocation` | `MapInfo` | raises `CANT_SENSE_THAT` if not sensable |
| `rc.adjacent_location(dir)` | `Direction` | `MapLocation` | `get_location().add(dir)`. Never raises and does **not** check the map |
| `rc.get_all_locations_within_radius_squared(center, r2)` | `MapLocation, int` | `list[MapLocation]` | only tiles within `r2` of `center` **that you can currently sense**. `r2` is capped at your vision radius; `-1` means your vision radius; `r2 < -1` raises `CANT_DO_THAT` |

## 7.1 `rc.sense_nearby_robots(...)` → `list[RobotInfo]`

Returns visible robots (never yourself), in no particular order. A multi-tile robot is included if **any** of its tiles is visible and within the radius. Each robot appears once.

| Python call form (the ONLY valid ones) | Meaning |
|---|---|
| `rc.sense_nearby_robots()` | everything you can see |
| `rc.sense_nearby_robots(radius_squared=r2)` | within `r2` of you |
| `rc.sense_nearby_robots(radius_squared=r2, team=t)` | within `r2` of you, only team `t` |
| `rc.sense_nearby_robots(center=c, radius_squared=r2, team=t)` | within `r2` of `c`, only team `t` |

- Any other combination, for example `sense_nearby_robots(team=t)` or `sense_nearby_robots(center=c)`, raises Python `ValueError`. To filter only by team, pass `radius_squared=-1`: `rc.sense_nearby_robots(radius_squared=-1, team=enemy)`.
- `r2 = -1` means your vision radius. Larger values are capped at your vision radius. `r2 < -1` raises `GameActionException(CANT_DO_THAT)`.
- Even with a custom `center`, robots must still be inside **your** vision cone.
- Cats are on `Team.NEUTRAL`.

```python
enemies = rc.sense_nearby_robots(radius_squared=-1, team=rc.get_team().opponent())
cats    = rc.sense_nearby_robots(radius_squared=-1, team=Team.NEUTRAL)
```

## 7.2 `rc.sense_nearby_map_infos(...)` → `list[MapInfo]`

| Python call form | Meaning |
|---|---|
| `rc.sense_nearby_map_infos()` | all sensable tiles |
| `rc.sense_nearby_map_infos(center=c)` | sensable tiles within vision radius of `c` |
| `rc.sense_nearby_map_infos(radius_squared=r2)` | sensable tiles within `r2` of you |
| `rc.sense_nearby_map_infos(center=c, radius_squared=r2)` | sensable tiles within `r2` of `c` |

The same radius rules apply (`-1` means vision; capped at vision; `< -1` raises `CANT_DO_THAT`). Only tiles you can sense are returned.

---

# 8. Cooldowns, Movement and Turning

## 8.1 How cooldowns work

Each robot has three independent counters: **action**, **movement** and **turning**.
- A counter is **ready** when it is `< 10` (`COOLDOWN_LIMIT`), and the robot is not being carried or thrown.
- Every round each counter goes down by 10 (`COOLDOWNS_PER_TURN`), but not below 0.
- Doing something **adds** its cost to the counter.
- Because the counters are independent, you can **turn, move and act in the same turn**.

| Method | Input | Output | Details |
|---|---|---|---|
| `rc.is_action_ready()` | none | `bool` | action cooldown < 10 and not carried/thrown |
| `rc.is_movement_ready()` | none | `bool` | movement cooldown < 10 and not carried/thrown |
| `rc.is_turning_ready()` | none | `bool` | turning cooldown < 10 and not carried/thrown |
| `rc.get_action_cooldown_turns()` | none | `int` | raw counter value |
| `rc.get_movement_cooldown_turns()` | none | `int` | raw counter value |
| `rc.get_turning_cooldown_turns()` | none | `int` | raw counter value |

## 8.2 Movement

| Method | Input | Output | Details |
|---|---|---|---|
| `rc.can_move(dir)` | `Direction` | `bool` | `True` if movement is ready **and** every tile of your body shifted by `dir` is on the map, not occupied by another robot, and passable |
| `rc.move(dir)` | `Direction` | `None` | moves one tile. Raises `IS_NOT_READY` (cooldown or carried), `OUT_OF_RANGE` (off map) or `CANT_MOVE_THERE` (occupied or impassable) |
| `rc.can_move_forward()` | none | `bool` | `can_move(rc.get_direction())` |
| `rc.move_forward()` | none | `None` | `move(rc.get_direction())` |

**Movement cost (added to the movement cooldown):**

| Unit | Cost |
|---|---|
| `BABY_RAT` moving in the direction it **faces** | 10 |
| `BABY_RAT` moving in **any other** direction (strafing) | 18 (`MOVE_STRAFE_COOLDOWN`) |
| `RAT_KING` (any direction) | 40 |
| `CAT` (any direction) | 20 |

The baby rat cost is then multiplied by `(1 + 0.01 × raw cheese)`.

- **Moving does not change your facing direction.** To move cheaply *and* look where you are going, a baby rat should `turn(d)` and then `move(d)` in the same turn. That costs 10 movement + 10 turning, so it can do it every turn, while strafing every turn costs 18 and leaves it slower.
- A rat king checks all 9 tiles of its body, so it needs a clear 3-wide path.
- Entering a tile next to an enemy trap (within its trigger radius) triggers it.
- Cats are allowed to move onto baby rats, which crushes them.

## 8.3 Turning

| Method | Input | Output | Details |
|---|---|---|---|
| `rc.can_turn()` | none | `bool` | turning cooldown < 10 and not carried/thrown |
| `rc.can_turn(dir)` | `Direction` | `bool` | the same, plus `dir` must not be `CENTER` |
| `rc.turn(dir)` | `Direction` | `None` | sets the facing to `dir` (any of the 8 directions, in a single call). Adds 10 to the turning cooldown. Raises `IS_NOT_READY` or `CANT_DO_THAT` (for `CENTER`) |

---

# 9. Building, Dirt and Traps

**Build range** (for dirt and traps), measured from your `get_location()`:
baby rat: distance² ≤ **2** (the 8 neighbors and your own tile); rat king: ≤ **8** from its center (the ring of tiles touching its 3x3 body); cat: ≤ 4.5 from its 2x2 center. The target must also be **sensable**: a baby rat has to *face* the tile it builds on.

## 9.1 Spawning baby rats (rat king only)

| Method | Input | Output |
|---|---|---|
| `rc.can_build_rat(loc)` | `MapLocation` | `bool` |
| `rc.build_rat(loc)` | `MapLocation` | `None` (raises `GameActionException` if illegal) |

Requirements:
1. You are a `RAT_KING`.
2. Action is ready.
3. `loc` is sensable and within distance² **8** of the king's center (the 16-tile ring around the 3x3 body).
4. The team pool has at least `get_current_rat_cost()` cheese.
5. `loc` is unoccupied and passable.

Effect: the cost is paid from the team pool, action cooldown increases by **10**, and the new baby rat faces the same direction as the king.

## 9.2 Becoming a rat king (baby rat only)

| Method | Input | Output |
|---|---|---|
| `rc.can_become_rat_king()` | none | `bool` |
| `rc.become_rat_king()` | none | `None` |

Requirements:
1. Action is ready.
2. The team pool has at least **50** cheese.
3. Your team has fewer than **5** kings, and fewer than **2** after round 1200.
4. All 9 tiles of the 3x3 square centered on you are on the map and passable.
5. There is no cat or rat king in that 3x3 square.
6. At least **7 allied baby rats** are in that 3x3 square, **counting yourself**.

Effect:
- **Every other robot in the 3x3 square dies**, including enemy baby rats.
- Their carried cheese and yours goes to the team pool.
- 50 cheese is paid.
- Your new HP is the sum of the allied HP in the square, capped at 600.
- Your type becomes `RAT_KING` and your location becomes the center of the 3x3.

## 9.3 Dirt

| Method | Input | Output | Requirements | Effect |
|---|---|---|---|---|
| `rc.can_place_dirt(loc)` / `rc.place_dirt(loc)` | `MapLocation` | `bool` / `None` | action ready; in build range and sensable; team dirt > 0; enough cheese for `PLACE_DIRT_CHEESE_COST` (**0** in the engine); tile is not a wall, not occupied, has no dirt, and has no cheese mine | tile becomes dirt (impassable), team dirt −1, action cooldown **+25** |
| `rc.can_remove_dirt(loc)` / `rc.remove_dirt(loc)` | `MapLocation` | `bool` / `None` | action ready; in build range and sensable; tile has dirt; rats need ≥ **5** cheese (`get_all_cheese()`) | tile becomes passable, team dirt +1, −5 cheese, action cooldown **+25** |

## 9.4 Traps

| Method | Input | Output |
|---|---|---|
| `rc.can_place_rat_trap(loc)` / `rc.place_rat_trap(loc)` | `MapLocation` | `bool` / `None` |
| `rc.can_place_cat_trap(loc)` / `rc.place_cat_trap(loc)` | `MapLocation` | `bool` / `None` |
| `rc.can_remove_rat_trap(loc)` / `rc.remove_rat_trap(loc)` | `MapLocation` | `bool` / `None` |
| `rc.can_remove_cat_trap(loc)` / `rc.remove_cat_trap(loc)` | `MapLocation` | `bool` / `None` |

**Placing a trap requires:**
1. Action is ready.
2. `loc` is in build range and sensable.
3. The tile is passable and unoccupied.
4. Your team has no trap on that tile yet.
5. The team has fewer than `max_count` traps of that type (rat 25, cat 10).
6. `get_all_cheese()` ≥ `build_cost` (rat **20**, cat 10).
7. The tile has no cheese mine.
8. For **cat traps only**: the game must still be in cooperation mode, or your team must have been backstabbed (not be the backstabber) within the last **100** rounds.

Effect: the cost is paid, and action cooldown increases by `trap.action_cooldown` (rat 15, cat 10).

**Removing a trap** requires only that it is your own trap and the tile is in build range and sensable. It needs **no action readiness, no cooldown and no cost**.

**When a trap triggers**, the victim takes `damage` and its movement cooldown is set to `stun_time`.

---

# 10. Combat and Carrying

## 10.1 Attacking (biting)

| Method | Input | Output |
|---|---|---|
| `rc.can_attack(loc, cheese_amount=0)` | `MapLocation, int` | `bool` |
| `rc.attack(loc, cheese_amount=0)` | `MapLocation, int` | `None` |

Requirements for a baby rat or rat king:
1. Action is ready.
2. `loc` is **sensable**. A baby rat must therefore be facing the target.
3. `0 < distance² ≤ 2` (baby rat: an adjacent tile) or `≤ 8` (king: tiles touching its body).
4. The tile is passable.
5. An **enemy** robot is there (bites on allies are rejected).
6. `cheese_amount ≥ 0` and `get_all_cheese() ≥ cheese_amount`.

Damage: `RAT_BITE_DAMAGE = 10`. If `cheese_amount > 0`, that cheese is spent and the bite does `10 + ceil(sqrt(cheese_amount))` damage. Action cooldown increases by the unit's `action_cooldown` (10).

Biting an enemy that is not a cat ends cooperation (your team becomes the backstabber).

## 10.2 Carrying, dropping and throwing (baby rats only)

| Method | Input | Output | Requirements | Effect |
|---|---|---|---|---|
| `rc.can_carry_rat(loc)` / `rc.carry_rat(loc)` | `MapLocation` | `bool` / `None` | action ready; you are a baby rat that is not carrying and not being carried; `loc` is adjacent and sensable; the target is a baby rat that is not being thrown and is not you; you may grab it if it is an **ally**, or it **cannot see you**, or its HP < your HP; you cannot re-grab an enemy you dropped or threw less than 2 turns ago | you pick it up; action cooldown **+20**. Grabbing an enemy ends cooperation |
| `rc.can_drop_rat(dir)` / `rc.drop_rat(dir)` | `Direction` | `bool` / `None` | action ready; carrying; the adjacent tile in `dir` is on the map, passable and empty | it is placed there safely; action cooldown **+20** |
| `rc.can_throw_rat()` / `rc.throw_rat()` | none | `bool` / `None` | action ready; carrying; the tile **in front of you** (facing direction) is on the map, passable and empty | it is thrown in your facing direction; action cooldown **+20** |
| `rc.get_carrying()` | none | `RobotInfo` or `None` | | |
| `rc.is_being_carried()` | none | `bool` | | while carried you cannot act, move or turn |
| `rc.is_being_thrown()` | none | `bool` | | while flying you cannot act, move, turn or pick up cheese |

A thrown rat flies 2 tiles per turn for up to 4 turns (`TILES_FLOWN_PER_TURN`, `THROW_DURATION`). The engine constants are `THROW_DAMAGE = 10`, `THROW_DAMAGE_PER_TILE = 4`, `HIT_GROUND_COOLDOWN = 10` and `HIT_TARGET_COOLDOWN = 20`.

---

# 11. Cheese Actions

| Method | Input | Output | Requirements | Effect |
|---|---|---|---|---|
| `rc.can_pick_up_cheese(loc)` | `MapLocation` | `bool` | you are a baby rat or rat king; `loc` is sensable and within distance² **2** (a king measures from its center, so it can only pick up cheese lying under its own 3x3 body); the tile has > 0 cheese; you are not being thrown | |
| `rc.pick_up_cheese(loc)` | `MapLocation` | `None` | same | takes **all** the cheese on the tile |
| `rc.pick_up_cheese(loc, amount)` | `MapLocation, int` | `None` | same | takes `amount`, clamped to 0..available |
| `rc.can_transfer_cheese(loc, amount)` | `MapLocation, int` | `bool` | you are a **baby rat**; action ready; at `loc` (any tile of the king's body) is an **allied rat king**; within distance² **9** and sensable; `0 < amount ≤ get_raw_cheese()` | |
| `rc.transfer_cheese(loc, amount)` | `MapLocation, int` | `None` | same | raw cheese → team pool; action cooldown **+10** |

- Picking up cheese needs **no action readiness and adds no cooldown**.
- Cheese a baby rat picks up becomes its raw cheese, which slows it down (section 6).
- Cheese a king picks up goes **directly into the team pool**.
- A baby rat's raw cheese only joins the team pool when it is transferred to a king. Until then, only that rat can spend it.

---

# 12. Communication

## 12.1 Shared array

See section **0.2** for all the rules.

| Method | Input | Output | Raises |
|---|---|---|---|
| `rc.read_shared_array(index)` | `int` (0..63) | `int` (0..1023) | nothing for valid indices. An invalid index crashes on the engine side (not bounds-checked) |
| `rc.write_shared_array(index, value)` | `int` (0..63), `int` (0..1023) | `None` | `CANT_DO_THAT` if you are not a rat king, or the index or value is out of range |

## 12.2 Squeaks (short-range messages)

| Method | Input | Output | Details |
|---|---|---|---|
| `rc.squeak(value)` | `int` (32-bit) | `None` | broadcasts `value` to every robot whose tile is within distance² **16** of your location. **Recipients are your allies AND cats**; enemy rats do not hear it. No vision or line of sight is needed. At most **1 squeak per turn**; extra calls are silently ignored (the wrapper hides the engine's `False`) |
| `rc.read_squeaks(round_num)` | `int` | `list[Message]` | squeaks this robot has received that were sent in round `round_num`. Pass **`-1`** to get every buffered squeak. Messages older than 5 rounds (`MESSAGE_ROUND_DURATION`) are discarded |

```python
# Send my position (x, y < 60 fit easily in 32 bits)
me = rc.get_location()
rc.squeak((me.x << 8) | me.y)

# Read everything received in the last 5 rounds
for m in rc.read_squeaks(-1):
    x = (m.bytes >> 8) & 0xFF
    y = m.bytes & 0xFF
    src = MapLocation(m.source_loc["x"], m.source_loc["y"])   # source_loc is a dict!
```

Squeaks sent this round are available to robots that take their turn later in the same round.

---

# 13. Indicators (debug drawing in the client)

| Method | Input | Output | Details |
|---|---|---|---|
| `rc.set_indicator_string(text)` | `str` | `None` | shown for this robot in the client; truncated to 256 characters |
| `rc.set_indicator_line(start, end, r, g, b)` | `MapLocation, MapLocation, int, int, int` | `None` | draws a line; raises `CANT_DO_THAT` if either end is off the map |
| `rc.set_timeline_marker(text, r, g, b)` | `str, int, int, int` | `None` | adds a team marker on the timeline at this round; truncated to 64 characters |
| `rc.set_indicator_dot(loc, r, g, b)` | `MapLocation, int, int, int` | — | **BROKEN in engine 1.2.6, do not call** (section 3.1). Use `rc.set_indicator_line(loc, loc, r, g, b)` instead |

---

# 14. Other RobotController Methods

| Method | Input | Output | Details |
|---|---|---|---|
| `rc.disintegrate()` | none | `None` | this robot dies immediately |
| `rc.resign()` | none | `None` | **all** your robots are destroyed and the opponent wins |

---

# 15. Global Helper Functions

These are plain functions (not `rc.` methods). They are available after `from battlecode26 import *` and are allowed at module load time. Each one is an engine round-trip, so in hot loops plain arithmetic is cheaper.

| Function | Input | Output | Details |
|---|---|---|---|
| `log(*messages)` | anything | `None` | `" ".join(str(m) for m in messages)` goes to the match log. Use this instead of `print` (not available) |
| `distance_squared_to(a, b)` | `MapLocation, MapLocation` | `int` | `(a.x-b.x)² + (a.y-b.y)²` |
| `bottom_left_distance_squared_to(a, b)` | `MapLocation, MapLocation` | **`float`** | `(a.x+0.5-b.x)² + (a.y+0.5-b.y)²` (the distance from the center of a 2x2 block whose bottom-left tile is `a`) |
| `direction_to(a, b)` | `MapLocation, MapLocation` | `Direction` | the closest of the 8 directions from `a` toward `b`; `CENTER` if `a == b`. Rule: if `|dx| ≥ 2.414·|dy|`, it is EAST or WEST; if `|dy| ≥ 2.414·|dx|`, it is NORTH or SOUTH; otherwise it is the diagonal |
| `is_adjacent_to(a, b)` | `MapLocation, MapLocation` | `bool` | `|dx| ≤ 1 and |dy| ≤ 1`. **Also `True` when `a == b`** |
| `is_within_distance_squared(a, b, d2, theta=360, use_bottom_left=False)` | | | **BROKEN, do not call** (section 3.1) |
| `get_all_type_locations(unit_type, center)` | `UnitType, MapLocation` | `list[MapLocation]` | the size² tiles a unit of that type would occupy if its designated location were `center` |

---

# 16. GameConstants (engine 1.2.6 values)

`GameConstants` in Python is only a reference copy; changing it does nothing, and several values are stale (section 3.3). The **engine** values are listed here.

| Group | Constant | Value |
|---|---|---:|
| Game | `GAME_MAX_NUMBER_OF_ROUNDS` | 2000 |
| | `GAME_DEFAULT_SEED` | 6370 |
| | `EXCEPTION_BYTECODE_PENALTY` | 500 |
| | `MAX_TEAM_EXECUTION_TIME` (ns) | 1200000000000 |
| Map | `MAP_MIN_WIDTH` / `MAP_MAX_WIDTH` | 20 / 60 |
| | `MAP_MIN_HEIGHT` / `MAP_MAX_HEIGHT` | 20 / 60 |
| | `MAX_DIRT_PERCENTAGE` / `MAX_WALL_PERCENTAGE` | 50 / 20 |
| | `MIN_CHEESE_MINE_SPACING_SQUARED` | 25 |
| Team / king | `INITIAL_TEAM_CHEESE` | 2500 |
| | `NUMBER_INITIAL_RAT_KINGS` | 1 |
| | `MAX_NUMBER_OF_RAT_KINGS` / `_AFTER_CUTOFF` | 5 / 2 |
| | `RAT_KING_CUTOFF_ROUND` | 1200 |
| | `RAT_KING_UPGRADE_CHEESE_COST` | 50 |
| | `RAT_KING_CHEESE_CONSUMPTION` (per round) | 2 |
| | `RAT_KING_HEALTH_LOSS` (per hungry round) | 10 |
| Cheese | `CHEESE_COOLDOWN_PENALTY` (per raw cheese) | 0.01 |
| | `CHEESE_MINE_SPAWN_PROBABILITY` | 0.01 |
| | `SQ_CHEESE_SPAWN_RADIUS` | 4 |
| | `CHEESE_SPAWN_AMOUNT` | 20 |
| | `CHEESE_PICK_UP_RADIUS_SQUARED` | 2 |
| | `CHEESE_TRANSFER_RADIUS_SQUARED` | 9 |
| Building | `BUILD_ROBOT_RADIUS_SQUARED` | **8** |
| | `BUILD_ROBOT_BASE_COST` / `BUILD_ROBOT_COST_INCREASE` / `NUM_ROBOTS_FOR_COST_INCREASE` | 10 / 10 / 4 |
| | `BUILD_DISTANCE_SQUARED` (rat) / `RAT_KING_BUILD_DISTANCE_SQUARED` / `CAT_BUILD_DISTANCE_SQUARED` | 2 / 8 / 4.5 |
| | `BUILD_ROBOT_COOLDOWN` | 10 |
| Dirt | `DIG_DIRT_CHEESE_COST` / `PLACE_DIRT_CHEESE_COST` | 5 / **0** |
| | `DIG_COOLDOWN` (place or remove) | 25 |
| | `CAT_DIG_ADDITIONAL_COOLDOWN` | 5 |
| Combat | `ATTACK_DISTANCE_SQUARED` / `RAT_KING_ATTACK_DISTANCE_SQUARED` | 2 / 8 |
| | `RAT_BITE_DAMAGE` | 10 |
| | `CAT_SCRATCH_DAMAGE` | **20** |
| | `CAT_POUNCE_MAX_DISTANCE_SQUARED` | **13** |
| | `HEALTH_GRAB_THRESHOLD` | 0 |
| | `CAT_TRAP_ROUNDS_AFTER_BACKSTAB` | 100 |
| Throwing | `THROW_DAMAGE` / `THROW_DAMAGE_PER_TILE` | **10** / **4** |
| | `TILES_FLOWN_PER_TURN` / `THROW_DURATION` | 2 / 4 |
| | `THROW_RAT_COOLDOWN` (carry, drop, throw) | 20 |
| | `HIT_GROUND_COOLDOWN` / `HIT_TARGET_COOLDOWN` | 10 / **20** |
| | `MAX_CARRY_TOWER_HEIGHT` / `MAX_CARRY_DURATION` | 2 / 10 |
| | `SAME_ROBOT_CARRY_COOLDOWN_TURNS` | 2 |
| | `CARRY_COOLDOWN_MULTIPLIER` | 1.5 (has no effect, section 3.4) |
| Comms | `SHARED_ARRAY_SIZE` / `COMM_ARRAY_MAX_VALUE` | 64 / 1023 |
| | `SQUEAK_RADIUS_SQUARED` / `MAX_MESSAGES_SENT_ROBOT` / `MESSAGE_ROUND_DURATION` | 16 / 1 / 5 |
| Cooldowns | `COOLDOWN_LIMIT` / `COOLDOWNS_PER_TURN` | 10 / 10 |
| | `TURNING_COOLDOWN` / `MOVE_STRAFE_COOLDOWN` | 10 / 18 |
| | `CHEESE_TRANSFER_COOLDOWN` | 10 |
| Debug | `INDICATOR_STRING_MAX_LENGTH` / `TIMELINE_LABEL_MAX_LENGTH` | 256 / 64 |
| Other | `CAT_SLEEP_TIME` | 2 |

---

# 17. Practical Patterns

## 17.1 Move from point A to point B (bug navigation)

Call `move_to(target)` **once per turn**. It takes one step (if movement is ready), goes around walls, dirt, robots and map edges by following the obstacle, and returns `True` once you have arrived. It was tested offline against a mock controller that follows the engine's movement rules (an open map, a long wall, a U-shaped trap, a two-gap maze, a wall touching the map edge, and an unreachable target), and under the sandbox's restricted builtins.

```python
from battlecode26 import *

# 8 movement directions in clockwise order (index + 1 == 45 degrees clockwise).
NAV_DIRS = [
    Direction.NORTH, Direction.NORTHEAST, Direction.EAST, Direction.SOUTHEAST,
    Direction.SOUTH, Direction.SOUTHWEST, Direction.WEST, Direction.NORTHWEST,
]

# Per-robot navigation memory. Every robot runs in its own sandbox, so this
# dict is private to the robot. It is mutated (never reassigned), so no
# `global` statement is needed.
_nav = {
    "target": None,       # (x, y) we are currently heading to
    "following": False,   # True while hugging an obstacle
    "heading": None,      # direction we last moved while hugging
    "start_dist": 0,      # distance to target when we started hugging
    "left_hand": True,    # which way we go around obstacles
    "follow_turns": 0,    # turns spent hugging without getting closer
}


def nav_dir_toward(a, b):
    """Same result as the engine's direction_to(a, b), computed locally (no engine call)."""
    dx = b.x - a.x
    dy = b.y - a.y
    adx = abs(dx)
    ady = abs(dy)
    if adx >= 2.414 * ady:
        if dx > 0:
            return Direction.EAST
        if dx < 0:
            return Direction.WEST
        return Direction.CENTER
    if ady >= 2.414 * adx:
        return Direction.NORTH if dy > 0 else Direction.SOUTH
    if dy > 0:
        return Direction.NORTHEAST if dx > 0 else Direction.NORTHWEST
    return Direction.SOUTHEAST if dx > 0 else Direction.SOUTHWEST


def nav_dist_sq(a, b):
    """Squared Euclidean distance, computed locally (no engine call)."""
    dx = a.x - b.x
    dy = a.y - b.y
    return dx * dx + dy * dy


def nav_reset():
    """Forget obstacle-following state (call when you pick a new target)."""
    _nav["target"] = None
    _nav["following"] = False
    _nav["heading"] = None
    _nav["follow_turns"] = 0


def _nav_step(d):
    """Move one tile in direction d. Baby rats turn first so they pay the
    forward move cost (10) instead of the strafe cost (18)."""
    if not rc.can_move(d):
        return False
    if rc.get_type().is_baby_rat_type() and rc.get_direction() != d and rc.can_turn(d):
        rc.turn(d)
    rc.move(d)
    return True


def move_to(target, arrive_dist_sq=0, dig=False):
    """Take ONE step from the current location toward `target` (a MapLocation).

    Call it once per turn, every turn, until it reports arrival.

    Returns:
        True  -> we are already within `arrive_dist_sq` of target (arrived)
        False -> not there yet (moved one step, or could not move this turn)

    arrive_dist_sq: stop when distance_squared <= this. Use 2 to stop adjacent
                    (e.g. when the target tile holds a robot).
    dig:            if True, a baby rat / rat king will dig through dirt that
                    blocks the direct path (costs 5 cheese + 25 action cooldown).
    """
    me = rc.get_location()
    if nav_dist_sq(me, target) <= arrive_dist_sq:
        return True

    key = (target.x, target.y)
    if _nav["target"] != key:
        nav_reset()
        _nav["target"] = key

    if not rc.is_movement_ready():
        return False

    d = nav_dir_toward(me, target)
    cur = nav_dist_sq(me, target)

    # 1) Greedy: go straight at the target, or 45 degrees either side, as long
    #    as that actually gets us closer. Leave obstacle-following if possible.
    if not _nav["following"] or cur < _nav["start_dist"]:
        for cand in (d, d.rotate_left(), d.rotate_right()):
            if nav_dist_sq(me.add(cand), target) < cur and _nav_step(cand):
                _nav["following"] = False
                return False

        # Optional: dig through dirt that sits directly in the way.
        if dig:
            ahead = me.add(d)
            if rc.can_remove_dirt(ahead):
                rc.remove_dirt(ahead)
                return False

        # Blocked -> start hugging the obstacle.
        if not _nav["following"]:
            _nav["following"] = True
            # Pre-rotate so that the first sweep below starts exactly at d.
            if _nav["left_hand"]:
                _nav["heading"] = d.rotate_left().rotate_left()
            else:
                _nav["heading"] = d.rotate_right().rotate_right()
            _nav["start_dist"] = cur
            _nav["follow_turns"] = 0

    # 2) Obstacle following (bug navigation). Start pointing back into the
    #    wall and sweep away from it until a free direction is found.
    _nav["follow_turns"] += 1
    if _nav["follow_turns"] > 2 * (rc.get_map_width() + rc.get_map_height()):
        # Going around the long way for too long: switch hands and retry.
        _nav["left_hand"] = not _nav["left_hand"]
        _nav["following"] = False
        _nav["follow_turns"] = 0
        return False

    h = _nav["heading"]
    if _nav["left_hand"]:
        h = h.rotate_right().rotate_right()      # wall is on our right
        for _ in range(8):
            if _nav_step(h):
                _nav["heading"] = h
                return False
            h = h.rotate_left()
    else:
        h = h.rotate_left().rotate_left()        # wall is on our left
        for _ in range(8):
            if _nav_step(h):
                _nav["heading"] = h
                return False
            h = h.rotate_right()
    return False   # completely boxed in this turn; try again next turn
```

Usage:

```python
TARGET = MapLocation(20, 30)

def turn():
    if move_to(TARGET):
        log("arrived at", TARGET)

    # Stop next to a robot instead of on top of it:
    # move_to(enemy_king.location, arrive_dist_sq=2)
```

Notes:
- Works for baby rats and rat kings (a king needs a 3-tile-wide gap; `rc.can_move` checks that).
- Enemy traps are invisible to you (section 4.7), so the path may still walk into one.
- Only one step per turn is possible. A baby rat walking forward has cooldown 10, so it moves every turn; a rat king (cooldown 40) moves about once every 4 turns.

## 17.2 Find and bite the nearest enemy

```python
def bite_nearest_enemy():
    me = rc.get_location()
    best = None
    best_d = 1000000
    for r in rc.sense_nearby_robots(radius_squared=-1, team=rc.get_team().opponent()):
        dx = r.location.x - me.x
        dy = r.location.y - me.y
        d = dx * dx + dy * dy
        if d < best_d:
            best, best_d = r, d
    if best is None:
        return False
    if rc.can_attack(best.location):
        rc.attack(best.location)
        return True
    move_to(best.location, arrive_dist_sq=2)
    return False
```

## 17.3 Collect cheese and bring it home

```python
def gather(king_loc):
    me = rc.get_location()
    if rc.get_raw_cheese() > 0 and rc.can_transfer_cheese(king_loc, rc.get_raw_cheese()):
        rc.transfer_cheese(king_loc, rc.get_raw_cheese())
        return
    for info in rc.sense_nearby_map_infos():
        if info.cheese_amount > 0:
            if rc.can_pick_up_cheese(info.location):
                rc.pick_up_cheese(info.location)
            else:
                move_to(info.location)
            return
    move_to(king_loc, arrive_dist_sq=9)
```

## 17.4 Rat king publishes its location to the team

```python
# Rat king (only kings may write). Slots 0 and 1 hold the king's x and y.
loc = rc.get_location()
rc.write_shared_array(0, loc.x)
rc.write_shared_array(1, loc.y)

# Any robot on the team:
king = MapLocation(rc.read_shared_array(0), rc.read_shared_array(1))
```

## 17.5 Debug drawing that works

```python
me = rc.get_location()
rc.set_indicator_string("round " + str(rc.get_round_num()))
rc.set_indicator_line(me, me, 255, 0, 0)          # dot substitute (set_indicator_dot is broken)
rc.set_indicator_line(me, TARGET, 0, 255, 0)      # line to the target
```

---

# 18. Recommended Learning Order

| Step | Topic | Sections |
|---|---|---|
| 1 | Sandbox rules (builtins, imports, per-robot globals) | 1 |
| 2 | Known bugs and stale constants | 3 |
| 3 | `Direction`, `MapLocation`, coordinates | 2, 4.2, 4.3 |
| 4 | Your own state: location, type, cheese | 0.1, 5, 6 |
| 5 | Cooldowns, movement, turning | 8 |
| 6 | Vision cone and sensing | 7 |
| 7 | Navigation pattern | 17.1 |
| 8 | Cheese economy, building, kings | 9, 11 |
| 9 | Combat and carrying | 10 |
| 10 | Communication | 0.2, 12 |
