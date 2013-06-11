#!/usr/bin/env python2

import random
import math
import sys
import time
from time import strftime, gmtime
import importlib
import copy
import pygame, pygame.locals
import pickle
import gzip

sys.path.reverse()
sys.path.append(sys.path[len(sys.path)-1]+'/ais')
sys.path.reverse()

UNIVERSE_WIDTH = 200
UNIVERSE_HEIGHT = 160
PLANETS = 160
SCALE = 3
RES_MAX = 100
CARGO_SLOTS = 10000
PROBE_COST = 1000
GUN_COST = 250
GUN_SLOTS = 2000
ARMOR_COST = 250
ARMOR_SLOTS = 2000
PROBE_SCAN_RANGE = 5
PROBE_ATTACK_RANGE = 1
MAX_SPEED=0.7
MAX_ROUNDS = 1350
PROBE_POINTS = 1
PLANET_POINTS=20
DEFAULT_TOURNAMENT_GAMES = 10
DEBUG_AI=True
MAXIMUM_STATION_GUNS = 4
MAXIMUM_STATION_ARMOR = 8
LIVE_STATS=False

#team colours
team_colours=[]
team_colours.append((255,0,0))
team_colours.append((0,255,0))
team_colours.append((0,0,255))
team_colours.append((255,255,0))
team_colours.append((255,0,255))
team_colours.append((0,255,255))

class MapLayer(object):
    def __init__(self, width, height, init=0):
        self.values=[[init for y in range(UNIVERSE_HEIGHT)] for x in range(UNIVERSE_WIDTH)]
        self.size=self.width, self.height = width, height
    def get(self, x, y):
        if (0 <= x < self.width) and (0 <= y < self.height):
            return self.values[x][y]
        else:
            return None

    def set(self, x, y, value):
        if (0 <= x < self.width) and (0 <= y < self.height):
            self.values[x][y]=value
        

class Display(object):
    def __init__(self, width, height, scale=2, video_mode=False):
        self.background = 0,0,0
        self.width, self.height = width, height
        self.scale = scale
        self.size = (self.width*scale , self.height*scale)
        pygame.init()
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("von Neumann")
        self.text = []
        self.draft_surface=pygame.Surface(self.size)
        self.planet_surface=pygame.Surface(self.size)
        self.probe_surface=pygame.Surface(self.size)
        self.planet_surface.set_colorkey(self.background)
        self.probe_surface.set_colorkey(self.background)
        self.video_mode=video_mode
    
    def set_frame(self, surface):
        self.screen.blit(surface, (0,0))
        pygame.display.flip()
    
    def get_event(self):
        for event in pygame.event.get(): # User did something
            if event.type == pygame.QUIT: # If user clicked close
                return 'quit'
            elif event.type==pygame.KEYUP:
                print event.key
                if event.key==113: #q
                    return 'quit'
                elif event.key==32: #SPACE
                    return 'playpause'
                elif event.key==118: #v
                    return 'stop'
                elif event.key==275: # right arrow
                    return 'right_arrow'
                elif event.key==276: #left arrow
                    return 'left_arrow'

    def update(self, planet_list, probe_list):
        self.draft_surface.lock()
        self.planet_surface.lock()
        self.probe_surface.lock()
        self.draft_surface.fill(self.background)
        self.planet_surface.fill(self.background)
        self.probe_surface.fill(self.background)
        self.draft_surface.unlock()
        if self.video_mode:
            for p in planet_list:
                if p[1]:
                    for x in xrange(0,SCALE):
                        for y in xrange(0,SCALE):
                            self.planet_surface.set_at((p[0][0]*SCALE+x,p[0][1]*SCALE+y),team_colours[p[2]])
                else:
                    for x in xrange(0,SCALE):
                        for y in xrange(0,SCALE):
                            self.planet_surface.set_at((SCALE*p[0][0]+x,SCALE*p[0][1]+y),(255,255,255))
            self.planet_surface.unlock()
            self.probe_surface.unlock()
            self.draft_surface.lock()
            for p in probe_list:
                self.probe_surface.set_at((int(math.floor(p[0][0]))*SCALE,int(math.floor(p[0][1]))*SCALE),team_colours[p[1]])
            self.draft_surface.unlock()     
            self.draft_surface.blit(self.planet_surface, (0,0))
            self.draft_surface.blit(self.probe_surface, (0,0))
            self.set_frame(self.draft_surface)
        else:
            for p in planet_list:
                if p.is_populated():
                    for x in xrange(0,SCALE):
                        for y in xrange(0,SCALE):
                            self.planet_surface.set_at((p.get_pos()[0]*SCALE+x,p.get_pos()[1]*SCALE+y),p.populating_probe().get_team().get_colour())
                else:
                    for x in xrange(0,SCALE):
                        for y in xrange(0,SCALE):
                            self.planet_surface.set_at((SCALE*p.get_pos()[0]+x,SCALE*p.get_pos()[1]+y),(255,255,255))
            self.planet_surface.unlock()
            self.probe_surface.unlock()
            self.draft_surface.lock()
            for p in probe_list:
                self.probe_surface.set_at((int(math.floor(p.get_pos()[0]))*SCALE,int(math.floor(p.get_pos()[1]))*SCALE),p.get_team().get_colour())
            self.draft_surface.unlock()     
            self.draft_surface.blit(self.planet_surface, (0,0))
            self.draft_surface.blit(self.probe_surface, (0,0))
            self.set_frame(self.draft_surface)

       
