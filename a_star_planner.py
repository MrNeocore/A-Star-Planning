import sys
import logging
import random
import time
from copy import deepcopy
from math import fabs

pkg_loc = {}
pkg_loc['S'] = 'A'
pkg_loc['L'] = 'B'
pkg_loc['M'] = 'T'

# World class, contains all the data about a give world
class World:
    def __init__(self, warehouseA, warehouseB, truck, robot):
        self.location = {'A':warehouseA, 'B':warehouseB, 'T':truck}
        self.robot = robot
        self.g = 10000
        self.h = 0
        self.f = 0
        self.previous = None
        self.action = "" 
    
    def getNextWorlds(self):
        worlds_list = []
        
        # The robot holding a package
        if self.robot.hold_package != None:
            for loc in self.location:  
                # Create a world where the robot moves to a new place
                if self.robot.pos != loc :
                    next = deepcopy(self)
                    next.f = 10000
                    next.h = 0
                    next.g = 10000
                    next.robot.pos = loc
                    next.action = f"Move from {self.robot.pos} to {loc}"
                    worlds_list.append(next)
                    
                else:
                    for pkg,loc2 in pkg_loc.items():   
                        # The robot is holding a package and is in the correct location of that package - put it down 
                        if loc == loc2 and self.robot.hold_package == pkg:
                            next = deepcopy(self)
                            next.f = 10000
                            next.h = 0
                            next.g = 10000
                            next.location[loc2][self.robot.hold_package] += 1
                            next.robot.hold_package = None
                            next.action = f"Putdown package {pkg} in {loc2}" 
                            worlds_list.append(next)
        
        # The robot is not holding anything
        elif self.robot.hold_package == None:       
            for loc,v in self.location.items():
                # Create a world where the robot moves to a new place - this could be merged with the previous block
                if self.robot.pos != loc :
                    next = deepcopy(self)
                    next.f = 10000
                    next.h = 0
                    next.g = 10000
                    next.robot.pos = loc
                    next.action = f"Move from {self.robot.pos} to {loc}" 
                    worlds_list.append(next)
                    
                else:
                    for pkg,loc2 in pkg_loc.items():
                        # The robot is in the location of a misplaced package - pick it up   
                        if loc != loc2 and self.location[loc][pkg] != 0:
                            next = deepcopy(self)
                            next.f = 10000
                            next.h = 0
                            next.g = 10000
                            next.robot.hold_package = pkg
                            next.location[loc][pkg] -= 1
                            next.action = f"Pickup package {pkg} in {loc}"
                            worlds_list.append(next)
        
                
        return worlds_list

       
# Robot class - data could be stored in a dictionnary           
class Robot:
    def __init__(self, pos, hold_package):
        self.pos = pos
        self.hold_package = hold_package
        

# ======= HELPER FUNCTIONS ===========

# Returns the distance between 2 depots. A different distance between places is simple to implement
def distanceDepot(loc1, loc2):
    return 1 if loc1 != loc2 else 0
    

# Returns a dictionnary of misplaced packages : {'A':{'S':X,'M':Y..},'B':{...},..}
def misplacedPackages(world1, world2):
    misplaced_dict = {}
    
    for (loc1, pkgs1), (loc2,pkgs2) in zip(world1.location.items(), world2.location.items()):
        misplaced_dict[loc1] = {}
        for (pkg3, nb3), (pkg4 ,nb4) in zip(pkgs1.items(), pkgs2.items()):
                if loc1 != pkg_loc[pkg3]:
                    misplaced_dict[loc1][pkg3] = int(fabs(nb3-nb4))
                else:
                    misplaced_dict[loc1][pkg3] = 0
     
    return misplaced_dict
   
# Returns the total sum of misplaced packages in the world "world"
def num_misplaced_packages(world, goal):
    miss = misplacedPackages(world, goal)

    count = 0
    for loc, pcks in miss.items():
        for pkgs_type, nb in pcks.items():
            count += nb  
    
    return count
            
