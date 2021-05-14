import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time

import player_module as PM
P1 = PM.player_module()
P1.banner()

class random_gen:
    def __init__(self, seed = 12345678):
        self.s1 = np.uint64(seed & 0xffff)
        self.s2 = np.uint64((seed >> 16) & 0xffff)
        for i in range(20): self.gen() # warm up
    
    def gen(self):
        self.s1 = self.s1 ^ (self.s1 >> np.uint64(17))
        self.s1 = self.s1 ^ (self.s1 << np.uint64(31))
        self.s1 = self.s1 ^ (self.s1 >>  np.uint64(8))
        self.s2 = (self.s2 & np.uint64(0xffffffff))*np.uint64(4294957665) + (self.s2>>np.uint64(32))
        return ((self.s1 ^ self.s2) & np.uint64(0xffffffff))

    def uniform(self,a = 0.,b = 1.):
        return float(self.gen())/0xffffffff*(b-a)+a

    def randint(self,a,b):
        return int(self.uniform(a,b+1.-1E-10))

# let's use our own random generator
# replace time function to a fixed seed if needed
rnd = random_gen(int(time.time()))

fig = plt.figure(figsize=(10,11), dpi=60)
ax = plt.axes(xlim=(0.,1.), ylim=(0.,1.1))

ms_scale = 2.3
g_base_ply0,  = ax.plot([], [], marker='o', ms = ms_scale*10, color=(0.8,0.800,0.8), ls='None')
g_base_ply1,  = ax.plot([], [], marker='o', ms = ms_scale*10, color=(0.0,0.827,1.0), ls='None')
g_base_ply2,  = ax.plot([], [], marker='o', ms = ms_scale*10, color=(0.0,0.546,1.0), ls='None')
g_base_ply3,  = ax.plot([], [], marker='o', ms = ms_scale*10, color=(0.0,0.267,1.0), ls='None')
g_base_ene0,  = ax.plot([], [], marker='o', ms = ms_scale*10, color=(0.8,0.800,0.8), ls='None')
g_base_ene1,  = ax.plot([], [], marker='o', ms = ms_scale*10, color=(1.0,0.653,0.0), ls='None')
g_base_ene2,  = ax.plot([], [], marker='o', ms = ms_scale*10, color=(1.0,0.467,0.0), ls='None')
g_base_ene3,  = ax.plot([], [], marker='o', ms = ms_scale*10, color=(1.0,0.280,0.0), ls='None')
g_pawn_ply,   = ax.plot([], [], marker='*', ms = ms_scale* 6, color=(0.0,0.546,1.0), ls='None')
g_pawn_ene,   = ax.plot([], [], marker='*', ms = ms_scale* 6, color=(1.0,0.467,0.0), ls='None')
g_resspot,    = ax.plot([], [], marker='P', ms = ms_scale* 8, color=(0.35,0.83,0.33), ls='None')
g_hit,  = ax.plot([], [], marker=(4, 1, 0), ms = ms_scale* 8, color=(1.0,0.84,0.0), ls='None')

g_status  = ax.text(0.03,1.05,'', fontsize = 19, color=(0.2,0.2,1.0), ha='left', va='center')
g_score   = ax.text(0.63,1.05,'', fontsize = 19, color=(0.2,0.2,1.0), ha='left', va='center')
g_message = ax.text(0.50,0.55,'', fontsize = 88, color=(1.0,0.6,0.2), ha='center', va='center')

unit_dim = 0.01
world_boundary_x = [0.,1.]
world_boundary_y = [0.,1.]

game_status = 1
game_level = 1
game_score = 0
game_message = 'NEW GAME'
game_message_delay = 40
game_score_last = 0

class sprite:
    def __init__(self):
        self.id = 0 # id number
        self.x, self.y = 0., 0. # current position
        self.tx, self.ty = 0., 0. # target position
        self.dx, self.dy = 0., 0. # expected movement
        self.cmd = 0 # action command: 0 - standby, 1 - combat, 2 - resource collect, 3 - construct
        self.tcmd = 0 # target action command
        self.lv = 1 # base level
        self.hp = 1 # hit point
        self.step = 0 # step in pawn creation
        self.type = 0 # type of sprite: 0 - base, 1 - pawn, 2 - resource spot, 3 - hit
        self.control_opt = 0 # 0 - user control, 1 - enemy AI
        self.status = 1 # 0 - dead, 1 - active
    
    def detect_collision(self, sp):
        dist_max = unit_dim
        if (self.type==0 or sp.type==0): dist_max = unit_dim*2.
        dist = ((sp.x-self.x)**2+(sp.y-self.y)**2)**0.5
        if (dist<=dist_max): return True
        return False