# Actions available to a probe on each turn.
ACT_BUILD_PROBE, ACT_BUILD_GUN, ACT_BUILD_ARMOR, ACT_MOVE, ACT_COLONIZE, ACT_LOAD, ACT_UNLOAD, ACT_ATTACK, ACT_IDLE = range(9)

class Action(object):
    '''
    A class for passing an action around.
    '''
    def __init__(self, action_type, data=None):
        self.type = action_type
        self.data = data

    def get_data(self):
        return self.data

    def get_type(self):
        return self.type



class Planet(object):
    def __init__(self, pos, resource):
        self.pos=pos
        self.resource=resource
        self.populated=False
        self.probe=None
    def populate(self, probe):
        probe.set_pos(copy.copy(self.pos))
        probe.set_landed(True)
        self.probe=probe
        self.populated=True
    
    def unpopulate(self):
        self.populated=False

    def get_pos(self):
        return self.pos
    
    def get_sector(self):
        return [int(math.floor(self.pos[0])),int(math.floor(self.pos[1]))]

    def get_res(self):
        return self.resource

    def scanned(self):
        if self.populated:
            return {'pos':self.pos, 'sector':self.get_sector(), 'res':self.resource, 'populated':self.populated, 'team_id':self.probe.get_team().get_id()}
        else:
            return {'pos':self.pos, 'sector':self.get_sector(), 'res':self.resource, 'populated':self.populated, 'team_id':None}
            
    def set_res(self, res):
        self.resource=res

    def is_populated(self):
        return self.populated
        
    def populating_probe(self):
        if self.is_populated()==True:
            return self.probe
        else:
            pass

class Probe(object):
    def __init__(self, pos, team, ai, probe_id, cargs):
        self.probe_id=probe_id
        self.pos = pos
        self.team = team
        self.ai = ai(cargs)
        self.landed=False
        self.cargo={'resources':[0,0,0], 'guns':0, 'armor':0}
        self.free_slots=CARGO_SLOTS
        self.act = self.ai.act
        self.death_message=self.ai.death_message
        self.network_id=None
    def get_team(self):
        return self.team

    def get_id(self):
        return self.probe_id
    
    def get_team_id(self):
        return self.team.get_id()
    
    def get_net_id(self):
        return self.network_id

    def set_net_id(self, net_id):
        self.network_id = net_id

    def scanned(self):
        return {'pos':self.pos, 'sector':self.get_sector(), 'landed':self.landed, 'cargo':self.cargo, 'team_id':self.team.get_id(), 'probe_id':self.probe_id}

    def get_ai(self):
        return self.ai

    def set_pos(self, pos):
        self.pos = pos
        
    def get_pos(self):
        return self.pos
    
    def get_sector(self):
        return [int(math.floor(self.pos[0])),int(math.floor(self.pos[1]))]

    def pay_probe(self):
        res=self.cargo['resources']
        res[0]-=PROBE_COST
        res[1]-=PROBE_COST
        res[2]-=PROBE_COST
    
    def pay_gun(self):
        res=self.cargo['resources']
        res[0]-=GUN_COST
        res[1]-=GUN_COST
        res[2]-=GUN_COST
    
    def pay_armor(self):
        res=self.cargo['resources']
        res[0]-=ARMOR_COST
        res[1]-=ARMOR_COST
        res[2]-=ARMOR_COST
    

    def set_landed(self, landed):
        self.landed=landed
        
    def get_landed(self):
        return self.landed

    def get_free_slots(self):
        self.free_slots=CARGO_SLOTS
        for i in xrange(3):
            self.free_slots-=self.cargo['resources'][i]
        self.free_slots-=GUN_SLOTS*self.cargo['guns']
        self.free_slots-=ARMOR_SLOTS*self.cargo['armor']
        return self.free_slots

    def get_cargo(self):
        return self.cargo

    def add_resources(self, res):
        for x in xrange(3):
            self.cargo['resources'][x]=self.cargo['resources'][x]+res[x]


