von_neumann=__import__("von-neumann")
import math
import random

class ProbeAi(object):
    
    def distance(self, a, b):
        return (b[0]-a[0], b[1]-a[1])
    
    def betrag(self, vect):
        return math.sqrt(math.pow(vect[0],2)+math.pow(vect[1],2))

    def act(self, view):
        #print view.cargo
        #view.cargo['ressources']=[100,100,100]
    
        if view.landed:
            res=view.cargo['ressources']
            if res[0]>=von_neumann.PROBE_COST and res[1]>=von_neumann.PROBE_COST and res[2]>=von_neumann.PROBE_COST and view.landed:
                return von_neumann.Action(von_neumann.ACT_BUILD, 'probe')
            else:
                return von_neumann.Action(von_neumann.ACT_IDLE)
        else:
            empty_planets = []
            for planet in view.scans['planets']:
                if planet['populated']==False:
                    empty_planets.append((planet, self.distance(view.pos, planet['pos'])))
            if len(empty_planets)==0:
                x=random.uniform(-1,1)
                y=random.uniform(-1,1)
                vect=[x,y]
                return von_neumann.Action(von_neumann.ACT_MOVE, vect)
            else:
                for (planet,dist) in empty_planets:
                    print "ALARM!!!"
                    if planet['pos'][0]==view.sector[0] and planet['pos'][1]==view.sector[1] :
                        return von_neumann.Action(von_neumann.ACT_COLONIZE, None)
                    else:
                        return von_neumann.Action(von_neumann.ACT_MOVE, dist)
