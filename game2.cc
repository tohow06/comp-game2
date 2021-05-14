// this code requires ROOT
#include <TROOT.h>
#include <TCanvas.h>
#include <TH1F.h>
#include <TLine.h>
#include <TPolyMarker.h>
#include <TLatex.h>
#include <TTimer.h>
#include <TRandom3.h>
#include <TString.h>
#include <vector>
#include "player_module.h"

player_module P1;

TCanvas *g_canvas(0);
TH1F *g_frame(0);
TLatex *g_status(0);
TLatex *g_score(0);
TLatex *g_message(0);
TPolyMarker *g_base(0);
TPolyMarker *g_pawn(0);
TPolyMarker *g_resspot(0);
TPolyMarker *g_hit(0);

class random_gen {
public:
    unsigned long long s1, s2;
    random_gen(unsigned long long seed = 12345678UL) {
        s1 = seed & 0xffffUL;
        s2 = (seed >> 16) & 0xffffUL;
        for(int i=0;i<20;++i) gen(); // warm up
    }
    unsigned int gen() {
        s1 = s1 ^ (s1 >> 17);
        s1 = s1 ^ (s1 << 31);
        s1 = s1 ^ (s1 >>  8);
        s2 = (s2 & 0xffffffffUL)*4294957665UL + (s2>>32);
        return static_cast<unsigned int>((s1 ^ s2) & 0xffffffffUL);
    }
    double uniform(double a = 0., double b = 1.) {
        return static_cast<double>(gen())/0xffffffff*(b-a)+a;
    }
    int randint(int a, int b) {
        return static_cast<int>(uniform(a,b+1.-1E-10));
    }
};

// let's use our own random generator
// replace time function to a fixed seed if needed
random_gen rnd(time(0));

const double unit_dim = 0.01;
const double world_boundary_x[2] = {0.,1.};
const double world_boundary_y[2] = {0.,1.};

int game_status = 1;
int game_level = 1;
int game_score = 0;
TString game_message = "NEW GAME";
int game_message_delay = 40;
int game_score_last = 0;

class sprite {
public:
    int id; // id number
    double x,y; // current position
    double tx,ty; // target position
    double dx,dy; // expected movement
    int cmd; // action command: 0 - standby, 1 - combat, 2 - resource collect, 3 - construct
    int tcmd; // target action command
    int lv; // base level
    int hp; // hit point
    int step; // step in pawn creation
    int type; // type of sprite: 0 - base, 1 - pawn, 2 - resource spot, 3 - hit
    int control_opt; // 0 - user control, 1 - enemy AI
    int status; // 0 - dead, 1 - active
    
    sprite() {
        id = 0;
        x = y = 0.;
        tx = ty = 0.;
        dx = dy = 0.;
        cmd = tcmd = 0;
        lv = 1;
        hp = 1;
        step = 0;
        type = 0;
        control_opt = 0;
        status = 1;
    }
    
    bool detect_collision(sprite &sp) {
        double dist_max = unit_dim;
        if (type==0 || sp.type==0) dist_max = unit_dim*2.;
        double dist = sqrt(pow(sp.x-x,2)+pow(sp.y-y,2));
        if (dist<=dist_max) return true;
        return false;
    }
};

int serial_id = 1;
int res_player = 0, res_enemy = 0;
std::vector<sprite> splist, splist_hit;

void add_init_base(double x, double y, int init_pawn, int control_opt) {
    sprite base;
    base.id = serial_id++;
    base.x = x;
    base.y = y;
    base.lv = 1;
    base.hp = 100;
    base.type = 0;
    base.control_opt = control_opt;
    splist.push_back(base);
    
    for(int it=0; it<init_pawn; ++it) {
        sprite pawn;
        pawn.id = serial_id++;
        double r = rnd.uniform(unit_dim*2,unit_dim*4);
        double phi = rnd.uniform(0.,M_PI*2.);
        pawn.x = base.x+r*cos(phi);
        pawn.y = base.y+r*sin(phi);
        if (pawn.x<unit_dim) pawn.x = unit_dim;
        if (pawn.y<unit_dim) pawn.y = unit_dim;
        if (pawn.x>1.-unit_dim) pawn.x = 1.-unit_dim;
        if (pawn.y>1.-unit_dim) pawn.y = 1.-unit_dim;
        pawn.lv = 1;
        pawn.hp = 10;
        pawn.type = 1;
        pawn.control_opt = control_opt;
        splist.push_back(pawn);
    }
}

