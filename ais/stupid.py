von_neumann=__import__("von-neumann")
import math
import random

class ProbeAi(object):
    
    def __init__(self, cargs):
        self.cargs=cargs
        if self.cargs=='initial':
            self.homebase=True
        else:
            self.homebase=False
    
    def distance(self, a, b):
        return (b[0]-a[0], b[1]-a[1])
    
    def betrag(self, vect):
        return math.sqrt(math.pow(vect[0],2)+math.pow(vect[1],2))

    def act(self, view):
        if view.landed:
            res=view.cargo['ressources']
            guns=view.cargo['guns']
            armor=view.cargo['armor']
            if guns<3:
                if res[0]>=von_neumann.GUN_COST and res[1]>=von_neumann.GUN_COST and res[2]>=von_neumann.GUN_COST and view.landed:
                    return {'action':von_neumann.Action(von_neumann.ACT_BUILD_GUN), 'message':None}
                else:
                    return {'action':von_neumann.Action(von_neumann.ACT_IDLE), 'message':None}
            elif armor<1:
                if res[0]>=von_neumann.ARMOR_COST and res[1]>=von_neumann.ARMOR_COST and res[2]>=von_neumann.ARMOR_COST and view.landed:
                    return {'action':von_neumann.Action(von_neumann.ACT_BUILD_ARMOR), 'message':None}
                else:
                    return {'action':von_neumann.Action(von_neumann.ACT_IDLE), 'message':None}
            else:
                if res[0]>=von_neumann.PROBE_COST and res[1]>=von_neumann.PROBE_COST and res[2]>=von_neumann.PROBE_COST and view.landed:
                    direction = (random.uniform(-3,3), random.uniform(-3,3))
                    return {'action':von_neumann.Action(von_neumann.ACT_BUILD_PROBE, direction), 'message':None}
                else:
                    return {'action':von_neumann.Action(von_neumann.ACT_IDLE), 'message':None}
        else:
            if True:
                guns=view.cargo['guns']
                armor=view.cargo['armor']
                if guns<3 or armor<1:
                    return {'action':von_neumann.Action(von_neumann.ACT_LOAD, {'ressources':(0,0,0), 'guns':3-guns, 'armor':1-armor}), 'message':None}
                for probe in view.scans['probes']:
                    if probe['team_id']!=view.team_id:
                        if probe['sector']==view.sector:
                            print "RETALLIATION!!!"
                            return {'action':von_neumann.Action(von_neumann.ACT_ATTACK, probe['probe_id']), 'message':None}
                        return {'action':von_neumann.Action(von_neumann.ACT_MOVE, self.distance(view.pos, probe['pos'])), 'message':None}


            if False:
                for p in view.scans['probes']:
                    if p['pos']==view.sector and p['landed']:
                        if p['cargo']['guns']>0:
                            if view.free_slots>=von_neumann.GUN_SLOTS:
                                return {'action':von_neumann.Action(von_neumann.ACT_LOAD, {'ressources':(0,0,0), 'guns':1, 'armor':0}), 'message':None}
                        
                return {'action':von_neumann.Action(von_neumann.ACT_IDLE), 'message':None}

            empty_planets = []
            for planet in view.scans['planets']:
                if planet['populated']==False:
                    empty_planets.append((planet, self.distance(view.pos, planet['pos'])))
            if len(empty_planets)==0:
                return {'action':von_neumann.Action(von_neumann.ACT_MOVE, self.cargs), 'message':None}
            else:
                for (planet,dist) in empty_planets:
                    if planet['pos'][0]==view.sector[0] and planet['pos'][1]==view.sector[1] :
                        return {'action':von_neumann.Action(von_neumann.ACT_COLONIZE, None), 'message':None}
                    else:

                        return {'action':von_neumann.Action(von_neumann.ACT_MOVE, dist), 'message':None}