# Return the distance from the robot to the closest misplaced package
def distance_to_closest_misplaced_package(world, goal):

    # Get dictionnary of misplaced packages 
    miss = misplacedPackages(world, goal)

    # Find closest non zero misplaced packages depot
    count = {} # {'A':X, 'B':Y..} - Sum packages misplaced per location
    for loc, pcks in miss.items():
        count[loc] = 0
        for pkgs_type, nb in pcks.items():
            count[loc] += nb  
    
    # Remove zero misplaced packages depots
    loc_to_del = []
    for depot, nb in count.items():
        if not nb:
            loc_to_del.append(depot)
    
    for depot in loc_to_del:
        del count[depot]
            
    # Getting distances between robot and depot where work is needed
    distances = {} # {'A':<DIST>, 'B':<DIST>}
    for depot in count:
        distances[depot] = distanceDepot(world.robot.pos, depot)
    
    if not distances:
        return None
        
    # Get distance from robot to closest depot where work is needed 
    closest = min(distances.items(), key=lambda x:x[1]) # (<DEPOT>,<DIST>)
    
    # Find first package in depot that is misplaced
    pkg = None
    for pkg_type, nb in miss[closest[0]].items():
        if nb:
            pkg = pkg_type
            break
    
    data = {'loc':closest[0],'dist':closest[1],'pkg':pkg}
    
    return data     


# If a world already exists in the list, returns this world, otherwise, returns the world given in parameter  
def findWorld(world_to_find, worlds_list):
    for world in worlds_list:
        if sameWorld(world_to_find, world):
            #loggin.debug("World found")
            return True, world
         
    #logging.debug("World not found, returning same")
    return False, world_to_find
   
   
# Compares 2 worlds data, if identical returns true, otherwise, returns false
def sameWorld(world1, world2):

    # We check if the packages in the different locations are the same
    for (key1, value1), (key2,value2) in zip(world1.location.items(), world2.location.items()):
        for (key3, value3), (key4,value4) in zip(value1.items(), value2.items()):
                if value3 != value4:
                    return False
           
    # We check that the roboto is at the same location and carries the same package         
    if world1.robot.pos != world2.robot.pos:           
        return False
    
    if world1.robot.hold_package != world2.robot.hold_package:
        return False
                                 
    return True  
 
# Show the final plan at the end of the search
def reconstructActionChain(world):
    actions = []
    
    # Starting from the last world, goes back to the start
    while(world.previous):
        actions.append(world.action)
        world = world.previous
       
    actions.reverse()
   
    print("\n==== Start ====\n")
    for action in actions:
        print("\t" + action)
        
    print("\n==== End ====\n")   
    print(f"{len(actions)} actions")
    
    
# ========= HEURISTICS =============

# Robot to closest misplaced package + package to correct pkg location + number of misplaced packages
def heuristic1(world, goal):
    h = 0
    
    # Add distance from robot to closest misplaced package
    mis_pkg = distance_to_closest_misplaced_package(world, goal) 
    
    if mis_pkg:
        # Returns ('loc':<LOC>, 'dist':<DIST>, 'pkg':<PKG_TYPE>)
        #print(mis_pkg)
        h += mis_pkg['dist']
        
        # Add misplaced package count
        h += num_misplaced_packages(world, goal)
        
        # Add distance from package to correct pkg location
        dist_pkg_corr = distanceDepot(mis_pkg['loc'], pkg_loc[mis_pkg['pkg']]) 
        
        # Returns distance between current pkg depot and correct pkg depot
        #print(dist_pkg_corr)
        h += dist_pkg_corr
        
        # Add distance from robot to final robot location
        #h+= distanceDepot(world.robot.pos, goal.robot.pos) * 0.1
        
    #print(f"Heuristic for world {world.action} : {h}")
    
    return h

# A simpler heuristic which makes A* 25-500x faster (increases with goal complexity)
def heuristic2(world, goal):
    h = 0
    
    # Add distance from robot to closest misplaced package
    h = num_misplaced_packages(world, goal) * 4
    
    return h
            
    