serial_id = 1
res_player, res_enemy = 0, 0
splist, splist_hit = [], []

def add_init_base(x, y, init_pawn, control_opt):
    global serial_id, splist
    
    base = sprite()
    base.id = serial_id
    serial_id += 1
    base.x = x
    base.y = y
    base.lv = 1
    base.hp = 100
    base.type = 0
    base.control_opt = control_opt
    splist.append(base)
    
    for it in range(init_pawn):
        pawn = sprite()
        pawn.id = serial_id
        serial_id += 1
        r = rnd.uniform(unit_dim*2,unit_dim*4)
        phi = rnd.uniform(0.,np.pi*2.)
        pawn.x = base.x+r*np.cos(phi)
        pawn.y = base.y+r*np.sin(phi)
        if (pawn.x<unit_dim): pawn.x = unit_dim
        if (pawn.y<unit_dim): pawn.y = unit_dim
        if (pawn.x>1.-unit_dim): pawn.x = 1.-unit_dim
        if (pawn.y>1.-unit_dim): pawn.y = 1.-unit_dim
        pawn.lv = 1
        pawn.hp = 10
        pawn.type = 1
        pawn.control_opt = control_opt
        splist.append(pawn)
        
def add_init_resspot(x, y):
    global serial_id, splist
    resspot = sprite()
    resspot.id = serial_id
    serial_id += 1
    resspot.x = x
    resspot.y = y
    resspot.lv = 1
    resspot.hp = rnd.randint(10,20)
    resspot.type = 2
    splist.append(resspot)

def init_level():

    add_init_base(0.10,0.10,4,0) # player base + initial pawn
    add_init_base(0.15,0.10,4,0)
    add_init_base(0.10,0.15,4,0)
    
    add_init_base(0.85,0.9,4,1) # enemy base + initial pawn
    add_init_base(0.9,0.85,4,1)
    
    for it in range(20):
        add_init_resspot(rnd.uniform(unit_dim,1.-unit_dim),rnd.uniform(unit_dim,1.-unit_dim))

def init():

    global g_base_ply0, g_base_ply1, g_base_ply2, g_base_ply3
    global g_base_ene0, g_base_ene1, g_base_ene2, g_base_ene3
    global g_pawn_ply, g_pawn_ene, g_resspot, g_hit
    global g_status, g_score, g_message

    g_base_ply0.set_data([], [])
    g_base_ply1.set_data([], [])
    g_base_ply2.set_data([], [])
    g_base_ply3.set_data([], [])
    g_base_ene0.set_data([], [])
    g_base_ene1.set_data([], [])
    g_base_ene2.set_data([], [])
    g_base_ene3.set_data([], [])
    g_pawn_ply.set_data([], [])
    g_pawn_ene.set_data([], [])
    g_resspot.set_data([], [])
    g_hit.set_data([], [])

    g_status.set(text='')
    g_score.set(text='')
    g_message.set(text='')

    return g_base_ply0, g_base_ply1, g_base_ply2, g_base_ply3, g_base_ene0, g_base_ene1, g_base_ene2, g_base_ene3, g_resspot, g_pawn_ply, g_pawn_ene, g_hit, g_status, g_score, g_message

