from battlecode26 import *


directions_map = {
    "N": (0, 1),
    "NE": (1, 1),
    "E": (1, 0),
    "SE": (1, -1),
    "S": (0, -1),
    "SW": (-1, -1),
    "W": (-1, 0),
    "NW": (-1, 1),
}

directions = [
    (0, 1),  # North
    (1, 1),  # North-East
    (1, 0),  # East
    (1, -1),  # South-East
    (0, -1),  # South
    (-1, -1),  # South-West
    (-1, 0),  # West
    (-1, 1),  # North-West
]
###############################################################################
""" NOtes  """
## -> bot has a unque id 


""" This is the plain declaration of the which index is for which thing """
###############################################################################
INT32_MAX = 2**31 - 1  # 2147483647

# index 0 -> kings health 
# index 1 --> kings x cordintae
# index 2 -> kings y cordintae
# index 
# index 30,31,32 -> 30 id , 31,32 coordintes
# index 33 , 36 , 39 , 42 , 45 ,48,51,54,57,60,63
###############################################################################
def distance(curr_loc:MapLocation,final_loc:MapLocation) -> int :
    """ The distance sq using the main formula  """
    return (curr_loc.x-final_loc.x)**2 - (curr_loc.y-final_loc.y)**2;

def get_direction_to(destination : MapLocation) -> Direction:
    curr_loc = rc.get_location()
    curr_dir = rc.get_direction()
    ans = curr_dir
    minimum_dis = INT32_MAX
    for dir in Direction:
        tmp_step = curr_loc.add(dir)
        tmp_dis = distance(curr_loc,tmp_step)
        if(tmp_dis < minimum_dis):
            ans = dir
            minimum_dis = tmp_dis
    return ans


#shortest path between  tywo point when we dont know the obstacles we dont know the 
def is_id_in_shared(id : int) -> int:
    for i in range(30,64,3):
        if(rc.read_shared_array(i) == id):
            return i
    return -1



def has_cheese_in_range() -> Direction:
    for info in rc.sense_nearby_map_infos():
        if info.cheese_amount >0:
            dest_dir = info.location
            return get_direction_to(dest_dir);
    return Direction.CENTER

def momentum() -> Direction:
    curr_dir =rc.get_direction()
    if rc.can_move(curr_dir) :
        rc.move(curr_dir)
    for dir in Direction.all_directions():
        if(rc.can_move(dir)):
            return dir


def has_dirt_in_range() -> Direction:
    for info in  rc.sense_nearby_map_infos():
        if info.is_dirt and rc.can_remove_dirt(info.location):
            rc.remove_dirt(info.location)
        elif info.is_dirt : 
            return get_direction_to(info.location)
        else:
            return rc.get_direction()
    return momentum()
            
def move_to(rc : RobotController) -> Direction :
    if(rc.get_type().is_baby_rat_type()):
        if rc.get_raw_cheese() > 0 :
            return get_direction_to(MapLocation(rc.read_shared_array(1),rc.read_shared_array(2)))
        if has_cheese_in_range() != Direction.CENTER :
                return has_cheese_in_range()

        curr_id = rc.get_id()
        validity = is_id_in_shared(curr_id)
        if validity:
            dest_loc = MapLocation(rc.read_shared_array(validity+1),rc.read_shared_array(validity+2))
            return get_direction_to(dest_loc)
        if has_dirt_in_range():
            return has_dirt_in_range()
        return momentum()
    else:
        if rc.get_round_num() <= 15:
            if rc.can_build_rat()





def explore(rc : RobotController):
    #oppposite direction to the spawn location 
    king_loc = MapLocation(rc.read_shared_array(1),rc.read_shared_array(2))
    
    if(rc.get_type().is_rat_king_type()):
        


def turn():
    if rc.get_type().is_baby_rat_type():
    #define process babay rat
    else:
    # process the rat king 
