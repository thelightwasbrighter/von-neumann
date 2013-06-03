von_neumann=__import__("von-neumann")
import math
import random

class ProbeAi(object):
    def act(self, view):
        #print view.cargo
        #view.cargo['ressources']=[100,100,100]
        if view.landed:
            res=view.cargo['ressources']
            if res[0]>=10000 and res[1]>=10000 and res[2]>=10000 and view.landed:
                return von_neumann.Action(von_neumann.ACT_BUILD, 'probe')
            else:
                return von_neumann.Action(von_neumann.ACT_IDLE)
        else:
            x=random.uniform(-1,1)
            y=random.uniform(-1,1)
            betrag=math.sqrt(math.pow(x,2)+math.pow(y,2))
            vect=[x/betrag,y/betrag]
            return von_neumann.Action(von_neumann.ACT_MOVE, vect)