def animate(frame):
    global g_base_ply0, g_base_ply1, g_base_ply2, g_base_ply3
    global g_base_ene0, g_base_ene1, g_base_ene2, g_base_ene3
    global g_pawn_ply, g_pawn_ene, g_resspot, g_hit
    global g_status, g_score, g_message
    global unit_dim, world_boundary_x, world_boundary_y
    global game_status, game_level, game_score, game_message, game_message_delay, game_score_last
    global serial_id, res_player, res_enemy
    global splist, splist_hit
    
    # base/pawn counting [# of base, # of pawn, # of max pawn]
    count_player, count_enemy = [0,0,0], [0,0,0]
    for sp in splist:
        if (sp.type==0 and sp.control_opt==0): count_player[0]+=1
        if (sp.type==1 and sp.control_opt==0): count_player[1]+=1
        if (sp.type==0 and sp.control_opt==0 and sp.lv>0): count_player[2]+=sp.lv*5+10
        if (sp.type==0 and sp.control_opt==1): count_enemy[0]+=1
        if (sp.type==1 and sp.control_opt==1): count_enemy[1]+=1
        if (sp.type==0 and sp.control_opt==1 and sp.lv>0): count_enemy[2]+=sp.lv*5+10
    
    P1_score = game_score
    P1_resource_player = res_player
    P1_resource_enemy = res_enemy
    P1_code, P1_hp, P1_target_cmd = [], [], []
    P1_x, P1_y, P1_target_x, P1_target_y = [], [], [], []
    
    for sp in splist:
        if (sp.control_opt!=0): continue
        if (sp.type!=1): continue
        if (sp.tcmd!=0): continue
        P1_code.append(0)
        P1_hp.append(sp.hp)
        P1_x.append(sp.x)
        P1_y.append(sp.y)
        P1_target_cmd.append(0)
        P1_target_x.append(sp.x)
        P1_target_y.append(sp.y)
    for sp in splist:
        if (sp.control_opt!=0): continue
        if (sp.type!=1): continue
        if (sp.tcmd==0): continue
        P1_code.append(1)
        P1_hp.append(sp.hp)
        P1_x.append(sp.x)
        P1_y.append(sp.y)
    for sp in splist:
        if (sp.control_opt!=0): continue
        if (sp.type!=0): continue
        P1_code.append(2)
        P1_hp.append(sp.hp)
        P1_x.append(sp.x)
        P1_y.append(sp.y)
    for sp in splist:
        if (sp.control_opt!=1): continue
        if (sp.type!=1): continue
        P1_code.append(3)
        P1_hp.append(sp.hp)
        P1_x.append(sp.x)
        P1_y.append(sp.y)
    for sp in splist:
        if (sp.control_opt!=1): continue
        if (sp.type!=0): continue
        P1_code.append(4)
        P1_hp.append(sp.hp)
        P1_x.append(sp.x)
        P1_y.append(sp.y)
    for sp in splist:
        if (sp.type!=2): continue
        P1_code.append(5)
        P1_hp.append(sp.hp)
        P1_x.append(sp.x)
        P1_y.append(sp.y)
    
    P1.decision(P1_score, P1_resource_player, P1_resource_enemy,
                P1_code, P1_hp, P1_x, P1_y,
                P1_target_cmd, P1_target_x, P1_target_y)
    
    pawn_idx = 0
    for sp in splist:
        if (sp.control_opt!=0): continue
        if (sp.type!=1): continue
        if (sp.tcmd!=0): continue
        if (pawn_idx>=len(P1_target_cmd) or
            pawn_idx>=len(P1_target_x) or
            pawn_idx>=len(P1_target_y)): continue
        
        sp.tcmd = P1_target_cmd[pawn_idx]
        sp.tx = P1_target_x[pawn_idx]
        sp.ty = P1_target_y[pawn_idx]
        if (sp.tcmd<0 or sp.tcmd>3): sp.tcmd = 0
        if (sp.tx<0.): sp.tx = 0.
        if (sp.ty<0.): sp.ty = 0.
        if (sp.tx>1.): sp.tx = 1.
        if (sp.ty>1.): sp.ty = 1.
        pawn_idx += 1
    
    ## action decision
    for sp in splist:
        if (sp.control_opt!=1): continue
        if (sp.type!=1): continue
        if (sp.tcmd!=0): continue
        
        resspot_count = 0
        min_sp = None
        min_dist = -1.
        for op in splist:
            if ((op.control_opt==0 and op.type==0) or
                (op.control_opt==0 and op.type==1) or
                (op.control_opt==1 and op.type==0) or
                (op.type==2)):
                dist = (sp.x-op.x)**2+(sp.y-op.y)**2
                if (min_dist<0. or dist<min_dist):
                    min_dist = dist
                    min_sp = op
            if (op.type==2): resspot_count += 1
        
        if (min_sp!=None):
            if ((min_sp.control_opt==0 and min_sp.type==0) or
                (min_sp.control_opt==0 and min_sp.type==1)):
                r = rnd.uniform()
                if (res_enemy>0 and resspot_count>0):
                    if (r<0.50): sp.tcmd = 1
                    elif (r<0.75): sp.tcmd = 2
                    else:        sp.tcmd = 3
                elif (res_enemy==0 and resspot_count>0):
                    if (r<0.66): sp.tcmd = 1
                    else:        sp.tcmd = 2
                elif (res_enemy>0 and resspot_count==0):
                    if (r<0.66): sp.tcmd = 1
                    else:        sp.tcmd = 3
                else: sp.tcmd = 1
            elif (min_sp.type==2):
                r = rnd.uniform()
                if (res_enemy>0):
                    if (r<0.50): sp.tcmd = 2
                    elif (r<0.75): sp.tcmd = 1
                    else:        sp.tcmd = 3
                else:
                    if (r<0.66): sp.tcmd = 2
                    else:        sp.tcmd = 1
            elif (min_sp.control_opt==1 and min_sp.type==0):
                r = rnd.uniform()
                if (res_enemy>0 and resspot_count>0):
                    if (r<0.50): sp.tcmd = 3
                    elif (r<0.75): sp.tcmd = 1
                    else:        sp.tcmd = 2
                elif (res_enemy==0 and resspot_count>0):
                    if (r<0.50): sp.tcmd = 1
                    else:        sp.tcmd = 2
                elif (res_enemy>0 and resspot_count==0):
                    if (r<0.66): sp.tcmd = 3
                    else:        sp.tcmd = 1
                else: sp.tcmd = 1
        else:
            if (res_enemy>0): sp.tcmd = rnd.randint(1,3)
            else: sp.tcmd = rnd.randint(1,2)
            
        if (sp.tcmd==1):
            priority_type = 0
            if (min_sp!=None and min_sp.control_opt==0 and min_sp.type==1 and rnd.uniform()<0.5):
                priority_type = 1
            
            min_dist = -1.
            for op in splist:
                if (op.type!=priority_type): continue
                if (op.control_opt!=0): continue
                dist = (sp.x-op.x)**2+(sp.y-op.y)**2
                if (min_dist<0. or dist<min_dist):
                    min_dist = dist
                    sp.tx = op.x
                    sp.ty = op.y
            if (min_dist<0.):
                for op in splist:
                    if (op.type!=1-priority_type): continue
                    if (op.control_opt!=0): continue
                    dist = (sp.x-op.x)**2+(sp.y-op.y)**2
                    if (min_dist<0. or dist<min_dist):
                        min_dist = dist
                        sp.tx = op.x
                        sp.ty = op.y
            if (min_dist<0.):
                sp.tx = rnd.uniform(unit_dim,1.-unit_dim)
                sp.ty = rnd.uniform(unit_dim,1.-unit_dim)
        elif (sp.tcmd==2):
            min_dist = -1.
            for op in splist:
                if (op.type!=2): continue
                dist = (sp.x-op.x)**2+(sp.y-op.y)**2
                if (min_dist<0. or dist<min_dist):
                    min_dist = dist
                    sp.tx = op.x
                    sp.ty = op.y
            if (min_dist<0.): sp.tcmd = 0
        elif (sp.tcmd==3):
            min_dist = -1.
            for op in splist:
                if (op.type!=0): continue
                if (op.control_opt!=1): continue
                if (op.lv>=3): continue
                dist = (sp.x-op.x)**2+(sp.y-op.y)**2
                if (min_dist<0. or dist<min_dist):
                    min_dist = dist
                    sp.tx = op.x
                    sp.ty = op.y
            if (min_dist<0.):
                for op in splist:
                    if (op.type!=0): continue
                    if (op.control_opt!=1): continue
                    dist = (sp.x-op.x)**2+(sp.y-op.y)**2
                    if (min_dist<0. or dist<min_dist):
                        min_dist = dist
                        sp.tx = op.x
                        sp.ty = op.y
                r = rnd.uniform(unit_dim*4,unit_dim*8)
                phi = rnd.uniform(0.,np.pi*2.)
                sp.tx += r*np.cos(phi)
                sp.ty += r*np.sin(phi)
                if (sp.tx<unit_dim): sp.tx = unit_dim
                if (sp.ty<unit_dim): sp.ty = unit_dim
                if (sp.tx>1.-unit_dim): sp.tx = 1.-unit_dim
                if (sp.ty>1.-unit_dim): sp.ty = 1.-unit_dim
            if (min_dist<0.):
                sp.tx = sp.x
                sp.ty = sp.y
            
    # base action
    for sp in splist:
        if (sp.type!=0): continue
        if (sp.control_opt==0 and count_player[1]>=count_player[2]): continue
        if (sp.control_opt==1 and count_enemy[1]>=count_enemy[2]): continue
        if (sp.lv<1): continue
        
        if (sp.step>=48-sp.lv*8):
            sp.step = 0
            
            pawn = sprite()
            pawn.id = serial_id
            serial_id += 1
            r = rnd.uniform(unit_dim*2,unit_dim*4)
            phi = rnd.uniform(0.,np.pi*2.)
            pawn.x = sp.x+r*np.cos(phi)
            pawn.y = sp.y+r*np.sin(phi)
            if (pawn.x<unit_dim): pawn.x = unit_dim
            if (pawn.y<unit_dim): pawn.y = unit_dim
            if (pawn.x>1.-unit_dim): pawn.x = 1.-unit_dim
            if (pawn.y>1.-unit_dim): pawn.y = 1.-unit_dim
            pawn.lv = 1
            pawn.hp = 10
            pawn.type = 1
            pawn.control_opt = sp.control_opt
            splist.append(pawn)
        else: sp.step+=1
    
    # pawn action
    for sp in splist:
        if (sp.type!=1): continue
        
        dist = ((sp.x-sp.tx)**2+(sp.y-sp.ty)**2)**0.5
        
        sp.cmd = 0
        if (sp.tcmd==1 and dist<unit_dim):
            for op in splist:
                if (op.type!=0 and op.type!=1): continue
                if (op.control_opt==sp.control_opt): continue
                if (op.detect_collision(sp)): sp.cmd = 1
            if (sp.cmd==0): sp.tcmd = 0
        if (sp.tcmd==2 and dist<unit_dim):
            for op in splist:
                if (op.type!=2): continue
                if (op.detect_collision(sp)): sp.cmd = 2
            if (sp.cmd==0): sp.tcmd = 0
        if (sp.tcmd==3 and dist<unit_dim):
            if ((sp.control_opt==0 and res_player>0) or
                (sp.control_opt==1 and res_enemy>0)): sp.cmd = 3
            if (sp.cmd==0): sp.tcmd = 0
        for op in splist:
            if (op.type!=0 and op.type!=1): continue
            if (op.control_opt==sp.control_opt): continue
            if (op.detect_collision(sp)): sp.cmd = 1
            
    
        if (sp.cmd==1):
            targets = []
            for op in splist:
                if (op.type!=0 and op.type!=1): continue
                if (op.control_opt==sp.control_opt): continue
                if (op.detect_collision(sp)): targets.append(op)
            
            for idx in range(len(targets)):
                if (rnd.uniform()<0.5): continue
                targets[idx].hp -= 1
                targets[idx].lv = 0
                if (sp.control_opt==0): game_score += 1
                if (targets[idx].type==0):
                    if (targets[idx].hp>=50): targets[idx].lv = 1
                    if (targets[idx].hp>=150): targets[idx].lv = 2
                    if (targets[idx].hp>=200): targets[idx].lv = 3
                if (targets[idx].hp<=0):
                    targets[idx].hp=0
                    targets[idx].status=0
                    if (sp.control_opt==0 and targets[idx].type==0): game_score += 100
                    if (sp.control_opt==0 and targets[idx].type==1): game_score += 10
                for i in range(2):
                    hit = sprite()
                    hit.x = targets[idx].x+rnd.uniform(-unit_dim,+unit_dim)
                    hit.y = targets[idx].y+rnd.uniform(-unit_dim,+unit_dim)
                    hit.hp = rnd.randint(5,9)
                    splist_hit.append(hit)
        elif (sp.cmd==2):
            targets = []
            for op in splist:
                if (op.type!=2): continue
                if (op.detect_collision(sp)): targets.append(op)
            idx = rnd.randint(0,len(targets)-1)
            if (targets[idx].hp>0):
                targets[idx].hp -= 1
                if (targets[idx].hp<=0):
                    targets[idx].hp=0
                    targets[idx].status=0
                    if (sp.control_opt==0): game_score += 10
                if (sp.control_opt==0):
                    res_player += 1
                    game_score += 1
                if (sp.control_opt==1):
                    res_enemy += 1
        elif (sp.cmd==3):
            if ((sp.control_opt==0 and res_player>0) or
                (sp.control_opt==1 and res_enemy>0)):
            
                targets = []
                for op in splist:
                    if (op.type!=0): continue
                    if (op.control_opt!=sp.control_opt): continue
                    if (op.detect_collision(sp)): targets.append(op)
            
                if (len(targets)>0):
                    idx = rnd.randint(0,len(targets)-1)
                    targets[idx].hp += 1
                    targets[idx].lv = 0
                    if (targets[idx].hp>=50): targets[idx].lv = 1
                    if (targets[idx].hp>=150): targets[idx].lv = 2
                    if (targets[idx].hp>=200): targets[idx].lv = 3
                    if (targets[idx].hp>=250): targets[idx].hp=250
                else:
                    base = sprite()
                    base.id = serial_id
                    serial_id += 1
                    base.x = sp.tx
                    base.y = sp.ty
                    base.lv = 0
                    base.hp = 1
                    base.type = 0
                    base.control_opt = sp.control_opt
                    splist.append(base)
                    
                if (sp.control_opt==0): res_player -= 1
                if (sp.control_opt==1): res_enemy -= 1
                if (sp.control_opt==0): game_score += 1
        
        if (sp.tcmd!=0):
            if (dist>unit_dim):
                dir = np.arctan2(sp.ty-sp.y,sp.tx-sp.x)
                scale = 0.5
                if (sp.cmd==1): scale = 0.1
                sp.dx = unit_dim*np.cos(dir)*scale
                sp.dy = unit_dim*np.sin(dir)*scale
                sp.x += sp.dx
                sp.y += sp.dy
                if (sp.x<0.): sp.x = 0.
                if (sp.y<0.): sp.y = 0.
                if (sp.x>1.): sp.x = 1.
                if (sp.y>1.): sp.y = 1.

    # hits action
    for sp in splist_hit:
        if (sp.hp<=0): sp.status = 0
        else: sp.hp-=1
    
    # clean up "dead" objects
    tmp = []
    for sp in splist:
        if (sp.status!=0): tmp.append(sp)
    splist = tmp
    tmp = []
    for sp in splist_hit:
        if (sp.status!=0): tmp.append(sp)
    splist_hit = tmp
    
    # status summary
    count_player, count_enemy = [0,0,0], [0,0,0]
    for sp in splist:
        if (sp.type==0 and sp.control_opt==0): count_player[0]+=1
        if (sp.type==1 and sp.control_opt==0): count_player[1]+=1
        if (sp.type==0 and sp.control_opt==0 and sp.lv>0): count_player[2]+=sp.lv*5+10
        if (sp.type==0 and sp.control_opt==1): count_enemy[0]+=1
        if (sp.type==1 and sp.control_opt==1): count_enemy[1]+=1
        if (sp.type==0 and sp.control_opt==1 and sp.lv>0): count_enemy[2]+=sp.lv*5+10
    status_str = 'Base: %d  Pawn: %d/%d  Res: %d' % (count_player[0],count_player[1],count_player[2],res_player)
    g_status.set(text=status_str)
    g_score.set(text='Score: %d' % game_score)
    
    game_status = 0 # check if game over
    if (count_player[0]>0 or count_player[1]>0): game_status = 1
    if (game_status==0):
        game_message = 'GAME OVER'
        game_message_delay = -1
    
    expected_levelup_score = 0
    expected_levelup_score += (game_level+1)*300
    expected_levelup_score += (game_level+1)*(game_level+3+8)*30
    expected_levelup_score += (15+game_level*5)*45
    if (count_enemy[0]==0 and count_enemy[1]==0) or (game_score-game_score_last>=expected_levelup_score):
        if (game_level<20):
            game_level += 1
            game_message = 'LEVEL %d' % game_level
        else: game_message = 'LV MASTER'
        game_message_delay = 40
        
        for it in range(game_level+1):
            add_init_base(rnd.uniform(unit_dim*4.,1.0-unit_dim*4.), rnd.uniform(unit_dim*4.,1.0-unit_dim*4.), 3+game_level, 1)
        for it in range(15+game_level*5):
            add_init_resspot(rnd.uniform(unit_dim,1.-unit_dim),rnd.uniform(unit_dim,1.-unit_dim))
            
        game_score_last = game_score
    
    vx, vy = [], []
    for sp in splist:
        if (sp.type==0 and sp.control_opt==0 and sp.lv==0):
            vx.append(sp.x)
            vy.append(sp.y)
    g_base_ply0.set_data(vx,vy)
    vx, vy = [], []
    for sp in splist:
        if (sp.type==0 and sp.control_opt==0 and sp.lv==1):
            vx.append(sp.x)
            vy.append(sp.y)
    g_base_ply1.set_data(vx,vy)
    vx, vy = [], []
    for sp in splist:
        if (sp.type==0 and sp.control_opt==0 and sp.lv==2):
            vx.append(sp.x)
            vy.append(sp.y)
    g_base_ply2.set_data(vx,vy)
    vx, vy = [], []
    for sp in splist:
        if (sp.type==0 and sp.control_opt==0 and sp.lv==3):
            vx.append(sp.x)
            vy.append(sp.y)
    g_base_ply3.set_data(vx,vy)
    vx, vy = [], []
    for sp in splist:
        if (sp.type==0 and sp.control_opt==1 and sp.lv==0):
            vx.append(sp.x)
            vy.append(sp.y)
    g_base_ene0.set_data(vx,vy)
    vx, vy = [], []
    for sp in splist:
        if (sp.type==0 and sp.control_opt==1 and sp.lv==1):
            vx.append(sp.x)
            vy.append(sp.y)
    g_base_ene1.set_data(vx,vy)
    vx, vy = [], []
    for sp in splist:
        if (sp.type==0 and sp.control_opt==1 and sp.lv==2):
            vx.append(sp.x)
            vy.append(sp.y)
    g_base_ene2.set_data(vx,vy)
    vx, vy = [], []
    for sp in splist:
        if (sp.type==0 and sp.control_opt==1 and sp.lv==3):
            vx.append(sp.x)
            vy.append(sp.y)
    g_base_ene3.set_data(vx,vy)
    
    vx, vy = [], []
    for sp in splist:
        if (sp.type==2):
            vx.append(sp.x)
            vy.append(sp.y)
    g_resspot.set_data(vx,vy)
    
    vx, vy = [], []
    for sp in splist:
        if (sp.type==1 and sp.control_opt==0):
            vx.append(sp.x)
            vy.append(sp.y)
    g_pawn_ply.set_data(vx,vy)
    vx, vy = [], []
    for sp in splist:
        if (sp.type==1 and sp.control_opt==1):
            vx.append(sp.x)
            vy.append(sp.y)
    g_pawn_ene.set_data(vx,vy)

    # hits
    vx, vy = [], []
    for sp in splist_hit:
        vx.append(sp.x)
        vy.append(sp.y)
    g_hit.set_data(vx,vy)
    
    if (game_message_delay>0 or game_message_delay<0):
        g_message.set(text=game_message)
        if (game_message_delay>0): game_message_delay-=1
    else: g_message.set(text='')

    return g_base_ply0, g_base_ply1, g_base_ply2, g_base_ply3, g_base_ene0, g_base_ene1, g_base_ene2, g_base_ene3, g_resspot, g_pawn_ply, g_pawn_ene, g_hit, g_status, g_score, g_message

init_level()

anim = animation.FuncAnimation(fig, animate, init_func=init,
                               frames=10, interval=25, blit=True)
plt.show()
