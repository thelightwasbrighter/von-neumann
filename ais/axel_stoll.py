N=__import__("von-neumann")
import math
import random

SECTORS=N.UNIVERSE_WIDTH*N.UNIVERSE_HEIGHT
CLOSE_LIMIT=10
TYP_MASTER, TYP_SCOUT, TYP_COLONIZER, TYP_COLONY = range(4)
MSG_SCOUT_DEATH, MSG_COLONIZER_DEATH, MSG_CREATION, MSG_MASTER, MSG_SCOUT_MISSION_ASSIGNMENT, MSG_SCOUT_REPORT, MSG_SCOUT_REQ_MISSION, MSG_COLONIZER_MISSION_ASSIGNMENT, MSG_COLONIZER_REQ_MISSION, MSG_COLONIZATION_COMPLETE, MSG_COLONY_REPORT, MSG_COLONY_DEATH= range(12)

def probe_buildable(view):
    for i in xrange(3):
        if view.cargo['resources'][i]<N.PROBE_COST:
            return False
    return True

def betrag(vect):
    return math.sqrt(math.pow(vect[0],2)+math.pow(vect[1],2))

def manhattan_distance(a,b):
    return abs(a[0]-b[0])+abs(a[1]-b[1])

def distance(a, b):
    vect=[0,0]
    if b[0]>a[0]:
        if b[0]-a[0]<N.UNIVERSE_WIDTH/2:
            vect[0]=b[0]-a[0]
        else:
            vect[0]=b[0]-a[0]-N.UNIVERSE_WIDTH
    else:
        if a[0]-b[0]<N.UNIVERSE_WIDTH/2:
            vect[0]=b[0]-a[0]
        else:
            vect[0]=b[0]-a[0]+N.UNIVERSE_WIDTH

    if b[1]>a[1]:
        if b[1]-a[1]<N.UNIVERSE_HEIGHT/2:
            vect[1]=b[1]-a[1]
        else:
            vect[1]=b[1]-a[1]-N.UNIVERSE_HEIGHT
    else:
        if a[1]-b[1]<N.UNIVERSE_HEIGHT/2:
            vect[1]=b[1]-a[1]
        else:
            vect[1]=b[1]-a[1]+N.UNIVERSE_HEIGHT
    return vect

def wrap_coordinates(coord):
    if coord[0]<0:
        x=coord[0]+N.UNIVERSE_WIDTH
    elif coord[0]>N.UNIVERSE_WIDTH-1:
        x=coord[0]-N.UNIVERSE_WIDTH
    else:
        x=coord[0]
        
    if coord[1]<0:
        y=coord[1]+N.UNIVERSE_HEIGHT
    elif coord[1]>N.UNIVERSE_HEIGHT-1:
        y=coord[1]-N.UNIVERSE_HEIGHT
    else:
        y=coord[1]
    
    return [x,y]
    
def close_unknown_points(start_point, known_map):
    close_unknown_points=[]
    for x in xrange(2*N.PROBE_SCAN_RANGE+1,2*CLOSE_LIMIT):
        for y in xrange(2*N.PROBE_SCAN_RANGE+1,2*CLOSE_LIMIT):
            for y_offset in (-y,y):
                for x_offset in xrange(-x,x+1):
                    coord=wrap_coordinates([start_point[0]+x_offset,start_point[1]+y_offset])
                    if known_map.get_known(coord)==False:
                        close_unknown_points.append(coord)
            for x_offset in (-x,x):
                for y_offset in xrange(-y,y+1):
                    coord=wrap_coordinates([start_point[0]+x_offset,start_point[1]+y_offset])
                    if known_map.get_known(coord)==False:
                        close_unknown_points.append(coord)
            if len(close_unknown_points)>0:
                random.shuffle(close_unknown_points)
                return close_unknown_points
    return close_unknown_points

def create_distance_queue(distance_map):
    temp_queue=[]
    for x in xrange(N.UNIVERSE_WIDTH):
        for y in xrange(N.UNIVERSE_HEIGHT):
            temp_queue.append(([x,y], distance_map.distance[x][y]))
    random.shuffle(temp_queue)
    temp_queue = sorted(temp_queue, key=lambda x: x[1])
    distance_queue=[]
    for i in xrange(len(temp_queue)):
        distance_queue.append(temp_queue[i][0])
    return distance_queue

