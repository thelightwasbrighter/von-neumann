#!/usr/bin/env python2

#import ConfigParser
import random
import math
import sys
import time
import importlib
import copy
#import numpy
import pygame, pygame.locals
sys.path.reverse()
sys.path.append(sys.path[len(sys.path)-1]+'/ais')
sys.path.reverse()
#print sys.path[len(sys.path)-1]
   

UNIVERSE_WIDTH = 600
UNIVERSE_HEIGHT = 350
PLANETS = 300
SCALE = 2
RES_MAX = 100
CARGO_SLOTS = 10000
PROBE_COST = 1000
PROBE_RANGE = 1
PLANET_RANGE = 5


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
    def __init__(self, width, height, scale=2):
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
        
    
    def set_frame(self, surface):
        self.screen.blit(surface, (0,0))
        pygame.display.flip()
    
    def update(self, planet_list, probe_list):
        self.draft_surface.fill(self.background)
        self.planet_surface.fill(self.background)
        self.probe_surface.fill(self.background)
        for p in planet_list:
            if p.is_populated():
                for x in range(0,SCALE):
                    for y in range(0,SCALE):
                        self.planet_surface.set_at((p.get_pos()[0]*SCALE+x,p.get_pos()[1]*SCALE+y),p.populating_probe().get_team().get_colour())
            else:
                for x in range(0,SCALE):
                    for y in range(0,SCALE):
                        self.planet_surface.set_at((SCALE*p.get_pos()[0]+x,SCALE*p.get_pos()[1]+y),(255,255,255))
        
        for p in probe_list:
            self.probe_surface.set_at((int(math.floor(p.get_pos()[0]))*SCALE,int(math.floor(p.get_pos()[1]))*SCALE),p.get_team().get_colour())
            
        self.draft_surface.blit(self.planet_surface, (0,0))
        self.draft_surface.blit(self.probe_surface, (0,0))
        self.set_frame(self.draft_surface)

    def new_draft(self):
        self.draft_surface.fill((0,0,0))

    def draw_planet(self, pos, colour):
        for x in range(0,SCALE):
            for y in range(0,SCALE):
                self.draft_surface.set_at((SCALE*pos[0]+x,SCALE*pos[1]+y),colour)
        
    
    def draw_draft(self):
        self.set_frame(self.draft_surface)


# Actions available to an agent on each turn.
ACT_BUILD, ACT_MOVE, ACT_COLONIZE, ACT_IDLE = range(4)

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
    def __init__(self, pos, ressource):
        self.pos=pos
        self.ressource=ressource
        self.populated=False
        self.probe=None

    def populate(self, probe):
        self.probe=probe
        self.populated=True
    
    def unpopulate(self):
        self.populated=False

    def get_pos(self):
        return self.pos

    def get_res(self):
        return self.ressource

    def scanned(self):
        if self.populated:
            return {'pos':self.pos, 'res':self.ressource, 'populated':self.populated, 'team_id':self.probe.get_team().get_id()}
        else:
            return {'pos':self.pos, 'res':self.ressource, 'populated':self.populated, 'team_id':None}
            
    def set_res(self, res):
        self.ressource=res

    def is_populated(self):
        return self.populated
        
    def populating_probe(self):
        if self.is_populated()==True:
            return self.probe
        else:
            pass

def assign_networks(grid, probe_list):
    probe_check=[]
    id_count=0
    temp_id=0
    for n in probe_list:
        probe_check.append(False)
    while probe_check.count(False)>0:
        init_probe=probe_list[probe_check.index(False)]
        check_grid=[]
        for x in range(UNIVERSE_WIDTH):
            check_grid.append([])
            for y in range(UNIVERSE_HEIGHT):
                check_grid[x].append(False)
        probe_queue=[init_probe]
        probe_list_temp=[]
        while len(probe_queue)!=0:
            #print probe_queue
            probe_temp=probe_queue.pop()
            for x in range(-PROBE_RANGE,PROBE_RANGE):
                if probe_temp.get_sector()[0]+x>=0 and probe_temp.get_sector()[0]+x<UNIVERSE_WIDTH:
                    for y in range(-PROBE_RANGE,PROBE_RANGE):
                        if probe_temp.get_sector()[1]+y>=0 and probe_temp.get_sector()[1]+y<UNIVERSE_HEIGHT:
                            if check_grid[probe_temp.get_sector()[0]+x][probe_temp.get_sector()[1]+y]==False:
                                for p in grid[probe_temp.get_sector()[0]+x][probe_temp.get_sector()[1]+y]['probes']:
                                    if p.get_team()==probe_temp.get_team():
                                        if probe_check[probe_list.index(p)]==True:
                                            for i in range(len(probe_list)):
                                                if probe_check[i]==True:
                                                    if probe_list[i].get_net_id()==p.get_net_id():
                                                        probe_list[i].set_net_id(temp_id)
                                        else:
                                            probe_list_temp.append(p)
                                            if p!=probe_temp:
                                                probe_queue.append(p)
                                            #check_grid[p.get_sector()[0]][p.get_sector()[1]]=True
                                check_grid[probe_temp.get_sector()[0]+x][probe_temp.get_sector()[1]+y]=True
        for p in probe_list_temp:
            p.set_net_id(temp_id)
            probe_check[probe_list.index(p)]=True
        temp_id=temp_id+1



