import numpy as np

class player_module:

    # Constructor, allocate any private data here
    def __init__(self):
        pass
    
    # Please update the banner according to your information
    def banner(self):
        print('------------------------')
        print('Author: your_name_here')
        print('ID: bxxxxxxxx')
        print('------------------------')

#   Decision making function for the action of your pawns, toward next decision frame.
#   ------------------------
#   The input arguments consist of
#   score = current score
#   resource_player = resource points (yours)
#   resource_enemy = resource points (enemy)
#   code = type of objects
#       0 - player pawn (free)
#       1 - player pawn (busy)
#       2 - player base
#       3 - enemy pawn
#       4 - enemy base
#       5 - resource spot
#   hp = current hit points of the objects
#   x,y = coordinate of the objects
#   ------------------------
#   For each of your "free pawns", you can set the target command and location
#   with the following lists:
#   target_cmd = action command
#       0 - standby
#       1 - attack
#       2 - collect resource
#       3 - construct
#   target_x, target_y = target location
#   ------------------------
#   *** Note the information for your "free pawns" are   ***
#   *** kept in the early entries of code/hp/x/y lists. ***
 
    def decision(self, score, resource_player, resource_enemy,
                 code, hp, x, y, target_cmd, target_x, target_y):
        
        for i in range(len(target_cmd)):
            
            if (resource_player>0):
                  target_cmd[i] = 1+(i%3) # can attack, collect resource, and construct
            else: target_cmd[i] = 1+(i%2) # can only attack and collect resource
            
            if (target_cmd[i]==1): # attack, look for the closest target
                min_dist = -1.
                for j in range(len(code)):
                    if (code[j]!=3 and code[j]!=4): continue
                    dist = (x[j]-x[i])**2+(y[j]-y[i])**2
                    if (min_dist<0. or dist<min_dist):
                        min_dist = dist
                        target_x[i] = x[j]
                        target_y[i] = y[j]

            if (target_cmd[i]==2): # collect resource, look for the closest spot
                min_dist = -1.
                for j in range(len(code)):
                    if (code[j]!=5): continue
                    dist = (x[j]-x[i])**2+(y[j]-y[i])**2
                    if (min_dist<0. or dist<min_dist):
                        min_dist = dist
                        target_x[i] = x[j]
                        target_y[i] = y[j]

            if (target_cmd[i]==3): # construct
                min_dist = -1. # look for the closest base
                for j in range(len(code)):
                    if (code[j]!=2): continue
                    if (hp[j]>=250): continue
                    dist = (x[j]-x[i])**2+(y[j]-y[i])**2
                    if (min_dist<0. or dist<min_dist):
                        min_dist = dist
                        target_x[i] = x[j]
                        target_y[i] = y[j]
                if (min_dist<0.): # construct a new one in place
                    target_x[i] = x[i]
                    target_y[i] = y[i]
            