void add_init_resspot(double x, double y) {
    sprite resspot;
    resspot.id = serial_id++;
    resspot.x = x;
    resspot.y = y;
    resspot.lv = 1;
    resspot.hp = rnd.randint(10,20);
    resspot.type = 2;
    splist.push_back(resspot);
}

void init_level() {
    
    add_init_base(0.10,0.10,4,0); // player base + initial pawn
    add_init_base(0.15,0.10,4,0);
    add_init_base(0.10,0.15,4,0);
    
    add_init_base(0.85,0.9,4,1); // enemy base + initial pawn
    add_init_base(0.9,0.85,4,1);
    
    for(int it=0; it<20; ++it)
        add_init_resspot(rnd.uniform(unit_dim,1.-unit_dim),rnd.uniform(unit_dim,1.-unit_dim));
}

void animate() {
    if (!gROOT->GetListOfCanvases()->FindObject("g_canvas")) return;
    
    g_frame->Draw("axis");
    
    // base/pawn counting [# of base, # of pawn, # of max pawn]
    int count_player[3] = {0,0,0},count_enemy[3] = {0,0,0};
    for(auto& sp : splist) {
        if (sp.type==0 && sp.control_opt==0) count_player[0]++;
        if (sp.type==1 && sp.control_opt==0) count_player[1]++;
        if (sp.type==0 && sp.control_opt==0) count_player[2]+=(sp.lv>0?sp.lv*5+10:0);
        if (sp.type==0 && sp.control_opt==1) count_enemy[0]++;
        if (sp.type==1 && sp.control_opt==1) count_enemy[1]++;
        if (sp.type==0 && sp.control_opt==1) count_enemy[2]+=(sp.lv>0?sp.lv*5+10:0);
    }
    
    int P1_score = game_score;
    int P1_resource_player = res_player;
    int P1_resource_enemy = res_enemy;
    std::vector<int> P1_code, P1_hp, P1_target_cmd;
    std::vector<double> P1_x, P1_y, P1_target_x, P1_target_y;
    
    for(auto& sp : splist) {
        if (sp.control_opt!=0) continue;
        if (sp.type!=1) continue;
        if (sp.tcmd!=0) continue;
        P1_code.push_back(0);
        P1_hp.push_back(sp.hp);
        P1_x.push_back(sp.x);
        P1_y.push_back(sp.y);
        P1_target_cmd.push_back(0);
        P1_target_x.push_back(sp.x);
        P1_target_y.push_back(sp.y);
    }
    for(auto& sp : splist) {
        if (sp.control_opt!=0) continue;
        if (sp.type!=1) continue;
        if (sp.tcmd==0) continue;
        P1_code.push_back(1);
        P1_hp.push_back(sp.hp);
        P1_x.push_back(sp.x);
        P1_y.push_back(sp.y);
    }
    for(auto& sp : splist) {
        if (sp.control_opt!=0) continue;
        if (sp.type!=0) continue;
        P1_code.push_back(2);
        P1_hp.push_back(sp.hp);
        P1_x.push_back(sp.x);
        P1_y.push_back(sp.y);
    }
    for(auto& sp : splist) {
        if (sp.control_opt!=1) continue;
        if (sp.type!=1) continue;
        P1_code.push_back(3);
        P1_hp.push_back(sp.hp);
        P1_x.push_back(sp.x);
        P1_y.push_back(sp.y);
    }
    for(auto& sp : splist) {
        if (sp.control_opt!=1) continue;
        if (sp.type!=0) continue;
        P1_code.push_back(4);
        P1_hp.push_back(sp.hp);
        P1_x.push_back(sp.x);
        P1_y.push_back(sp.y);
    }
    for(auto& sp : splist) {
        if (sp.type!=2) continue;
        P1_code.push_back(5);
        P1_hp.push_back(sp.hp);
        P1_x.push_back(sp.x);
        P1_y.push_back(sp.y);
    }
    
    P1.decision(P1_score, P1_resource_player, P1_resource_enemy,
                P1_code, P1_hp, P1_x, P1_y,
                P1_target_cmd, P1_target_x, P1_target_y);
    
    int pawn_idx = 0;
    for(auto& sp : splist) {
        if (sp.control_opt!=0) continue;
        if (sp.type!=1) continue;
        if (sp.tcmd!=0) continue;
        if (pawn_idx>=P1_target_cmd.size() ||
            pawn_idx>=P1_target_x.size() ||
            pawn_idx>=P1_target_y.size()) continue;
        
        sp.tcmd = P1_target_cmd[pawn_idx];
        sp.tx = P1_target_x[pawn_idx];
        sp.ty = P1_target_y[pawn_idx];
        if (sp.tcmd<0 || sp.tcmd>3) sp.tcmd = 0;
        if (sp.tx<0.) sp.tx = 0.;
        if (sp.ty<0.) sp.ty = 0.;
        if (sp.tx>1.) sp.tx = 1.;
        if (sp.ty>1.) sp.ty = 1.;
        ++pawn_idx;
    }
    
    // action decision
    for(auto& sp : splist) {
        if (sp.control_opt!=1) continue;
        if (sp.type!=1) continue;
        if (sp.tcmd!=0) continue;
        
        int resspot_count = 0;
        sprite *min_sp = 0;
        double min_dist = -1.;
        for(auto& op : splist) {
            if ((op.control_opt==0 && op.type==0) ||
                (op.control_opt==0 && op.type==1) ||
                (op.control_opt==1 && op.type==0) ||
                (op.type==2)) {
                double dist = pow(sp.x-op.x,2)+pow(sp.y-op.y,2);
                if (min_dist<0. || dist<min_dist) {
                    min_dist = dist;
                    min_sp = &op;
                }
            }
            if (op.type==2) ++resspot_count;
        }
        
        if (min_sp!=0) {
            if ((min_sp->control_opt==0 && min_sp->type==0) ||
                (min_sp->control_opt==0 && min_sp->type==1)) {
                double r = rnd.uniform();
                if (res_enemy>0 && resspot_count>0) {
                    if (r<0.50) sp.tcmd = 1;
                    else
                    if (r<0.75) sp.tcmd = 2;
                    else        sp.tcmd = 3;
                }else if (res_enemy==0 && resspot_count>0) {
                    if (r<0.66) sp.tcmd = 1;
                    else        sp.tcmd = 2;
                }else if (res_enemy>0 && resspot_count==0) {
                    if (r<0.66) sp.tcmd = 1;
                    else        sp.tcmd = 3;
                }else sp.tcmd = 1;
            }else if (min_sp->type==2) {
                double r = rnd.uniform();
                if (res_enemy>0) {
                    if (r<0.50) sp.tcmd = 2;
                    else
                    if (r<0.75) sp.tcmd = 1;
                    else        sp.tcmd = 3;
                }else {
                    if (r<0.66) sp.tcmd = 2;
                    else        sp.tcmd = 1;
                }
            }else if (min_sp->control_opt==1 && min_sp->type==0) {
                double r = rnd.uniform();
                if (res_enemy>0 && resspot_count>0) {
                    if (r<0.50) sp.tcmd = 3;
                    else
                    if (r<0.75) sp.tcmd = 1;
                    else        sp.tcmd = 2;
                }else if (res_enemy==0 && resspot_count>0) {
                    if (r<0.50) sp.tcmd = 1;
                    else        sp.tcmd = 2;
                }else if (res_enemy>0 && resspot_count==0) {
                    if (r<0.66) sp.tcmd = 3;
                    else        sp.tcmd = 1;
                }else sp.tcmd = 1;
            }
        }else {
            if (res_enemy>0) sp.tcmd = rnd.randint(1,3);
            else sp.tcmd = rnd.randint(1,2);
        }
            
        if (sp.tcmd==1) {
            int priority_type = 0;
            if (min_sp!=0 && min_sp->control_opt==0 && min_sp->type==1 &&
                rnd.uniform()<0.5) priority_type = 1;
            
            double min_dist = -1.;
            for(auto& op : splist) {
                if (op.type!=priority_type) continue;
                if (op.control_opt!=0) continue;
                double dist = pow(sp.x-op.x,2)+pow(sp.y-op.y,2);
                if (min_dist<0. || dist<min_dist) {
                    min_dist = dist;
                    sp.tx = op.x;
                    sp.ty = op.y;
                }
            }
            if (min_dist<0.)
                for(auto& op : splist) {
                    if (op.type!=1-priority_type) continue;
                    if (op.control_opt!=0) continue;
                    double dist = pow(sp.x-op.x,2)+pow(sp.y-op.y,2);
                    if (min_dist<0. || dist<min_dist) {
                        min_dist = dist;
                        sp.tx = op.x;
                        sp.ty = op.y;
                    }
                }
            if (min_dist<0.) {
                sp.tx = rnd.uniform(unit_dim,1.-unit_dim);
                sp.ty = rnd.uniform(unit_dim,1.-unit_dim);
            }
        }else if (sp.tcmd==2) {
            double min_dist = -1.;
            for(auto& op : splist) {
                if (op.type!=2) continue;
                double dist = pow(sp.x-op.x,2)+pow(sp.y-op.y,2);
                if (min_dist<0. || dist<min_dist) {
                    min_dist = dist;
                    sp.tx = op.x;
                    sp.ty = op.y;
                }
            }
            if (min_dist<0.) sp.tcmd = 0;
        }else if (sp.tcmd==3) {
            double min_dist = -1.;
            for(auto& op : splist) {
                if (op.type!=0) continue;
                if (op.control_opt!=1) continue;
                if (op.lv>=3) continue;
                double dist = pow(sp.x-op.x,2)+pow(sp.y-op.y,2);
                if (min_dist<0. || dist<min_dist) {
                    min_dist = dist;
                    sp.tx = op.x;
                    sp.ty = op.y;
                }
            }
            if (min_dist<0.) {
                for(auto& op : splist) {
                    if (op.type!=0) continue;
                    if (op.control_opt!=1) continue;
                    double dist = pow(sp.x-op.x,2)+pow(sp.y-op.y,2);
                    if (min_dist<0. || dist<min_dist) {
                        min_dist = dist;
                        sp.tx = op.x;
                        sp.ty = op.y;
                    }
                }
                double r = rnd.uniform(unit_dim*4,unit_dim*8);
                double phi = rnd.uniform(0.,M_PI*2.);
                sp.tx += r*cos(phi);
                sp.ty += r*sin(phi);
                if (sp.tx<unit_dim) sp.tx = unit_dim;
                if (sp.ty<unit_dim) sp.ty = unit_dim;
                if (sp.tx>1.-unit_dim) sp.tx = 1.-unit_dim;
                if (sp.ty>1.-unit_dim) sp.ty = 1.-unit_dim;
            }
            if (min_dist<0.) {
                sp.tx = sp.x;
                sp.ty = sp.y;
            }
        }
    }
    
    // base action
    for(auto& sp : splist) {
        if (sp.type!=0) continue;
        if (sp.control_opt==0 && count_player[1]>=count_player[2]) continue;
        if (sp.control_opt==1 && count_enemy[1]>=count_enemy[2]) continue;
        if (sp.lv<1) continue;
        
        if (sp.step>=48-sp.lv*8) {
            sp.step = 0;
            
            sprite pawn;
            pawn.id = serial_id++;
            double r = rnd.uniform(unit_dim*2,unit_dim*4);
            double phi = rnd.uniform(0.,M_PI*2.);
            pawn.x = sp.x+r*cos(phi);
            pawn.y = sp.y+r*sin(phi);
            if (pawn.x<unit_dim) pawn.x = unit_dim;
            if (pawn.y<unit_dim) pawn.y = unit_dim;
            if (pawn.x>1.-unit_dim) pawn.x = 1.-unit_dim;
            if (pawn.y>1.-unit_dim) pawn.y = 1.-unit_dim;
            pawn.lv = 1;
            pawn.hp = 10;
            pawn.type = 1;
            pawn.control_opt = sp.control_opt;
            splist.push_back(pawn);
        } else sp.step+=1;
    }
    
    // pawn action
    for(auto& sp : splist) {
        if (sp.type!=1) continue;
        
        double dist = sqrt(pow(sp.x-sp.tx,2)+pow(sp.y-sp.ty,2));
        
        sp.cmd = 0;
        if (sp.tcmd==1 && dist<unit_dim) {
            for(auto& op : splist) {
                if (op.type!=0 && op.type!=1) continue;
                if (op.control_opt==sp.control_opt) continue;
                if (op.detect_collision(sp)) sp.cmd = 1;
            }
            if (sp.cmd==0) sp.tcmd = 0;
        }
        if (sp.tcmd==2 && dist<unit_dim) {
            for(auto& op : splist) {
                if (op.type!=2) continue;
                if (op.detect_collision(sp)) sp.cmd = 2;
            }
            if (sp.cmd==0) sp.tcmd = 0;
        }
        if (sp.tcmd==3 && dist<unit_dim) {
            if ((sp.control_opt==0 && res_player>0) ||
                (sp.control_opt==1 && res_enemy>0)) sp.cmd = 3;
            if (sp.cmd==0) sp.tcmd = 0;
        }
        for(auto& op : splist) {
            if (op.type!=0 && op.type!=1) continue;
            if (op.control_opt==sp.control_opt) continue;
            if (op.detect_collision(sp)) sp.cmd = 1;
        }
    
        if (sp.cmd==1) {
            std::vector<sprite*> targets;
            for(auto& op : splist) {
                if (op.type!=0 && op.type!=1) continue;
                if (op.control_opt==sp.control_opt) continue;
                if (op.detect_collision(sp)) targets.push_back(&op);
            }
            for(int idx=0; idx<targets.size(); ++idx) {
                if (rnd.uniform()<0.5) continue;
                targets[idx]->hp -= 1;
                targets[idx]->lv = 0;
                if (sp.control_opt==0) game_score += 1;
                if (targets[idx]->type==0) {
                    if (targets[idx]->hp>=50) targets[idx]->lv = 1;
                    if (targets[idx]->hp>=150) targets[idx]->lv = 2;
                    if (targets[idx]->hp>=200) targets[idx]->lv = 3;
                }
                if (targets[idx]->hp<=0) {
                    targets[idx]->hp=0;
                    targets[idx]->status=0;
                    if (sp.control_opt==0 && targets[idx]->type==0) game_score += 100;
                    if (sp.control_opt==0 && targets[idx]->type==1) game_score += 10;
                }
                for(int i=0;i<2;++i) {
                    sprite hit;
                    hit.x = targets[idx]->x+rnd.uniform(-unit_dim,+unit_dim);
                    hit.y = targets[idx]->y+rnd.uniform(-unit_dim,+unit_dim);
                    hit.hp = rnd.randint(5,9);
                    splist_hit.push_back(hit);
                }
            }
        }else
        if (sp.cmd==2) {
            std::vector<sprite*> targets;
            for(auto& op : splist) {
                if (op.type!=2) continue;
                if (op.detect_collision(sp)) targets.push_back(&op);
            }
            int idx = rnd.randint(0,targets.size()-1);
            if (targets[idx]->hp>0) {
                targets[idx]->hp -= 1;
                if (targets[idx]->hp<=0) {
                    targets[idx]->hp=0;
                    targets[idx]->status=0;
                    if (sp.control_opt==0) game_score += 10;
                }
                if (sp.control_opt==0) { res_player += 1; game_score += 1; }
                if (sp.control_opt==1) res_enemy += 1;
            }
        }else
        if (sp.cmd==3) {
            if ((sp.control_opt==0 && res_player>0) ||
                (sp.control_opt==1 && res_enemy>0)) {
            
                std::vector<sprite*> targets;
                for(auto& op : splist) {
                    if (op.type!=0) continue;
                    if (op.control_opt!=sp.control_opt) continue;
                    if (op.detect_collision(sp)) targets.push_back(&op);
                }
                if (targets.size()>0) {
                    int idx = rnd.randint(0,targets.size()-1);
                    targets[idx]->hp += 1;
                    targets[idx]->lv = 0;
                    if (targets[idx]->hp>=50) targets[idx]->lv = 1;
                    if (targets[idx]->hp>=150) targets[idx]->lv = 2;
                    if (targets[idx]->hp>=200) targets[idx]->lv = 3;
                    if (targets[idx]->hp>=250) targets[idx]->hp=250;
                } else {
                    sprite base;
                    base.id = serial_id++;
                    base.x = sp.tx;
                    base.y = sp.ty;
                    base.lv = 0;
                    base.hp = 1;
                    base.type = 0;
                    base.control_opt = sp.control_opt;
                    splist.push_back(base);
                }
                if (sp.control_opt==0) res_player -= 1;
                if (sp.control_opt==1) res_enemy -= 1;
                if (sp.control_opt==0) game_score += 1;
            }
        }
        
        if (sp.tcmd!=0) {
            if (dist>unit_dim) {
                double dir = atan2(sp.ty-sp.y,sp.tx-sp.x);
                double scale = 0.5;
                if (sp.cmd==1) scale = 0.1;
                sp.dx = unit_dim*cos(dir)*scale;
                sp.dy = unit_dim*sin(dir)*scale;
                sp.x += sp.dx;
                sp.y += sp.dy;
                if (sp.x<0.) sp.x = 0.;
                if (sp.y<0.) sp.y = 0.;
                if (sp.x>1.) sp.x = 1.;
                if (sp.y>1.) sp.y = 1.;
            }
        }
    }

    // hits action
    for(auto& sp : splist_hit) {
        if (sp.hp<=0) sp.status = 0;
        else sp.hp--;
    }
    
    // clean up "dead" objects
    std::vector<sprite> tmp;
    for(auto& sp : splist) if (sp.status!=0) tmp.push_back(sp);
    splist = tmp;
    tmp.clear();
    for(auto& sp : splist_hit) if (sp.status!=0) tmp.push_back(sp);
    splist_hit = tmp;
    tmp.clear();
    
    // status summary
    count_player[0] = count_player[1] = count_player[2] = 0;
    count_enemy[0] = count_enemy[1] = count_enemy[2] = 0;
    for(auto& sp : splist) {
        if (sp.type==0 && sp.control_opt==0) count_player[0]++;
        if (sp.type==1 && sp.control_opt==0) count_player[1]++;
        if (sp.type==0 && sp.control_opt==0) count_player[2]+=(sp.lv>0?sp.lv*5+10:0);
        if (sp.type==0 && sp.control_opt==1) count_enemy[0]++;
        if (sp.type==1 && sp.control_opt==1) count_enemy[1]++;
        if (sp.type==0 && sp.control_opt==1) count_enemy[2]+=(sp.lv>0?sp.lv*5+10:0);
    }
    TString status_str = Form("Base: %d  Pawn: %d/%d  Res: %d", count_player[0],count_player[1],count_player[2],res_player);
    g_status->DrawLatex(0.03,1.05,status_str);
    g_score->DrawLatex(0.63,1.05,Form("Score: %d",game_score));
    
    game_status = 0; // check if game over
    if (count_player[0]>0 || count_player[1]>0) game_status = 1;
    if (!game_status) {
        game_message = "GAME OVER";
        game_message_delay = -1;
    }
    
    int expected_levelup_score = 0;
    expected_levelup_score += (game_level+1)*300;
    expected_levelup_score += (game_level+1)*(game_level+3+8)*30;
    expected_levelup_score += (15+game_level*5)*45;
    if ((count_enemy[0]==0 && count_enemy[1]==0) || (game_score-game_score_last>=expected_levelup_score)) {
        if (game_level<20) {
            game_level += 1;
            game_message = Form("LEVEL %d",game_level);
        }else game_message = Form("LV MASTER");
        game_message_delay = 40;
        
        for(int it=0;it<game_level+1;++it)
            add_init_base(rnd.uniform(unit_dim*4.,1.0-unit_dim*4.), rnd.uniform(unit_dim*4.,1.0-unit_dim*4.), 3+game_level, 1);
        for(int it=0; it<15+game_level*5; ++it)
            add_init_resspot(rnd.uniform(unit_dim,1.-unit_dim),rnd.uniform(unit_dim,1.-unit_dim));
        
        game_score_last = game_score;
    }
    
    for(auto& sp : splist) {
        if (sp.type==0 && sp.control_opt==0) {
            if (sp.lv==0) g_base->SetMarkerColor(17);
            if (sp.lv==1) g_base->SetMarkerColor(66);
            if (sp.lv==2) g_base->SetMarkerColor(63);
            if (sp.lv==3) g_base->SetMarkerColor(60);
            g_base->DrawPolyMarker(1,&sp.x,&sp.y);
        }else if (sp.type==0 && sp.control_opt==1) {
            if (sp.lv==0) g_base->SetMarkerColor(17);
            if (sp.lv==1) g_base->SetMarkerColor(93);
            if (sp.lv==2) g_base->SetMarkerColor(95);
            if (sp.lv==3) g_base->SetMarkerColor(97);
            g_base->DrawPolyMarker(1,&sp.x,&sp.y);
        }
    }
    for(auto& sp : splist) {
        if (sp.type==2)
            g_resspot->DrawPolyMarker(1,&sp.x,&sp.y);
    }
    for(auto& sp : splist) {
        if (sp.type==1 && sp.control_opt==0) {
            g_pawn->SetMarkerColor(63);
            g_pawn->DrawPolyMarker(1,&sp.x,&sp.y);
        }else if (sp.type==1 && sp.control_opt==1) {
            g_pawn->SetMarkerColor(95);
            g_pawn->DrawPolyMarker(1,&sp.x,&sp.y);
        }
    }
    
    // hits
    for(auto& sp : splist_hit)
        g_hit->DrawPolyMarker(1,&sp.x,&sp.y);
    
    if (game_message_delay>0 || game_message_delay<0)
        g_message->DrawLatex(0.50,0.55,game_message);
        if (game_message_delay>0) game_message_delay--;
    
    g_canvas->Update();
}