class Team(object):
    def __init__(self, id_num, ai, colour, num_planets, num_probes):
        self.id_num=id_num
        self.ai=ai
        self.colour=colour
        self.num_planets=num_planets
        self.num_probes=num_probes

    def add_num_probes(self, num):
        self.num_probes+=num

    def add_num_planets(self, num):
        self.num_planets+=num

    def set_num_probes(self, num):
        self.num_probes=num

    def set_num_planets(self, num):
        self.num_planets=num

    def get_num_probes(self):
        return self.num_probes

    def get_num_planets(self):
        return self.num_planets

    def get_alive(self):
        if self.get_num_probes()>0:
            return 1
        else:
            return 0

    def get_ai(self):
        return self.ai

    def get_colour(self):
        return self.colour
        
    def get_id(self):
        return self.id_num

    def get_points(self):
        return self.num_probes*PROBE_POINTS+self.num_planets*PLANET_POINTS

class View(object):
    def __init__(self, probe, grid, message_queues):
        self.pos=probe.get_pos()
        self.cargo=probe.get_cargo()
        self.free_slots=probe.get_free_slots()
        self.team_id=probe.get_team().get_id()
        self.landed=probe.get_landed()
        self.sector=[int(math.floor(self.pos[0])),int(math.floor(self.pos[1]))]
        self.scans = {'planets':[], 'probes':[]}
        self.probe_id = probe.get_id()
        for x in xrange(-PROBE_SCAN_RANGE,PROBE_SCAN_RANGE+1):
            for y in xrange(-PROBE_SCAN_RANGE,PROBE_SCAN_RANGE+1):
                if self.sector[0]+x<0:
                    x+=UNIVERSE_WIDTH
                elif self.sector[0]+x>UNIVERSE_WIDTH-1:
                    x-=UNIVERSE_WIDTH
                if self.sector[1]+y<0:
                    y+=UNIVERSE_HEIGHT
                elif self.sector[1]+y>UNIVERSE_HEIGHT-1:
                    y-=UNIVERSE_HEIGHT
                for planet in grid[self.sector[0]+x][self.sector[1]+y]['planets']:
                    self.scans['planets'].append(planet.scanned())
                for p in grid[self.sector[0]+x][self.sector[1]+y]['probes']:
                    self.scans['probes'].append(p.scanned())
        self.messages=message_queues[probe.get_team().get_id()]

def fight(attacker, victim):
    if attacker.get_landed():
        if attacker.get_cargo()['guns']>0:
            if attacker.get_cargo()['guns']>=MAXIMUM_STATION_GUNS:
                attack_bonus=MAXIMUM_STATION_GUNS
            else:
                attack_bonus=attacker.get_cargo()['guns']
        else:
            return False
    else:
        if attacker.get_cargo()['guns']>0:
            attack_bonus=attacker.get_cargo()['guns']
        else:
            return False

    if victim.get_landed():
        if victim.get_cargo()['armor']>=MAXIMUM_STATION_ARMOR:
            defense_bonus=MAXIMUM_STATION_ARMOR
        else:
            defense_bonus=victim.get_cargo()['armor']
    else:
        defense_bonus=victim.get_cargo()['armor']

    min_dice_val=10-attack_bonus+defense_bonus
    return random.randint(0,20)>min_dice_val
class Snapshot(object):
    def __init__(self, probe_list, planet_list, round_count):
        self.probe_list=(probe_list)
        self.planet_list=(planet_list)
        self.round_count=(round_count)


class Recording(object):
    def __init__(self, time, team_list, universe_size):
        self.time=time
        self.team_list=team_list
        self.UNI_WIDTH=universe_size[0]
        self.UNI_HEIGHT=universe_size[1]
        self.snapshot_list=[]
        self.winner=None
        
    def add_snapshot(self, snapshot):
        self.snapshot_list.append(snapshot)
   