class Probe(object):
    def calc_sector(self):
        self.sector=(int(math.floor(self.pos[0])), int(math.floor(self.pos[1])))
    
    def __init__(self, pos, team, ai):
        self.pos = pos
        self.team = team
        self.ai = ai()
        self.landed=False
        self.cargo={'ressources':[0,0,0]}
        self.free_slots=CARGO_SLOTS
        self.act = self.ai.act
        self.calc_sector()
        self.network_id=None
    def get_team(self):
        return self.team

    def get_net_id(self):
        return self.network_id

    def set_net_id(self, net_id):
        self.network_id = net_id

    def scanned(self):
        return {'pos':self.pos, 'cargo':self.cargo, 'team_id':self.team.get_id()}

    def get_ai(self):
        return self.ai

    def set_pos(self, pos):
        self.pos = pos
        if self.pos[0]>UNIVERSE_WIDTH:
            self.pos[0]=UNIVERSE_WIDTH
        elif self.pos[0]<0:
            self.pos[0]=0
        if self.pos[1]>UNIVERSE_HEIGHT:
            self.pos[1]=UNIVERSE_HEIGHT
        elif self.pos[1]<0:
            self.pos[1]=0
        self.calc_sector()
    def get_pos(self):
        return self.pos

    def get_sector(self):
        return self.sector

    def pay_probe(self):
        res=self.cargo['ressources']
        res[0]=res[0]-PROBE_COST
        res[1]=res[1]-PROBE_COST
        res[2]=res[2]-PROBE_COST
        self.cargo['ressources']=res                
        
    def set_landed(self, landed):
        self.landed=landed
        
    def get_landed(self):
        return self.landed

    def get_free_slots(self):
        return self.free_slots

    def get_cargo(self):
        return self.cargo

    def add_ressources(self, res):
        for x in range(3):
            self.cargo['ressources'][x]=self.cargo['ressources'][x]+res[x]


class Team(object):
    def __init__(self, id_num, ai, colour):
        self.id_num=id_num
        self.ai=ai
        self.colour=colour

    def get_ai(self):
        return self.ai

    def get_colour(self):
        return self.colour
        
    def get_id(self):
        return self.id_num

class View(object):
    def __init__(self, probe, grid):
        self.pos=copy.deepcopy(probe.get_pos())
        self.cargo=copy.deepcopy(probe.get_cargo())
        self.free_slots=copy.deepcopy(probe.get_free_slots())
        self.team_id=copy.deepcopy(probe.get_team().get_id())
        self.landed=copy.deepcopy(probe.get_landed())
        self.sector=(int(math.floor(self.pos[0])),int(math.floor(self.pos[1])))
        self.scans = {'planets':[], 'probes':[]}
        for x in range(-2,2):
            if self.sector[0]+x>0 and self.sector[0]+x<UNIVERSE_WIDTH:
                for y in range(-2,2):
                    if self.sector[1]+y>0 and self.sector[1]+y<UNIVERSE_HEIGHT:
                        for planet in grid[self.sector[0]+x][self.sector[1]+y]['planets']:
                            self.scans['planets'].append(copy.deepcopy(planet.scanned()))
                        for probe in grid[self.sector[0]+x][self.sector[1]+y]['probes']:
                            self.scans['probes'].append(copy.deepcopy(probe.scanned()))