# =========== A STAR ==============
def a_star(start_world, goal_world, heuristic):
    start_time = time.time()

    explored_worlds_count = 0
    
    closed_set = []
    print("Starting A* algorithm")
    # Initialize initial world a_star data
    start_world.g = 0
    start_world.h = heuristic(start_world, goal_world)
    start_world.f = start_world.g + start_world.h           # Yes "0 + something", for consistency sake
    
    open_set = [start_world]
    
    while open_set:
        explored_worlds_count += 1
        logging.debug(f"Current worlds in open_set : {len(open_set)}")
        
        if step_by_step:
            input()
        else:
            print('.', end = "")
            sys.stdout.flush()
        
        # Sort the open_set by f values
        open_set = sorted(open_set, key=lambda x:x.f)
        
        current_world = open_set.pop(0)
        
        logging.info(f"Next a_star round - exploring world '{current_world.action}'")  
        logging.info(f"World f-value {current_world.f}")
        
        # Check if we reached the goal
        if sameWorld(current_world, goal_world):
            print(f"\n\nGoal reached ! ({round(time.time() - start_time, 2)} seconds - explored {explored_worlds_count} worlds)")
            reconstructActionChain(current_world)
            return True
        
        closed_set.append(current_world) 
        
        # Adding unexplored neighbours to the open_set
        new_worlds = current_world.getNextWorlds()
        logging.debug(f"{len(new_worlds)} neighbours discovered")
        
        # Get neighbouring worlds from the current one
        for world in new_worlds: 
            if findWorld(world, closed_set)[0]:
                logging.debug("Neighbour world already explored - not adding to open_set")
                continue
                
            # We did not explore that world already
            if not findWorld(world, open_set)[0]:
                world.h = heuristic(world, goal_world) 
                world.f = current_world.g + 1 + world.h 
                logging.debug(f"Appending to open_set world {world.action}")
                open_set.append(world)              
            
            world = findWorld(world, closed_set)[1]
            tmp_g = current_world.g + 1 # Distance between neighbouring worlds
            logging.debug(f"Neighbour with action {world.action}, g-score {tmp_g} and f-score : {world.f}")
                  
            if tmp_g >= world.g:
                logging.debug(f"\t[RESULT] World cannot be reached quicker - new {tmp_g} vs old : {world.g} - skipping")
             
            # We found a shorter path that leads to this world   
            else:
                logging.debug("\t[RESULT] Shorter path to world found")
                world.previous = current_world
                world.g = tmp_g
                world.h = heuristic(world, goal_world) 
                world.f = world.g + world.h
                    
    # Exhausted the open_set, no solutions
    login.critical("Ran out of worlds")
    return False


# ========== MAIN ===========
    
if __name__ == "__main__":
    
    # Debug mode - configure the logger
    if len(sys.argv) > 1:
        step_by_step = True
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        stderrHandler = logging.StreamHandler()
        stderrHandler.setLevel(logging.DEBUG)
        stderrHandler.setFormatter(logging.Formatter(u'\t%(funcName)s --%(levelname)7s : %(message)s'))        
        logger.addHandler(stderrHandler)
    else:
        step_by_step = False
    
    # Initial world        
    warehouseA_s  = {'S':0,'M':2,'L':0}
    warehouseB_s  = {'S':0,'M':1,'L':0}
    truck_s       = {'S':3,'M':0,'L':3} 
    robot_s = Robot('T', None)
    initial_world = World(warehouseA_s, warehouseB_s, truck_s, robot_s)
    initial_world.action = "Start"

    # Goal world
    warehouseA_g = {'S':2, 'M':0, 'L':0}
    warehouseB_g = {'S':0, 'M':0, 'L':3}
    truck_g      = {'S':0, 'M':3, 'L':0}
    robot_g = Robot('A', 'S')
    goal_world = World(warehouseA_g, warehouseB_g, truck_g, robot_g)
    
    # Start the search
    a_star(initial_world, goal_world, heuristic=heuristic2)
