## A little animation of a population evolving on a simple fitness landscape.
##
## There is an object for an organism, an abstract entity with a point
## in space and some offspring.  And another object for a population
## of such entities.
import bpy
from bpy import context
from mathutils import Vector
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

    def __init__(self, x, y, parentLoc=(0,0,0), key=0, duration=20):
        """
        Creates a new organism at (x,y) with z determined by raycasting
        a vertical line onto the fitness landscape. The parent location
        is also specified, and the frame number of the 'birth' event, so
        the process can be animated.  The duration is the number of 
        frames the birth and move are to take.
        """
        self.fitness = 0
        self.fitstep = 0.025
        self.radius = 0.005
        landscape = bpy.data.objects['fitnessLandscape']
        sourcePoint = landscape.matrix_world.inverted() @ Vector((x, y, 1000.0))
        
        (hit, hitLoc, norm, index) = landscape.ray_cast(sourcePoint,
                                                        (0,0,-1))
        if hit:
            # We have the intersection location in mesh 
            # coordinates. xform to world coordinates.
            self.location = landscape.matrix_world @ hitLoc
        else:
            sys.exit("point is not over fitnessLandscape")
            
        self.x = self.location.x
        self.y = self.location.y
        self.fitness = self.location.z 
        
        if parentLoc == (0,0,0):
            startLoc = self.location
        else:
            startLoc = parentLoc
                    
        bpy.ops.mesh.primitive_ico_sphere_add(location=startLoc, 
                                              radius=self.radius)
        self.obj = bpy.context.object
        self.obj.active_material = bpy.data.materials.get("orgMaterial")
        self.reproduced = False
        
        if key != 0:
            # Start hidden.
            bpy.context.scene.frame_set(1)
            self.obj.hide_render = True
            self.obj.keyframe_insert(data_path="hide_render", 
                                     frame=1, index=-1)
                           
            bpy.context.scene.frame_set(key)
            self.obj.hide_render = False
            self.obj.keyframe_insert(data_path="location", 
                                     frame=key, index=-1)
            self.obj.keyframe_insert(data_path="hide_render", 
                                     frame=key, index=-1)
            
            # Move the object to the halfway point, set another key frame.
            midpoint = ((self.x + parentLoc[0])/2.0, 
                        (self.y + parentLoc[1])/2.0,
                        0.1 + (self.fitness + parentLoc[2])/2.0)
            newFrame = key + int(duration/2.0)
            bpy.context.scene.frame_set(newFrame)
            self.obj.location = midpoint
            self.obj.keyframe_insert(data_path="location", 
                                     frame=newFrame)
            
            # Move the object to its final point, set another key frame.
            newFrame = key + duration
            bpy.context.scene.frame_set(newFrame)
            self.obj.location = self.location
            self.obj.keyframe_insert(data_path="location", 
                                     frame=newFrame, index=-1)
        
    def reproduce(self, N, key=0, duration=20):
        """
        Produces N children somewhere nearby on the fitness landscape.
        """
        out = []
        for i in range(N):
            newX = self.x + random.gauss(0, self.fitstep)
            newY = self.y + random.gauss(0, self.fitstep)
            
            out.append(organism(newX, newY, parentLoc=self.location,
                       key=key, duration=duration))

        self.reproduced = True
        return out

    def die(self, key=0):
        """
        In this world, organisms never die, they just disappear.
        """
        if key == 0:
            self.obj.hide_render = True
        else:
            bpy.context.scene.frame_set(key)
            self.obj.hide_render = True
            self.obj.keyframe_insert(data_path="hide_render",
                                     frame=key, index=-1)        

class pop(object):
    """
    Models a population of organisms.
    """
    def __init__(self, N, key=0):
               
        # Create a population group object and also an instance of it.
        if "population" in bpy.data.collections: 
            self.popObj = bpy.data.collections["population"]
        else:
            self.popObj = bpy.data.collections.new("population")

        parent = bpy.data.objects["fitnessLandscape"].users_collection[0]
        parent.children.link(self.popObj) # Add the new collection under a parent

        # There is also a list of the organism objects in the population.
        self.population = []

        for i in range(N):
            o = organism(random.gauss(0, 0.05), random.gauss(0,0.05), 
                         parentLoc=(0,0,0.0765), key=key, duration=20) 
            
            # Move new organisms into the population collection.
            oldCollection = o.obj.users_collection[0]
            self.popObj.objects.link(o.obj) 
            oldCollection.objects.unlink(o.obj) 
            
            self.population.append(o)

        # Sort to put the least fit at the front.
        self.population.sort(key=lambda ob: ob.fitness)
  
    def reproduce(self, N, key=0, duration=20):
        """
        We welcome a new generation.
        """
        young = []
        for organism in self.population:
            orgList = organism.reproduce(N, key=key, duration=duration)
            
            # Move new organisms into the population collection.
            for o in orgList:
                oldCollection = o.obj.users_collection[0]
                self.popObj.objects.link(o.obj) 
                oldCollection.objects.unlink(o.obj) 

            young.extend(orgList)

        # Incorporate the new young'uns into the population.
        self.population.extend(young)

        # Sort to keep the least fit near the front of the line.
        self.population.sort(key=lambda ob: ob.fitness)

    def retire(self, key=0):
        """
        The organisms that have reproduced can fade away.
        """
        ## We retire them backward so we can just use pop() to remove.
        for i in range(len(self.population)-1,-1,-1):
            if self.population[i].reproduced:
                self.population[i].die(key=key)
                self.population.pop(i)
                
    def select(self, fraction, key=0):
        """
        Selects away a given fraction of the population.
        """
        if 0 <= fraction <= 1:
            Nselected = int(fraction * len(self.population))
            for i in range(Nselected):
                self.population[1].die(key=key)
                self.population.pop(1)
        else:
            sys.exit("must select away a positive fraction.")


    def print(self):
        for p in self.population:
            print(p.x, p.y, p.obj.location)
        

#o = organism(0.1,0.1, parentLoc=(0,0,0.0765), key=10)

#o.reproduce(3, key=40, duration=20)


population = pop(30, key=5)

kframe = 30
for i in range(4):
    print("Starting step", i)
    population.reproduce(5, key=kframe)
    population.retire(key=kframe+5)
    population.select(0.8, key=kframe+25)
    population.print()
    kframe += 30