class Game(object):
    def __init__(self, ai_list):
        self.rounds=0
        self.ais= [ai[1].ProbeAi for ai in ai_list]
        #team colours
        self.team_colours=[]
        self.team_colours.append((255,0,0))
        self.team_colours.append((0,255,0))
        self.team_colours.append((0,0,255))
        self.team_colours.append((255,255,0))
        self.team_colours.append((255,0,255))
        self.team_colours.append((0,255,255))
        

        #create grid
        self.grid=[]
        for x in range(UNIVERSE_WIDTH):
            self.grid.append([])
            for y in range(UNIVERSE_HEIGHT):
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
        for x in range(PLANETS-1):
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
            #print (planet_temp.get_pos(), planet_temp.get_res())
        
        #set equal ressources for all homeworlds
        res_a = random.randint(10,RES_MAX)
        res_b = random.randint(10,RES_MAX)
        res_c = random.randint(10,RES_MAX)
        res=[res_a,res_b,res_c]
        for x in range(0,len(ai_list)):
            self.planet_list[x].set_res(res)    
            #print self.planet_list[x].get_res()

        self.team_list = []
        for x in range(0, len(ai_list)):
            self.team_list.append(Team(x, ai_list[x], self.team_colours[x]))

        #create initial probes
        self.probe_list = []
        for x in range(0, len(ai_list)):
            temp_probe=Probe([0,0], self.team_list[x], self.ais[x])
            self.probe_list.append(temp_probe)
            self.grid[self.planet_list[x].get_pos()[0]][self.planet_list[x].get_pos()[1]]['probes'].append(temp_probe)
            self.planet_list[x].populate(self.probe_list[x])
            self.probe_list[x].set_pos(copy.deepcopy(self.planet_list[x].get_pos()))
            self.probe_list[x].set_landed(True)

        #generate display
        self.mydisplay = Display(UNIVERSE_WIDTH, UNIVERSE_HEIGHT, SCALE)
        #self.mydisplay.new_draft()
        #self.draw_planets()
        #self.mydisplay.draw_draft()
                
    def tick(self):
        self.rounds=self.rounds+1
        print "round ", self.rounds
        
        #ressource mining
        for p in self.planet_list:
            if p.is_populated():
                p.populating_probe().add_ressources(p.get_res())
                
        #update networks
        #assign_networks(self.grid, self.probe_list)

        #create probe/view list
        view_list=[]
        for p in self.probe_list:
            view_list.append((p, View(p,self.grid)))
        

        #create action list
        action_list = []
        for (p,v) in view_list:
            action_list.append((p, p.act(v)))
            
        #print action_list[0][1].get_type(), action_list[0][1].get_data()
            
        
        #colonize planets
        for (p,act) in action_list:
            if act.get_type()==ACT_COLONIZE:
                #print "ALARM!!!"
                if len(self.grid[p.get_sector()[0]][p.get_sector()[1]]['planets'])==1:
                    if self.grid[p.get_sector()[0]][p.get_sector()[1]]['planets'][0].is_populated()==False:
                        self.grid[p.get_sector()[0]][p.get_sector()[1]]['planets'][0].populate(p)
                        p.set_pos=p.get_sector
                        p.set_landed(True)

        #build new probes
        for (p,act) in action_list:
            if act.get_type()==ACT_BUILD:
                if act.get_data()=='probe':
                    res=p.get_cargo()['ressources']
                    if res[0]>=PROBE_COST and res[1]>=PROBE_COST and res[2]>=PROBE_COST:
                        temp_probe=Probe(copy.deepcopy(p.get_pos()), p.get_team(), p.get_team().get_ai()[1].ProbeAi)
                        self.probe_list.append(temp_probe)
                        self.grid[p.get_pos()[0]][p.get_pos()[1]]['probes'].append(temp_probe)
                        #print self.grid
                        p.pay_probe()

        #move probes
        for (p,act) in action_list:
            if act.get_type()==ACT_MOVE:
                pos=p.get_pos()
                self.grid[int(math.floor(p.get_pos()[0]))][int(math.floor(p.get_pos()[1]))]['probes'].remove(p)
                betrag=math.sqrt(math.pow(act.get_data()[0],2)+math.pow(act.get_data()[1],2))
                if betrag>1:
                    pos[0]=pos[0]+act.get_data()[0]/betrag
                    pos[1]=pos[1]+act.get_data()[1]/betrag
                else:
                    pos[0]=pos[0]+act.get_data()[0]
                    pos[1]=pos[1]+act.get_data()[1]
                if pos[0]>=UNIVERSE_WIDTH-1:
                    pos[0]=UNIVERSE_WIDTH-1
                if pos[0]<0:
                    pos[0]=0
                if pos[1]>=UNIVERSE_HEIGHT-1:
                    pos[1]=UNIVERSE_HEIGHT-1
                if pos[1]<0:
                    pos[1]=0
               
                p.set_pos(pos)
                self.grid[int(math.floor(p.get_pos()[0]))][int(math.floor(p.get_pos()[1]))]['probes'].append(p)

        
        #update display
        self.mydisplay.update(self.planet_list, self.probe_list)
       
            
def get_ai(name):
    importlib.import_module(name)
    ai = sys.modules[name]
    ai.name = name
    return ai


def main():
     global ai_list
     ai_list = [(n, get_ai(n)) for n in sys.argv[1:]]
     
#background = pygame.Surface((UNIVERSE_WIDTH*SCALE,UNIVERSE_HEIGHT*SCALE))
#background.fill((0,0,0)

    #mydisplay.set_pixel(planet_list[x],(200,200,200))

#pygame.display.flip()

if __name__ == "__main__":
    main()
    mygame = Game(ai_list)

    while 1:
        mygame.tick()
