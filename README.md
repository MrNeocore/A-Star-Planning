# A-Star-Planning
A* algorithm applied to action planning

## Context :
- Original developement date : 11/2017
- Developped as part of a Artificial Intelligence coursework at HWU.

## Features 
A robot is tasked with the handling of various boxes. 
These packages must be moved to specific warehouses based on the boxes' size in as few steps as possible.
The robot's action are planned using the A* algorithm.


## Self analysis as of 28/07/2018 :
  - Code could be simplified by using more pythonic constructs (list comprehensions, pandas etc)
  - Could add some flexibility (e.g. variable location count)
  - Rather clear code, but very 'loopy' and 'ify'
  
## Overall : 
- Stability    : OK
- Readability  : MOK, no vector operations
- Code quality : MOK, some sections to be more explicit / less "loopy".
- Performance  : Hard to judge, but I'd say MOK due to the absence of any code optimization.
