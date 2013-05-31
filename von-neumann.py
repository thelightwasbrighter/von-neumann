#!/usr/bin/env python2

#import ConfigParser
import random
import sys
import time

#import numpy
import pygame, pygame.locals


UNIVERSE_WIDTH = 400
UNIVERSE_HEIGHT = 300
PLANETS = 50
SCALE = 2
RES_MAX = 100


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
        self.black = 0,0,0
        self.width, self.height = width, height
        self.scale = scale
        self.size = (self.width*scale , self.height*scale)
        pygame.init()
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption("vo Neumann")

        self.text = []

    def set_frame(self, surface):
        self.screen.blit(surface, (0,0))
        pygame.display.flip()


class Planet(object):
    def __init__(self, pos, ressource):
        self.pos=pos
        self.ressource=ressource
        self.populated=0
        self.probe=None

    def populate(probe):
        self.probe=probe
        self.populated=1
    
    def unpopulate(self):
        self.populated=0

    def get_pos(self):
        return self.pos

    def get_res(self):
        return self.ressource

    def set_res(self, res):
        self.res=res



class Game(object):
    def __init__(self):
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
        planet_temp = Planet((xtemp,ytemp), res)
        self.planet_list.append(planet_temp)
        for x in range(PLANETS-1):
            while sum(1 for i in self.planet_list if i.get_pos()==(xtemp,ytemp))!=0:
                xtemp = random.randint(0,UNIVERSE_WIDTH-1)
                ytemp = random.randint(0,UNIVERSE_HEIGHT-1)
            
            res_a = random.randint(0,RES_MAX)
            res_b = random.randint(0,RES_MAX)
            if res_b+res_a>RES_MAX:
                res_b=RES_MAX-res_a
            res=[res_a,res_b,0]
            random.shuffle(res)
            planet_temp = Planet((xtemp,ytemp), res)

            self.planet_list.append(planet_temp)
            print (planet_temp.get_pos(), planet_temp.get_res())
        





#background = pygame.Surface((UNIVERSE_WIDTH*SCALE,UNIVERSE_HEIGHT*SCALE))
#background.fill((0,0,0)


#mydisplay = Display(UNIVERSE_WIDTH, UNIVERSE_HEIGHT, SCALE)

#planet_map = MapLayer(UNIVERSE_WIDTH, UNIVERSE_HEIGHT, 0)
#for x in range(PLANETS):
 #   planet_map.set(planet_list[x][0],planet_list[x][1],1)
 #   mydisplay.set_pixel(planet_list[x],(200,200,200))

#pygame.display.flip()

mygame = Game()

#while 1:
#    pass
