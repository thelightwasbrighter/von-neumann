'''
This probe finds new planets, transports resources and reproduces.
No fighting at all.
'''

von_neumann=__import__("von-neumann")
import math
import random

class ProbeAi(object):
    
    def __init__(self, cargs):
        self.cargs=cargs
        self.direction=None
        self.submission=None
        if cargs=='initial':
            self.mission='produce'
        elif cargs=='search':
            self.mission='search'
        elif cargs=='transport':
            self.mission='transport'
        else:
            print "Warning, no mission!"
            self.mission='none'

    def distance(self, a, b):
        return (b[0]-a[0], b[1]-a[1])
    
    def min_res(self, view):
        local_sector=view.sector
        for p in view.scans['planets']:
            if p['sector']==local_sector:
                local_planet=p
        p_res=p['res']
        lowest=101
        for x in xrange(3):
            if p_res[x]<lowest:
                lowest=p_res[x]
                m=x
        return m

    def max_res(self, view):
        local_sector=view.sector
        for p in view.scans['planets']:
            if p['sector']==local_sector:
                local_planet=p
        p_res=p['res']
        highest=0
        for x in range(3):
            if p_res[x]>highest:
                highest=p_res[x]
                m=x
        return m

    def max_res2(self, res):
        highest=0
        for x in range(3):
            if res[x]>highest:
                highest=res[x]
                m=x
        return m


    def betrag(self, vect):
        return math.sqrt(math.pow(vect[0],2)+math.pow(vect[1],2))

    def get_transport_mission(self, view):
        #get local maximum resource
        local_planet_pos=None
        random.shuffle(view.messages)
        ran=random.uniform(0,1)
        for planet in view.scans['planets']:
            if planet['sector']==view.sector and planet['team_id']==view.team_id:
                local_planet_pos=planet['pos']
                local_planet_have=self.max_res2(planet['res'])
        if local_planet_pos==None or ran<0.3:
            local_planet_pos=view.messages[0]['pos']
            local_planet_have=view.messages[0]['have']
        receiver_pos=None
        receiver_dist=1000000
        for m in view.messages:
            if m['need']==local_planet_have:
                if receiver_dist>self.betrag(self.distance(local_planet_pos,m['pos'])):
                    receiver_pos=m['pos']
                    receiver_dist=self.betrag(self.distance(local_planet_pos,m['pos']))
        if receiver_pos==None:
            #print "no receiver found, selecting randomly"
            receiver_pos=view.messages[1]['pos']
            
        return {'res':local_planet_have, 'sender_pos':local_planet_pos, 'receiver_pos':receiver_pos}


    def act(self, view):
        if self.mission=='produce':
            if view.landed==False:
                self.mission='search'
                return {'action':von_neumann.Action(von_neumann.ACT_IDLE), 'message':None}
            
            message={'pos':view.pos, 'need':self.min_res(view), 'have':self.max_res(view)}
            x=random.uniform(0,1)
            if x<0.5 or len(view.messages)<4:
                #produce searcher
                return {'action':von_neumann.Action(von_neumann.ACT_BUILD_PROBE, 'search'), 'message':message}
            else:
                #procuce transporter
                return {'action':von_neumann.Action(von_neumann.ACT_BUILD_PROBE, 'transport'), 'message':message}
        elif self.mission=='search':
            if self.direction==None:
                self.direction=[random.uniform(-2,2),random.uniform(-2,2)]
            closest_empty_planet=(None,100)
            for planet in view.scans['planets']:
                if planet['populated']==False:
                    if self.betrag(self.distance(view.pos, planet['pos']))<closest_empty_planet[1]:
                        closest_empty_planet=(planet, self.betrag(self.distance(view.pos, planet['pos'])))
            if closest_empty_planet[0]!=None:
                if closest_empty_planet[0]['sector']==view.sector:
                    self.mission='produce'
                    return {'action':von_neumann.Action(von_neumann.ACT_COLONIZE), 'message':None}
                else:
                    return {'action':von_neumann.Action(von_neumann.ACT_MOVE, self.distance(view.pos, closest_empty_planet[0]['pos'])), 'message':None}
            else:
                #fly in random direction
                if view.sector[0]==0:
                    self.direction[0]=random.uniform(0,2)
                if view.sector[0]==von_neumann.UNIVERSE_WIDTH-1:
                    self.direction[0]=random.uniform(-2,0)
                if view.sector[1]==0:
                    self.direction[1]=random.uniform(0,2)
                if view.sector[1]==von_neumann.UNIVERSE_HEIGHT-1:
                    self.direction[1]=random.uniform(-2,0)
                return {'action':von_neumann.Action(von_neumann.ACT_MOVE, self.direction), 'message':None}
        elif self.mission=='transport':
            if self.submission==None:
                if len(view.messages)<2:
                    return {'action':von_neumann.Action(von_neumann.ACT_IDLE), 'message':None}
                self.transport_mission=self.get_transport_mission(view)
                self.submission='goto_sender'
                self.direction=self.distance(view.pos,self.transport_mission['sender_pos'])
                return {'action':von_neumann.Action(von_neumann.ACT_MOVE, self.direction), 'message':None}
            elif self.submission=='goto_sender':
                if view.sector==[int(math.floor(self.transport_mission['sender_pos'][0])),int(math.floor(self.transport_mission['sender_pos'][1]))]:
                    load_res=[0,0,0]
                    load_res[self.transport_mission['res']]=von_neumann.CARGO_SLOTS
                    self.submission='goto_receiver'
                    return {'action':von_neumann.Action(von_neumann.ACT_LOAD, {'resources':load_res, 'guns':0, 'armor':0}), 'message':None}
                else:
                    self.direction=self.distance(view.pos,self.transport_mission['sender_pos'])
                    return {'action':von_neumann.Action(von_neumann.ACT_MOVE, self.direction), 'message':None}
            elif self.submission=='goto_receiver':
                if view.sector==[int(math.floor(self.transport_mission['receiver_pos'][0])),int(math.floor(self.transport_mission['receiver_pos'][1]))]:
                    #print "arrived at receiver_pos, mission complete"
                    unload_res=[von_neumann.CARGO_SLOTS,von_neumann.CARGO_SLOTS,von_neumann.CARGO_SLOTS]
                    self.submission=None
                    return {'action':von_neumann.Action(von_neumann.ACT_UNLOAD, {'resources':unload_res, 'guns':0, 'armor':0}), 'message':None}
                else:
                    self.direction=self.distance(view.pos,self.transport_mission['receiver_pos'])
                    return {'action':von_neumann.Action(von_neumann.ACT_MOVE, self.direction), 'message':None}
        else:
            print "Warning, no mission!"
        
