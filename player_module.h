#include <vector>
#include <cstdlib>

class player_module {
public:
    // Constructor, allocate any private data here
    player_module() {}
    
    // Please update the banner according to your information
    void banner() {
        printf("------------------------\n");
        printf("Author: your_name_here\n");
        printf("ID: bxxxxxxxx\n");
        printf("------------------------\n");
    }

/*  Decision making function for the action of your pawns, toward next decision frame.
    ------------------------
    The input arguments consist of
    score = current score
    resource_player = resource points (yours)
    resource_enemy = resource points (enemy)
    code = type of objects
        0 - player pawn (free)
        1 - player pawn (busy)
        2 - player base
        3 - enemy pawn
        4 - enemy base
        5 - resource spot
    hp = current hit points of the objects
    x,y = coordinate of the objects
    ------------------------
    For each of your "free pawns", you can set the target command and location
    with the following arrays:
    target_cmd = action command
        0 - standby
        1 - attack
        2 - collect resource
        3 - construct
    target_x, target_y = target location
    ------------------------
    *** Note the information for your "free pawns" are   ***
    *** kept in the early entries of code/hp/x/y arrays. ***
 */
    void decision(int score, int resource_player, int resource_enemy,
                  std::vector<int> &code,
                  std::vector<int> &hp,
                  std::vector<double> &x, std::vector<double> &y,
                  std::vector<int> &target_cmd,
                  std::vector<double> &target_x, std::vector<double> &target_y) {
        
        for(int i=0; i<target_cmd.size(); ++i) {
            
            if (resource_player>0)
                 target_cmd[i] = 1+(i%3); // can attack, collect resource, and construct
            else target_cmd[i] = 1+(i%2); // can only attack and collect resource
            
            if (target_cmd[i]==1) { // attack, look for the closest target
                double min_dist = -1.;
                for (int j=0;j<code.size(); ++j) {
                    if (code[j]!=3 && code[j]!=4) continue;
                    double dist = pow(x[j]-x[i],2)+pow(y[j]-y[i],2);
                    if (min_dist<0. || dist<min_dist) {
                        min_dist = dist;
                        target_x[i] = x[j];
                        target_y[i] = y[j];
                    }
                }
            }
            if (target_cmd[i]==2) { // collect resource, look for the closest spot
                double min_dist = -1.;
                for (int j=0;j<code.size(); ++j) {
                    if (code[j]!=5) continue;
                    double dist = pow(x[j]-x[i],2)+pow(y[j]-y[i],2);
                    if (min_dist<0. || dist<min_dist) {
                        min_dist = dist;
                        target_x[i] = x[j];
                        target_y[i] = y[j];
                    }
                }
            }
            if (target_cmd[i]==3) { // construct
                double min_dist = -1.; // look for the closest base
                for (int j=0;j<code.size(); ++j) {
                    if (code[j]!=2) continue;
                    if (hp[j]>=250) continue;
                    double dist = pow(x[j]-x[i],2)+pow(y[j]-y[i],2);
                    if (min_dist<0. || dist<min_dist) {
                        min_dist = dist;
                        target_x[i] = x[j];
                        target_y[i] = y[j];
                    }
                }
                if (min_dist<0.) { // construct a new one in place
                    target_x[i] = x[i];
                    target_y[i] = y[i];
                }
            }
        }
    }
};
