## A little animation of a population evolving on a simple fitness landscape.
##
## There is an object for an organism, an abstract entity with a point
## in space and some offspring.  And another object for a population
## of such entities.
import bpy
from bpy import context
import random
import sys
import time

## This is a global variable.
population = []

class organism(object):
    """
    A class that defines an organism in our abstract space.  The
    fitness landscape is a mesh called 'fitnessLandscape'.
    """

    def __init__(self, x, y, parentLoc=(0,0,0), key=0):
        """
        Creates a new organism at (x,y) with z determined by raycasting
        a vertical line onto the fitness landscape. The parent location
        is also specified, and the frame number of the 'birth' event, so
        the process can be animated.
        """
        self.fitness = 0
        self.fitstep = 0.1
        self.radius = 0.02
        landscape = bpy.data.objects['fitnessLandscape']
        res = landscape.ray_cast((x,y,1000.0),(0,0,-1))
        if res[0]:
            # We have the intersection location in mesh 
            # coordinates. xform to world coordinates.
            self.location = landscape.matrix_world @ res[1]
        else:
            sys.exit("point is not over fitnessLandscape")
            
        self.x = self.location.x
        self.y = self.location.y
        self.fitness = self.location.z 
        
        if parentLoc == (0,0,0):
            startLoc = self.location
        else:
            startLoc = parentLoc
        
        bpy.ops.mesh.primitive_ico_sphere_add(location=startLoc, radius=self.radius)
        self.obj = bpy.context.object
        self.obj.active_material = bpy.data.materials.get("orgMaterial")
        self.reproduced = False
        
        if key != 0:
            self.obj.keyframe_insert(data_path="location", frame=key)
            # Move the object, set another key frame.
            self.obj.location = self.location
            self.obj.keyframe_insert(data_path="location", frame=key+10)
        
    def reproduce(self, N, key=0):
        """
        Produces N children somewhere nearby on the fitness landscape.
        """
        out = []
        for i in range(N):
            newX = self.x + random.gauss(0, self.fitstep)
            newY = self.y + random.gauss(0, self.fitstep)
            
            out.append(organism(newX, newY))

        self.reproduced = True
        return out

    def die(self, key=0):
        bpy.data.objects.remove(bpy.data.objects[self.obj.name])
        

class pop(object):
    """
    Models a population of organisms.
    """
    def __init__(self, N, key=0):
        self.population = [organism(random.gauss(0, 0.1), random.gauss(0,0.1)) for i in range(N)]

        self.population.sort(key=lambda ob: ob.fitness)


    def reproduce(self, N, key=0):
        """
        We welcome a new generation.
        """
        young = []
        for p in self.population:
            young.extend(p.reproduce(2))

        self.population.extend(young)

    def retire(self, key=0):
        """
        The organisms that have reproduced can fade away.
        """
        ## We retire them backward so we can just use pop() to remove.
        for i in range(len(self.population)-1,-1,-1):
            if self.population[i].reproduced:
                self.population[i].die()
                self.population.pop(i)
                
    def select(self, fraction, key=0):
        """
        Selects away a given fraction of the population.
        """
        if 0 <= fraction <= 1:
            Nselected = int(fraction * len(self.population))
            for i in range(Nselected):
                self.population[1].die()
                self.population.pop(1)
        else:
            sys.exit("must select away a positive fraction.")


    def print(self):
        print(self.population)
        



population = pop(3, key=20)

population.print()

population.reproduce(2, key=70)

population.print()

population.retire(key=120)

population.print()

population.select(0.5, key=170)

population.print()

#time.sleep(5)

#for i in range(5):
#    population[i].die()