class Planet(object):
    def __init__(self, pos, res, populated, team_id):
        self.pos=pos
        self.res=res
        self.populated=populated
        self.team_id=team_id
        

class PlanetMap(object):
    def __init__(self, view):
        self.planet_list=[]
        for p in view.scans['planets']:
            planet=Planet(p['pos'],p['res'],p['populated'],p['team_id'])
        self.planet_list.append(planet)
        
    def update_planet(self, planet):
        for p in self.planet_list:
            if p.pos==planet.pos:
              p.populated=planet.populated
              p.team_id=planet.team_id
              return None
        self.planet_list.append(planet)

    def empty_planets_by_distance(self, pos):
        pl_dis_list=[(p, betrag(distance(p.pos,pos))) for p in self.planet_list if p.populated==False]
        pl_dis_sorted=sorted(pl_dis_list, key=lambda x:x[1])
        return pl_dis_sorted
            
    def planet_known(self, pos):
        for p in self.planet_list:
            if p.pos==pos:
                return True
        return False
    
    def get_planet(self, pos):
        for p in self.planet_list:
            if p.pos==pos:
                return p
    

class DistanceMap(object):
    def __init__(self, view):
        self.distance = [[betrag(distance(view.sector, [x,y])) for y in xrange(N.UNIVERSE_HEIGHT)] for x in xrange(N.UNIVERSE_WIDTH)]
        

class KnownMap(object):
    def __init__(self, view):
        self.known = [[False for y in xrange(N.UNIVERSE_HEIGHT)] for x in xrange(N.UNIVERSE_WIDTH)]
        self.deep_known = [[False for y in xrange(N.UNIVERSE_HEIGHT)] for x in xrange(N.UNIVERSE_WIDTH)]
        self.know_scan_area(view.sector)
        
    def get_known(self, pos):
        return self.known[pos[0]][pos[1]]
        
    def know_scan_area(self, pos):
        if self.deep_known[pos[0]][pos[1]]==False:
            self.deep_known[pos[0]][pos[1]]=True
            for x in xrange(-N.PROBE_SCAN_RANGE+pos[0], N.PROBE_SCAN_RANGE+1+pos[0]):
                for y  in xrange(-N.PROBE_SCAN_RANGE+pos[1], N.PROBE_SCAN_RANGE+1+pos[1]):
                    coord=wrap_coordinates([x,y])
                    self.known[coord[0]][coord[1]]=True

class Message(object):
    def __init__(self, sender_id=None, receiver_id=None, content=None, message_type=None, death_message=False):
        #self.sender_view=view
        self.receiver_id=receiver_id
        self.content=content
        self.sender_id=sender_id
        self.message_type=message_type
        

class ColonizationMission(object):
    def __init__(self, probe_id, target_pos):
        self.probe_id=probe_id
        self.target_pos=target_pos

class ColonizationTable(object):
    def __init__(self):
        self.colonization_list=[]
    
    def add_mission(self, mission):
        self.colonization_list.append(mission)
        
    def remove_mission_by_id(self, probe_id):
        for m in self.colonization_list:
            if m.probe_id==probe_id:
                self.colonization_list.remove(m)
                break
    
    def mission_to_target_exists(self, target):
        for m in self.colonization_list:
            if m.target_pos==target:
                return True
        return False
    
    def get_redundant_missions(self, planet_map):
        redundant_list=[]
        for m in self.colonization_list:
            if planet_map.get_planet(m.target_pos).populated:
                redundant_list.append(m)
        return redundant_list


class Colony(object):
    def __init__(self, probe_id, pos, planet_res, cargo):
        self.probe_id=probe_id
        self.pos=pos
        self.planet_res=planet_res
        self.cargo=cargo

class ColonyTable(object):
    def __init__(self):
        self.colony_list=[]

    def add_colony(self, colony):
        self.colony_list.append(colony)

    def remove_colony(self, pos):
        for c in self.colony_list:
            if c.pos==pos:
                self.colony_list.remove(c)
                break

    def update_colonies(self, messages):
        for m in messages:
            if m.message_type==MSG_COLONY_REPORT:
                for i in xrange(len(self.colony_list)):
                    if self.colony_list[i].pos==m.content['sector']:
                        self.colony_list[i].probe_id=m.sender_id
                        self.colony_list[i].cargo=m.content['cargo']
                        break


class ScoutingMission(object):
    def __init__(self, probe_id, target_pos):
        self.probe_id=probe_id
        self.target_pos=target_pos

