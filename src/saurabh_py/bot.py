from battlecode26 import *
from baby_rat import baby_rat_exploration, proces_baby_rat
from rat_king import *
#  in the shared array kings health gets stored at index number 0 and put them in one array of max 5 so basically it is 0,1,2,3,4,5
#  if the king is under attack also
#
#
#  ok so i will have multiple cheese mines
#
#  we gonna maintain a count of how many bots do we have in baby rats or so

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


def turn():
    # This is the data we getting from the system
    curr_location = rc.get_location()  # maplocation
    curr_turn = rc.get_round_num()  # int
    curr_raw_cheese = rc.get_raw_cheese()  # int
    curr_global_cheese = rc.get_global_cheese()  # int
    curr_all_cheese = rc.get_all_cheese()  # int
    curr_dirt_count = rc.get_dirt()  # int
    curr_dir = rc.get_direction()  # Direction object
    curr_bot = rc.get_type()  # Unit type

    if rc.get_type().is_baby_rat_type():
        proces_baby_rat(curr_raw_cheese)
    else:
        spawn_baby_rat()
        rat_king_exploration(curr_dir)
