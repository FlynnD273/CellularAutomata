import math
import random
import pyglet
import re
from pyglet.window import mouse
from pyglet.window import key
import time
from threading import Timer

width = 200
height = 200
zoneCount = 10
probability = 0.1
fps = 30
isPlaying = False

window = pyglet.window.Window(600, 600)
batch = pyglet.graphics.Batch()
cells = []
zones = []

class Zone:
    def __init__ (self, rect, isActive):
        self._isActive = False
        self.rect = rect
        self.isActive = isActive
    
    @property
    def isActive (self):
        return self._isActive
    
    @isActive.setter
    def isActive (self, value):
        if self.isActive == value:
            return
        
        self._isActive = value

        if self.rect is None:
            return
        
        if value:
            self.rect.color = (255, 255, 255, 50)
        else:
            self.rect.color = (255, 255, 255, 0)

class Cell:
    def __init__ (self, rect, isAlive, zones, b, s, color = (255, 255, 255, 255)):
        self._born = b
        self._survive = s
        self._zones = zones
        self._rect = rect
        self._color = color
        self.isAlive = isAlive

    def __init__ (self, rect, isAlive, zones, rule, color = (255, 255, 255, 255)):
        rules = rule.split("/")
        b = []
        for c in re.sub(r'[^0-9]', '', rules[0]):
            b.append(int(c))
        s = []
        for c in re.sub(r'[^0-9]', '', rules[1]):
            s.append(int(c))
        
        self._born = b
        self._survive = s
        self._zones = zones
        self._rect = rect
        self._color = color
        self.isAlive = isAlive
    
    @property
    def born(self):
        return self._born
    
    @property
    def survive(self):
        return self._survive

    @property
    def color(self):
        return self._color
    
    @color.setter
    def color (self, value):
        self._color = value
        self._updateCellColor()

    @property
    def rect (self):
        return self._rect

    @property
    def zones (self):
        return self._zones
    
    @property
    def isAlive (self):
        return self._isAlive
    
    @isAlive.setter
    def isAlive (self, value):
        global zones
        self._isAlive = value

        for i in self.zones:
            zones[i].isActive = True
        
        self._updateCellColor()

    def _updateCellColor (self):
        if self.isAlive:
            self.rect.color = self.color
        else:
            self.rect.color = ( self.color[0], self.color[1], self.color[2], 0)


def getIndex (x, y):
    return y * width + x

def getPos (i):
     return (i % width, math.floor(i / width))

def getCellState (x, y):
    if x < 0 or x >= width or y < 0 or y >= height:
        return False
    
    return cells[getIndex(x, y)].isAlive

def getNeighbourCount (x, y):
    neighbours = 0
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            if dx == 0 and dy == 0:
                continue

            if getCellState(x + dx, y + dy):
                neighbours += 1
    
    return neighbours

def getZones (x, y):
    zoneWidth = width / zoneCount
    zoneHeight = height / zoneCount
    zoneX = math.floor(x / zoneWidth)
    zoneY = math.floor(y / zoneHeight)
    z = [ zoneX + zoneY * zoneCount ]

    zx = 0
    if x % zoneWidth >= zoneWidth - 1 and  zoneX < zoneCount - 1:
        z.append(zoneX + 1 + zoneY * zoneCount)
        zx = 1
    elif x % zoneWidth < 1 and zoneX > 0:
        z.append(zoneX - 1 + zoneY * zoneCount)
        zx = -1
    
    zy = 0
    if y % zoneHeight >= zoneHeight - 1 and zoneY < zoneCount - 1:
        z.append(zoneX + (zoneY + 1) * zoneCount)
        zy = 1
    elif y % zoneHeight < 1 and zoneY > 0:
        z.append(zoneX + (zoneY - 1) * zoneCount)
        zy = - 1

    if zx and zy:
        z.append(zoneX + zx + (zoneY + zy) * zoneCount)
    
    return z


def initCells ():
    global zones, cells
    zones = []
    cells = []
    cellW = window.width / width
    cellH = window.height / height

    zoneW = window.width / zoneCount
    zoneH = window.height / zoneCount

    for i in range(zoneCount * zoneCount):
        zoneX = i % zoneCount
        zoneY = int(i / zoneCount)
        zoneX *= zoneW
        zoneY *= zoneH

        # rect = pyglet.shapes.Rectangle(zoneX, zoneY, zoneW, zoneH, (255, 255, 255, 255), batch)
        zones.append(Zone(None, True))

    for y in range(height):
        for x in range(width):
            rect = pyglet.shapes.Rectangle(x * cellW, y * cellH, cellW, cellH, (255, 255, 255, 255), batch)
            z = getZones(x, y)
            color = (255, 255, 255, 255)
            rule = "B3/S23"
            if y > height / 2:
                if x > width / 2:
                    rule = "B3456/S3"
                    color = (255, 255, 0, 255)
                else:
                    rule = "B36/S24"
                    color = (255, 0, 255, 255)
            else:
                if x > width / 2:
                    rule = "B3/S0123456"
                    color = (0, 255, 255, 255)
            # if len(z) > 2:
            #     color = (255, 255, 0, 255)
            # elif len(z) > 1:
            #     color = (255, 0, 0, 255)

            cells.append(Cell(rect, random.random() < probability, z, rule, color))

# TODO: change this to use a rule stored per cell
def getNextState (cell, neighbours):
    if cell.isAlive:
        return neighbours in cell.survive
    else:
        return neighbours in cell.born

def nextFrame ():
    global zones
    zoneWidth = int(width / zoneCount)
    zoneHeight = int(height / zoneCount)

    newCellStates = []
    for zoneIndex, z in enumerate(zones):
        if not z.isActive:
            continue
        zoneX = zoneIndex % zoneCount
        zoneY = int(zoneIndex / zoneCount)

        for y in range(zoneY * zoneHeight, (zoneY + 1) * zoneHeight):
            for x in range(zoneX * zoneWidth, (zoneX + 1) * zoneWidth):
                i = getIndex(x, y)
                neighbours = getNeighbourCount(x, y)
                nextState = getNextState(cells[i], neighbours)
                if cells[i].isAlive != nextState:
                    newCellStates.append({ "index":i, "state":nextState })
    
    for i in range(len(zones)):
        zones[i].isActive = False
    for state in newCellStates:
        index = state["index"]
        cells[index].isAlive = state["state"]

@window.event
def on_mouse_press (x, y, button, modifiers):
    global isPlaying

    if button == mouse.LEFT:
        i = getIndex(math.floor(x / window.width * width), math.floor(y / window.height * height))
        cells[i].isAlive = not cells[i].isAlive
    elif button == mouse.RIGHT:
        nextFrame()
        isPlaying = False

@window.event
def on_key_press (symbol, modifiers):
    global isPlaying
    if symbol == key.SPACE:
        isPlaying = not isPlaying

# animTimer = Timer(1,nextFrame)


@window.event
def on_draw ():
    window.clear()
    batch.draw()

def frame (dt):
    if isPlaying:
        nextFrame()

# animTimer.start()

initCells()

pyglet.clock.schedule_interval(frame, 1/fps)
pyglet.app.run()