def dump_recording(filename, recording):
    f=gzip.open(filename, 'w')
    pickle.dump(recording,f)
    f.close()

class VideoPlayer(object):
    def __init__(self, video_file, fps):
        self.video_file=video_file
        self.fps=fps
        f=gzip.open(self.video_file, 'r')
        self.recording=pickle.load(f)
        f.close
        #generate display
        self.mydisplay = Display(self.recording.UNI_WIDTH, self.recording.UNI_HEIGHT, SCALE, True)
    
    def play(self):
        index=0
        max_i=len(self.recording.snapshot_list)
        pause=False
        while 1:
            #update display
            event=self.mydisplay.get_event()
            if event=='quit':
                sys.exit()
            elif event=='playpause':
                pause = not pause
            elif event=='stop':
                pause=True
                index=0
            elif event=='left_arrow' and pause:
                index-=1
                if index<0:
                    index=max_i-1
            elif event=='right_arrow' and pause:
                index+=1
                if index>=max_i:
                    index=0
           
            else:
                snapshot = self.recording.snapshot_list[index]
                self.mydisplay.update(snapshot.planet_list, snapshot.probe_list)
                if not pause:
                    index+=1
                    if index>=max_i:
                        index=0
        return None
        

class Game(object):
    def __init__(self, ai_list, record):
        self.rounds=0
        self.ais= [ai[1].ProbeAi for ai in ai_list]
        self.probe_id_counter=0
        self.finished=False
        #create grid
        self.grid=[]
        for x in xrange(UNIVERSE_WIDTH):
            self.grid.append([])
            for y in xrange(UNIVERSE_HEIGHT):
                self.grid[x].append({'probes':[], 'planets':[]})

        #create planets
        self.planet_list = []
        xtemp = random.randint(0,UNIVERSE_WIDTH-1)
        ytemp = random.randint(0,UNIVERSE_HEIGHT-1)
        res_a = random.randint(0,RES_MAX)
        res_b = random.randint(0,RES_MAX)
        if res_b+res_a>RES_MAX:
            res_b=RES_MAX-res_a
        res=[res_a,res_b,0]
        random.shuffle(res)
        planet_temp = Planet([xtemp,ytemp], res)
        self.planet_list.append(planet_temp)
        self.grid[xtemp][ytemp]['planets'].append(planet_temp)
        for x in xrange(PLANETS-1):
            while sum(1 for i in self.planet_list if i.get_pos()==[xtemp,ytemp])!=0:
                xtemp = random.randint(0,UNIVERSE_WIDTH-1)
                ytemp = random.randint(0,UNIVERSE_HEIGHT-1)
            
            res_a = random.randint(0,RES_MAX)
            res_b = random.randint(0,RES_MAX)
            if res_b+res_a>RES_MAX:
                res_b=RES_MAX-res_a
            res=[res_a,res_b,0]
            random.shuffle(res)
            planet_temp = Planet([xtemp,ytemp], res)
            self.planet_list.append(planet_temp)
            self.grid[xtemp][ytemp]['planets'].append(planet_temp)
        
        #set equal resources for all homeworlds
        res_a = random.randint(10,RES_MAX)
        res_b = random.randint(10,RES_MAX)
        res_c = random.randint(10,RES_MAX)
        res=[res_a,res_b,res_c]
        for x in xrange(0,len(ai_list)):
            self.planet_list[x].set_res(res)    
            
        #team stuff
        self.team_list = []
        self.message_queues=[]
        for x in xrange(0, len(ai_list)):
            self.team_list.append(Team(x, ai_list[x], team_colours[x], 1, 1))
            self.message_queues.append([])

        recording_team_list=[]
        for i in xrange(len(ai_list)):
            recording_team_list.append([i, ai_list[i][0]])           

        #create recording
        if record:
            self.record=True
            self.recording=Recording(gmtime(), recording_team_list, [UNIVERSE_WIDTH,UNIVERSE_HEIGHT])
            self.recording_filename='recordings/'+strftime("%m_%d__%H%M%S",self.recording.time)+'.vn'
        else:
            self.record=False

        #create initial probes
        self.probe_list = []
        for x in xrange(0, len(ai_list)):
            temp_probe=Probe([0,0], self.team_list[x], self.ais[x], self.probe_id_counter, 'initial')
            self.probe_id_counter+=1
            self.probe_list.append(temp_probe)
            self.grid[self.planet_list[x].get_pos()[0]][self.planet_list[x].get_pos()[1]]['probes'].append(temp_probe)
            self.planet_list[x].populate(self.probe_list[x])
        
        #generate display
        self.mydisplay = Display(UNIVERSE_WIDTH, UNIVERSE_HEIGHT, SCALE)
    
    def append_view(self, probe):
        view=View(probe,self.grid, self.message_queues)
        self.view_list.append((probe, copy.deepcopy(view)))
        
    def tick(self):
        self.rounds=self.rounds+1
        if LIVE_STATS:
            #print information
            print "round:  ", self.rounds
            print "probes:"
            for t in self.team_list:
                print "    team",t.get_id(),": ",t.get_num_probes()
            print "    total  : ", len(self.probe_list)
            print "planets:"
            for t in self.team_list:
                print "    team",t.get_id(),": ",t.get_num_planets()
            
        
        #check for end of game
        num_players=sum(t.get_alive() for t in self.team_list)
        if num_players<2:
            self.finished==True
            if num_players==0:
                if self.record:
                    self.recording.winner='draw'
                    dump_recording(self.recording_filename, self.recording)
                return 'draw'
            else:
                for t in self.team_list:
                    if t.get_num_probes!=0:
                        winner=t
                        if self.record:
                            self.recording.winner=copy.copy(t.get_id())
                            dump_recording(self.recording_filename, self.recording)
                return winner.get_id()
        if self.rounds>MAX_ROUNDS:
            winner_list= sorted(self.team_list, key=lambda team: team.get_points(), reverse=True)
            if self.record:
                self.recording.winner=copy.copy(winner_list[0].get_id())
                dump_recording(self.recording_filename, self.recording)
            return winner_list[0].get_id()
        
        #resource mining
        for p in self.planet_list:
            if p.is_populated():
                p.populating_probe().add_resources(p.get_res())
                
        #create probe/view list
        self.view_list=[]
        for p in self.probe_list:
            self.append_view(p)

        #create action and message list
        action_list = []
        self.message_list = []
        for (p,v) in self.view_list:
            if DEBUG_AI:
                reaction=p.act(v)
            else:
                try:
                    reaction=p.act(v)
                except:
                    print "The ai of team",p.get_team().get_id(),"caused an error!"
                    reaction={'action':Action(ACT_IDLE), 'message':None} 
            if reaction==None:
                reaction={'action':Action(ACT_IDLE), 'message':None} 
            action_list.append((p, reaction['action']))
            if reaction['message']!=None:
                self.message_list.append((p, reaction['message']))
            
        
                
        #fight
        death_list=[]
        for (p,act) in action_list:
            if act.get_type()==ACT_ATTACK:
                victim_id=act.get_data()
                p_sector=p.get_sector()
                probes=[]
                victim=None
                for x in xrange(-PROBE_ATTACK_RANGE,PROBE_ATTACK_RANGE+1):
                    for y in xrange(-PROBE_ATTACK_RANGE,PROBE_ATTACK_RANGE+1):
                        if p_sector[0]+x<0:
                            x+=UNIVERSE_WIDTH
                        elif p_sector[0]+x>UNIVERSE_WIDTH-1:
                            x-=UNIVERSE_WIDTH
                        if p_sector[1]+y<0:
                            y+=UNIVERSE_HEIGHT
                        elif p_sector[1]+y>UNIVERSE_HEIGHT-1:
                            y-=UNIVERSE_HEIGHT
                        probes.append(self.grid[p_sector[0]+x][p_sector[1]+y]['probes'])

                for px in probes:
                    for pp in px:
                        if pp.get_id()==victim_id:
                            victim=pp
                if victim!=None:
                    if fight(p,victim):
                        death_list.append(victim)
                        #print "KILL"
        
                        
        #remove killed probes
        death_set=set(death_list)
        for k in death_set:
            k_sector=k.get_sector()
            for (p,m) in self.message_list:
                if p==k:
                    self.message_list.remove((p,m))
            for (p,v) in self.view_list:
                if p==k:
                    death_message=k.death_message(v)
                    if death_message!=None:
                        #pass
                        self.message_list.append((k, death_message))
                    break
            for action in action_list:
                if action[0]==k:
                    action_list.remove(action)
            
            self.grid[k_sector[0]][k_sector[1]]['probes'].remove(k)
            if k.get_landed():
                self.grid[k_sector[0]][k_sector[1]]['planets'][0].unpopulate()
                self.team_list[k.get_team().get_id()].add_num_planets(-1)
            self.team_list[k.get_team().get_id()].add_num_probes(-1)
            self.probe_list.remove(k)
        
                        
        #sort messages
        for i in xrange(len(self.message_queues)):
            self.message_queues[i]=[]

        for (p,m) in self.message_list:
            self.message_queues[p.get_team().get_id()].append(m)
        

        #if LIVE_STATS:
            #print "message volume:"
            #for t in self.team_list:
            #    print "    team",t.get_id(),": ", sys.getsizeof(self.message_queues[t.get_id()])

        #colonize planets
        for (p,act) in action_list:
            if act.get_type()==ACT_COLONIZE:
                p_sector=p.get_sector()
                if len(self.grid[p_sector[0]][p_sector[1]]['planets'])==1:
                    if self.grid[p_sector[0]][p_sector[1]]['planets'][0].is_populated()==False:
                        self.grid[p_sector[0]][p_sector[1]]['planets'][0].populate(p)
                        #p.set_pos(p_sector)
                        #p.set_landed(True)
                        self.team_list[p.get_team().get_id()].add_num_planets(1)

        #build new probes
        for (p,act) in action_list:
            if act.get_type()==ACT_BUILD_PROBE:
                res=p.get_cargo()['resources']
                if p.get_landed() and res[0]>=PROBE_COST and res[1]>=PROBE_COST and res[2]>=PROBE_COST:
                    temp_probe=Probe(copy.deepcopy(p.get_pos()), p.get_team(), p.get_team().get_ai()[1].ProbeAi, self.probe_id_counter, copy.deepcopy(act.get_data()))
                    self.probe_id_counter+=1
                    self.probe_list.append(temp_probe)
                    self.grid[p.get_sector()[0]][p.get_sector()[1]]['probes'].append(temp_probe)
                    #print self.grid
                    p.pay_probe()
                    self.team_list[p.get_team().get_id()].add_num_probes(1)
        
        #build new guns
        for (p,act) in action_list:
            if act.get_type()==ACT_BUILD_GUN:
                res=p.get_cargo()['resources']
                if p.get_landed() and res[0]>=GUN_COST and res[1]>=GUN_COST and res[2]>=GUN_COST:
                    p.cargo['guns']+=1
                    #print self.grid
                    p.pay_gun()
        
        #build new armor
        for (p,act) in action_list:
            if act.get_type()==ACT_BUILD_ARMOR:
                res=p.get_cargo()['resources']
                if p.get_landed() and res[0]>=ARMOR_COST and res[1]>=ARMOR_COST and res[2]>=ARMOR_COST:
                    p.cargo['armor']+=1
                    #print self.grid
                    p.pay_armor()
        
        #load stuff
        for (p,act) in action_list:
            if act.get_type()==ACT_LOAD:
                cargo=act.get_data()
                if len(self.grid[p.get_sector()[0]][p.get_sector()[1]]['planets'])==1 and p.get_landed()==False:
                    if self.grid[p.get_sector()[0]][p.get_sector()[1]]['planets'][0].is_populated():
                        landed_probe=self.grid[p.get_sector()[0]][p.get_sector()[1]]['planets'][0].populating_probe()
                        if landed_probe.get_team()==p.get_team():
                            #resources
                            wanted_res=cargo['resources']
                            probe_res=p.get_cargo()['resources']
                            station_res=landed_probe.get_cargo()['resources']
                            free_slots=p.get_free_slots()
                            for i in xrange(3):
                                if wanted_res[i]<=station_res[i]:
                                    if free_slots>=wanted_res[i]:
                                        station_res[i]-=wanted_res[i]
                                        probe_res[i]+=wanted_res[i]
                                        free_slots-=wanted_res[i]
                                    else:
                                        station_res[i]-=free_slots
                                        probe_res[i]+=free_slots
                                        free_slots=0
                                else:
                                    if free_slots>=station_res[i]:
                                        probe_res[i]+=station_res[i]
                                        free_slots-=station_res[i]
                                        station_res[i]=0
                                    else:
                                        station_res[i]-=free_slots
                                        probe_res[i]+=free_slots
                                        free_slots=0
                            #guns
                            wanted_guns=cargo['guns']
                            station_guns=landed_probe.get_cargo()['guns']
                            probe_guns=p.get_cargo()['guns']

                            if wanted_guns<=station_guns:
                                if free_slots>=GUN_SLOTS*wanted_guns:
                                    probe_guns+=wanted_guns
                                    station_guns-=wanted_guns
                                else:
                                    probe_guns+=int(math.floor(free_slots/GUN_SLOTS))
                                    station_guns-=int(math.floor(free_slots/GUN_SLOTS))
                            else:
                                if free_slots>=GUN_SLOTS*station_guns:
                                    probe_guns+=station_guns
                                    station_guns=0
                                else:
                                    probe_guns+=int(math.floor(free_slots/GUN_SLOTS))
                                    station_guns-=int(math.floor(free_slots/GUN_SLOTS))
                            p.get_cargo()['guns']=probe_guns
                            landed_probe.get_cargo()['guns']=station_guns


                            #armor
                            wanted_armor=cargo['armor']
                            station_armor=landed_probe.get_cargo()['armor']
                            probe_armor=p.get_cargo()['armor']

                            if wanted_armor<=station_armor:
                                if free_slots>=GUN_SLOTS*wanted_armor:
                                    probe_armor+=wanted_armor
                                    station_armor-=wanted_armor
                                else:
                                    probe_armor+=int(math.floor(free_slots/ARMOR_SLOTS))
                                    station_armor-=int(math.floor(free_slots/ARMOR_SLOTS))
                            else:
                                if free_slots>=GUN_SLOTS*station_armor:
                                    probe_armor+=station_armor
                                    station_armor=0
                                else:
                                    probe_armor+=int(math.floor(free_slots/ARMOR_SLOTS))
                                    station_armor-=int(math.floor(free_slots/ARMOR_SLOTS))
                            p.get_cargo()['armor']=probe_armor
                            landed_probe.get_cargo()['armor']=station_armor

        #unload stuff
        for (p,act) in action_list:
            if act.get_type()==ACT_UNLOAD:
                cargo=act.get_data()
                if len(self.grid[p.get_sector()[0]][p.get_sector()[1]]['planets'])==1 and p.get_landed()==False:
                    if self.grid[p.get_sector()[0]][p.get_sector()[1]]['planets'][0].is_populated():
                        landed_probe=self.grid[p.get_sector()[0]][p.get_sector()[1]]['planets'][0].populating_probe()
                        if landed_probe.get_team()==p.get_team():
                            #resources
                            dump_res=cargo['resources']
                            probe_res=p.get_cargo()['resources']
                            station_res=landed_probe.get_cargo()['resources']
                            for i in xrange(3):
                                if dump_res[i]<=probe_res[i]:
                                    probe_res[i]-=dump_res[i]
                                    station_res[i]+=dump_res[i]
                                else:
                                    station_res[i]+=probe_res[i]
                                    probe_res[i]=0

                            #guns
                            dump_guns=cargo['guns']
                            probe_guns=p.get_cargo()['guns']
                            station_guns=landed_probe.get_cargo()['guns']
                            if dump_guns<=probe_guns:
                                probe_guns-=dump_guns
                                station_guns+=dump_guns
                            else:
                                station_guns+=probe_guns
                                probe_guns=0
                            p.get_cargo()['guns']=probe_guns
                            landed_probe.get_cargo()['guns']=station_guns


                            #armor
                            dump_armor=cargo['armor']
                            probe_armor=p.get_cargo()['armor']
                            station_armor=landed_probe.get_cargo()['armor']
                            if dump_armor<=probe_armor:
                                probe_armor-=dump_armor
                                station_armor+=dump_armor
                            else:
                                station_armor+=probe_armor
                                probe_armor=0
                            p.get_cargo()['armor']=probe_armor
                            landed_probe.get_cargo()['armor']=station_armor
        #move probes
        for (p,act) in action_list:
            if act.get_type()==ACT_MOVE:
                if p.get_landed()==False:
                    pos=p.get_pos()
                    self.grid[int(math.floor(p.get_pos()[0]))][int(math.floor(p.get_pos()[1]))]['probes'].remove(p)
                    betrag=math.sqrt(math.pow(act.get_data()[0],2)+math.pow(act.get_data()[1],2))
                    if betrag>MAX_SPEED:
                        pos[0]=pos[0]+MAX_SPEED*act.get_data()[0]/betrag
                        pos[1]=pos[1]+MAX_SPEED*act.get_data()[1]/betrag
                    else:
                        pos[0]=pos[0]+act.get_data()[0]
                        pos[1]=pos[1]+act.get_data()[1]
                    if math.floor(pos[0])>=UNIVERSE_WIDTH:
                        pos[0]-=UNIVERSE_WIDTH
                    elif math.floor(pos[0])<0:
                        pos[0]+=UNIVERSE_WIDTH
                    if math.floor(pos[1])>=UNIVERSE_HEIGHT:
                        pos[1]-=UNIVERSE_HEIGHT
                    elif math.floor(pos[1])<0:
                        pos[1]+=UNIVERSE_HEIGHT
                    p.set_pos(pos)
                    try:
                        self.grid[int(math.floor(p.get_pos()[0]))][int(math.floor(p.get_pos()[1]))]['probes'].append(p)
                    except:
                        print p.get_pos()
                        print pos
                        while 1:
                            pass

                else:
                    print "landed probe of team",p.get_team().get_id(),  "attempted to move"
        
        #record snapshot
        if self.record:
            recording_probe_list=[]
            recording_planet_list=[]
            for probe in self.probe_list:
                recording_probe_list.append([probe.get_sector()[:], copy.copy(probe.get_team().get_id())])
            for planet in self.planet_list:
                if planet.is_populated():
                    recording_planet_list.append([planet.get_sector()[:], copy.copy(planet.is_populated()), copy.copy(planet.populating_probe().get_team().get_id())])
                else:
                    recording_planet_list.append([planet.get_sector()[:], copy.copy(planet.is_populated())])                 
            snapshot=Snapshot(recording_probe_list, recording_planet_list, self.rounds)
            self.recording.add_snapshot(snapshot)
               
        
        #update display
        self.mydisplay.update(self.planet_list, self.probe_list)
        event=self.mydisplay.get_event
        if event=='quit':
            if self.record:
                dump_recording(self.recording_filename, self.recording)
            return 'quit'
        return None
        
            
            