class ScoutingTable(object):
    def __init__(self):
        self.scouting_list=[]

    def add_mission(self, mission):
        self.scouting_list.append(mission)

    def remove_mission_by_id(self, probe_id):
        for m in self.scouting_list:
            if m.probe_id==probe_id:
                self.scouting_list.remove(m)
                break
                
    def mission_to_target_exists(self, target):
        for m in self.scouting_list:
            if m.target_pos==target:
                return True
        return False
    
    def get_redundant_missions(self, known_map):
        redundant_list=[]
        for m in self.scouting_list:
            if known_map.get_known(m.target_pos):
                redundant_list.append(m)
        return redundant_list

class ProbeAi(object):
    
    def __init__(self, cargs):
        self.typ=None
        self.initial=False
        if cargs=='initial':
            self.typ=TYP_MASTER
            self.int_id=0
            self.id_counter=1
            self.scouting_table=ScoutingTable()
            self.colonization_table=ColonizationTable()
            self.initial=True
            self.scout_count=0
            self.colonizer_count=0
            self.colony_table=ColonyTable()
        else:
            self.int_id=cargs.receiver_id
            self.typ=cargs.content
            self.mission=None
    
    def master_build_colonizer(self):
        if probe_buildable(self.view):
            closest_empty_planets=self.planet_map.empty_planets_by_distance(self.view.pos)
            for (p,dis) in closest_empty_planets:
                if self.colonization_table.mission_to_target_exists(p.pos)==False:
                    
                    colonization_mission=ColonizationMission(self.id_counter, p.pos)
                    self.colonization_table.add_mission(colonization_mission)
 
                    create_message=Message()
                    create_message.sender_id=self.int_id
                    create_message.receiver_id=self.id_counter
                    create_message.message_type=MSG_CREATION
                    create_message.content=TYP_COLONIZER
                    
                    message=Message()
                    message.sender_id=self.int_id
                    message.receiver_id=self.id_counter
                    message.message_type=MSG_COLONIZER_MISSION_ASSIGNMENT
                    message.content=colonization_mission
                    
                    self.master_message.content.append(message)
                    self.colonizer_count+=1
                    self.id_counter+=1
                    return {'action':N.Action(N.ACT_BUILD_PROBE, create_message), 'message':self.master_message} 
                    
        return {'action':N.Action(N.ACT_IDLE), 'message':self.master_message}

        
    def master_build_scout(self):
        if probe_buildable(self.view):
            for pos in self.distance_queue:
                if self.known_map.get_known(pos)==False and self.scouting_table.mission_to_target_exists(pos)==False:
                    
                    scout_mission=ScoutingMission(self.id_counter, pos)
                    self.scouting_table.add_mission(scout_mission)
                    
                    create_message=Message()
                    create_message.sender_id=self.int_id
                    create_message.receiver_id=self.id_counter
                    create_message.message_type=MSG_CREATION
                    create_message.content=TYP_SCOUT
                    
                    message=Message()
                    message.sender_id=self.int_id
                    message.receiver_id=self.id_counter
                    message.message_type=MSG_SCOUT_MISSION_ASSIGNMENT
                    message.content=scout_mission
                    
                    self.master_message.content.append(message)
                    self.scout_count+=1
                    self.id_counter+=1
                    return {'action':N.Action(N.ACT_BUILD_PROBE, create_message), 'message':self.master_message} 
                    
        return {'action':N.Action(N.ACT_IDLE), 'message':self.master_message}


    def scout_move_to_target(self, message):
        return {'action': N.Action(N.ACT_MOVE, distance(self.view.pos, self.mission.target_pos)), 'message':message}
    
    def update_known_map(self, message):
        self.known_map.know_scan_area(message.content['sector'])

    def assign_scout_mission(self, message):
        point_found=False
        best_dist=SECTORS
        for pos in close_unknown_points(message.content['sector'], self.known_map):
            temp_dist = self.distance_queue.index(pos)
            if temp_dist < best_dist:
                if self.scouting_table.mission_to_target_exists(self.distance_queue[temp_dist])==False:
                    best_dist = temp_dist
                    point_found=True
        if point_found:
            mission=ScoutingMission(message.sender_id, self.distance_queue[best_dist])
            self.scouting_table.remove_mission_by_id(message.sender_id)
            self.scouting_table.add_mission(mission)
            m=Message()
            m.sender_id=self.int_id
            m.receiver_id=message.sender_id
            m.message_type=MSG_SCOUT_MISSION_ASSIGNMENT
            m.content=mission
            self.master_message.content.append(m)
    
    def assign_colonization_mission(self, message):
        closest_empty_planets=self.planet_map.empty_planets_by_distance(message.content['sector'])
        for (p,dis) in closest_empty_planets:
                if self.colonization_table.mission_to_target_exists(p.pos)==False:
                    mission=ColonizationMission(message.sender_id, p.pos)
                    self.colonization_table.remove_mission_by_id(message.sender_id)
                    self.colonization_table.add_mission(mission)
                    m=Message()
                    m.sender_id=self.int_id
                    m.receiver_id=message.sender_id
                    m.message_type=MSG_COLONIZER_MISSION_ASSIGNMENT
                    m.content=mission
                    self.master_message.content.append(m)
                    break
            
        
    def act_master(self):
        if self.initial:
            self.known_map=KnownMap(self.view)
            self.distance_map=DistanceMap(self.view)
            self.distance_queue=create_distance_queue(self.distance_map)
            self.initial=False
            self.planet_map=PlanetMap(self.view)
        self.master_message=Message()
        self.master_message.sender_id=self.int_id
        self.master_message.content=[]
        self.master_message.message_type=MSG_MASTER
        self.planet_map.empty_planets_by_distance(self.view.pos)

        if self.view.team_id==0:
            print len(self.colony_table.colony_list)
        
        #update_colonies
        self.colony_table.update_colonies(self.view.messages)
        
        #update planets
        for p in self.view.scans['planets']:
            planet=Planet(p['pos'],p['res'],p['populated'],p['team_id'])
            self.planet_map.update_planet(planet)

        ####handle incoming messages
        for m in self.view.messages:
            if m.message_type!=MSG_MASTER:
                #update planets
                for p in m.content['scans']['planets']:
                    planet=Planet(p['pos'],p['res'],p['populated'],p['team_id'])
                    self.planet_map.update_planet(planet)
            if m.message_type==MSG_SCOUT_REPORT or m.message_type==MSG_SCOUT_REQ_MISSION:
                #update known map
                self.update_known_map(m)
            if m.message_type==MSG_SCOUT_REQ_MISSION:
                #assign scout mission
                self.assign_scout_mission(m)
            if m.message_type==MSG_COLONIZER_REQ_MISSION:
                #assign scout mission
                self.assign_colonization_mission(m)
            if m.message_type==MSG_SCOUT_DEATH:
                #delete scouting mission
                self.scout_count-=1
                self.scouting_table.remove_mission_by_id(m.sender_id)
            if m.message_type==MSG_COLONIZER_DEATH:
                #delete scouting mission
                self.colonizer_count-=1
                self.colonization_table.remove_mission_by_id(m.sender_id)
            if m.message_type==MSG_COLONIZATION_COMPLETE:
                self.colonization_table.remove_mission_by_id(m.sender_id)
                for pl in m.content['scans']['planets']:
                    if pl['sector']==m.content['sector']:
                        planet_res=pl['res']
                self.colony_table.add_colony(Colony(m.sender_id, m.content['sector'], planet_res, m.content['cargo']))
            if m.message_type==MSG_COLONY_DEATH:
                self.colony_table.remove_colony(m.content['sector'])
                
        #eliminate redundant scouting missions
        redundant_missions=self.scouting_table.get_redundant_missions(self.known_map)
        for mi in redundant_missions:
            #get scout position
            scout_sector=None
            #self.scouting_table.remove_mission_by_id(mi.probe_id)
            for mes in self.view.messages:
                if mes.sender_id==mi.probe_id:
                    scout_sector=mes.content['sector']
                    break
            dummy_message=Message()
            dummy_message.sender_id=mi.probe_id
            if scout_sector==None:
                scout_sector=self.view.sector
                dummy_message.sender_id=self.id_counter-1
            dummy_message.message_type=MSG_SCOUT_REQ_MISSION
            dummy_message.content={'sector':scout_sector, 'scans':self.view.scans}
            self.assign_scout_mission(dummy_message)
        
        #eliminate redundant colonization missions
        redundant_missions=self.colonization_table.get_redundant_missions(self.planet_map)
        for mi in redundant_missions:
            #get position
            colonizer_sector=None
            for mes in self.view.messages:
                if mes.sender_id==mi.probe_id:
                    colonizer_sector=mes.content['sector']
                    break
            dummy_message=Message()
            dummy_message.sender_id=mi.probe_id
            if colonizer_sector==None:
                colonizer_sector=self.view.sector
                dummy_message.sender_id=self.id_counter-1
            dummy_message.message_type=MSG_COLONIZER_REQ_MISSION
            dummy_message.content={'sector':colonizer_sector, 'scans':self.view.scans}
            self.assign_colonization_mission(dummy_message)
        
    
        if self.scout_count<3:
            return self.master_build_scout()
        
        return self.master_build_colonizer()
            
        return {'action':N.Action(N.ACT_IDLE), 'message':self.master_message}

        
    def act_scout(self):
        message=Message()
        message.sender_id=self.int_id
        message.content={'sector':self.view.sector, 'scans':self.view.scans}
        #handle messages
        for m in self.view.messages:
             if m.message_type==MSG_MASTER:
                 for mm in m.content:
                    if mm.receiver_id==self.int_id and mm.message_type==MSG_SCOUT_MISSION_ASSIGNMENT:
                        self.mission=mm.content
        
        if self.mission==None or self.view.sector==self.mission.target_pos :
            message.message_type=MSG_SCOUT_REQ_MISSION
            self.mission=None
            return {'action':N.Action(N.ACT_IDLE), 'message':message}
            #return {'action':N.Action(N.ACT_MOVE, [random.randint(-5,5),random.randint(-5,5)]), 'message':message}
        else:
            message.message_type=MSG_SCOUT_REPORT
            return self.scout_move_to_target(message)
    
    def act_colonizer(self):
        message=Message()
        message.sender_id=self.int_id
        message.content={'sector':self.view.sector, 'scans':self.view.scans, 'cargo':self.view.cargo}
        #handle messages
        for m in self.view.messages:
             if m.message_type==MSG_MASTER:
                 for mm in m.content:
                    if mm.receiver_id==self.int_id and mm.message_type==MSG_COLONIZER_MISSION_ASSIGNMENT:
                        self.mission=mm.content
        
        if self.view.landed:
            self.typ=TYP_COLONY
            message.message_type=MSG_COLONIZATION_COMPLETE
            return {'action':N.Action(N.ACT_COLONIZE), 'message':message}

        if self.view.sector==self.mission.target_pos:
            message.message_type=MSG_SCOUT_REPORT
            return {'action':N.Action(N.ACT_COLONIZE), 'message':message}

        if self.mission==None:
            message.message_type=MSG_COLONIZER_REQ_MISSION
            return {'action':N.Action(N.ACT_IDLE), 'message':message}
            #return {'action':N.Action(N.ACT_MOVE, [random.randint(-5,5),random.randint(-5,5)]), 'message':message}
        else:
            message.message_type=MSG_SCOUT_REPORT
            return self.scout_move_to_target(message)
                            
    def act_colony(self):
        message=Message()
        message.sender_id=self.int_id
        message.message_type=MSG_COLONY_REPORT
        for p in self.view.scans['planets']:
            if p['sector']==self.view.sector:
                planet_res=p['res']
                break
        message.content={'sector':self.view.sector, 'planet_res':planet_res, 'cargo':self.view.cargo, 'scans':self.view.scans}
        return {'action':N.Action(N.ACT_IDLE), 'message':message}
       

    def act(self, view):
        self.view=view
        if self.typ==TYP_MASTER:
            return self.act_master()
        elif self.typ==TYP_SCOUT:
            return self.act_scout()
        elif self.typ==TYP_COLONIZER:
            return self.act_colonizer()
        elif self.typ==TYP_COLONY:
            return self.act_colony()

    def death_message(self, view):
        message=Message()
        message.sender_id=self.int_id
        if self.typ==TYP_SCOUT:
            message.message_type=MSG_SCOUT_DEATH
            message.content={'sector': self.view.sector, 'scans':self.view.scans}
            return message
        if self.typ==TYP_COLONIZER:
            message.message_type=MSG_COLONIZER_DEATH
            message.content={'sector': self.view.sector, 'scans':self.view.scans}
            return message
        if self.typ==TYP_COLONY:
            message.message_type=MSG_COLONY_DEATH
            message.content={'sector': self.view.sector, 'scans':self.view.scans}
            return message
        else:
            return None
