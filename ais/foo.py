von_neumann=__import__("von-neumann")


class ProbeAi(object):
    def act(self, view):
        #print view.cargo
        #view.cargo['ressources']=[100,100,100]
        res=view.cargo['ressources']
        if res[0]>=10000 and res[1]>=10000 and res[2]>=10000 and view.landed:
            return von_neumann.Action(von_neumann.ACT_BUILD, 'probe')
        else:
             return von_neumann.Action(von_neumann.ACT_IDLE)