def get_ai(name):
    importlib.import_module(name)
    ai = sys.modules[name]
    ai.name = name
    return ai


def play_video(record_file):
    videoplayer=VideoPlayer(record_file, 25)
    return videoplayer.play()
    

def play_game(record):
    mygame = Game(ai_list,record)
    winner=None
    while winner==None:
        winner=mygame.tick()
    if winner=='draw':
        print "Draw!"
    else:
        print "The winner is Team ",winner
    return winner


def play_tournament(num_games, record):
    win_table=[[x,0] for x in xrange(len(ai_list))]
    for i in xrange(num_games):
        winner=play_game(record)
        if winner!='draw':
            win_table[winner][1]+=1
    sorted_win_table=sorted(win_table, key=lambda x: x[1], reverse=True)
    print "--------------------"
    print "Tournament results:"
    print " "
    print "  | ID | WINS | NAME"
    print "-------------------------------"
    for x in xrange(len(sorted_win_table)):
        print x+1,"| ", sorted_win_table[x][0], "|  ", sorted_win_table[x][1], " |",ai_list[sorted_win_table[x][0]][0] 
    print "-------------------------------"

def main():
    global ai_list
    tournament=False
    record=False
    replay=False
    while sys.argv.count ('--record'):
        record=True
        r_index=sys.argv.index('--record')
        sys.argv.pop(r_index)
    while sys.argv.count ('--replay'):
        record=False
        replay=True
        r_index=sys.argv.index('--replay')
        replay_file=sys.argv[r_index+1]
        sys.argv.pop(r_index+1)
        sys.argv.pop(r_index)
   
    while sys.argv.count('-t')>0:
        tournament=True
        t_index=sys.argv.index('-t')
        try:
            num_games=int(sys.argv[t_index+1])
            sys.argv.pop(t_index+1)
            sys.argv.pop(t_index)
        except:
            num_games=DEFAULT_TOURNAMENT_GAMES
            sys.argv.pop(t_index)
    
    ai_list = [(n, get_ai(n)) for n in sys.argv[1:]]
    if replay:
        play_video(replay_file)
    elif tournament==False:
        play_game(record)
    else:
        play_tournament(num_games, record)


if __name__ == "__main__":
    main()