void game2() {
    P1.banner();
    
    g_canvas = new TCanvas("g_canvas","",600,660);
    g_canvas->SetMargin(0.1,0.05,0.1,0.05);
    g_frame = g_canvas->DrawFrame(world_boundary_x[0],world_boundary_y[0],world_boundary_x[1],world_boundary_y[1]*1.1);
    g_frame->GetXaxis()->SetLabelSize(0.025);
    g_frame->GetYaxis()->SetLabelSize(0.025);
    
    g_base = new TPolyMarker();
    g_base->SetMarkerStyle(20);
    g_base->SetMarkerSize(2.5);
    
    g_pawn = new TPolyMarker();
    g_pawn->SetMarkerStyle(29);
    g_pawn->SetMarkerSize(1.5);
    
    g_resspot = new TPolyMarker();
    g_resspot->SetMarkerColor(8);
    g_resspot->SetMarkerStyle(34);
    g_resspot->SetMarkerSize(2.);
    
    g_hit = new TPolyMarker();
    g_hit->SetMarkerColor(91);
    g_hit->SetMarkerStyle(43);
    g_hit->SetMarkerSize(1.5);
    
    g_status = new TLatex();
    g_status->SetTextSize(0.035);
    g_status->SetTextColor(kBlue-4);
    g_status->SetTextAlign(12);
    g_status->SetTextFont(42);
    g_score = new TLatex();
    g_score->SetTextSize(0.035);
    g_score->SetTextColor(kBlue-4);
    g_score->SetTextAlign(12);
    g_score->SetTextFont(42);
    g_message = new TLatex();
    g_message->SetTextSize(0.14);
    g_message->SetTextAlign(22);
    g_message->SetTextColor(kOrange+1);
    g_message->SetTextFont(42);
    
    init_level();
    
    TTimer *timer = new TTimer(25);
    timer->SetCommand("animate()");
    timer->TurnOn();
}
