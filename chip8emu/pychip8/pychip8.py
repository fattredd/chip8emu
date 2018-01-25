#
# Chip8
#

import pyglet

class screen(object):
    ploy = pyglet.gl.GL_POLYGON
    self.windowScale = 1
    self.windowH = 32 * windowScale
    self.windowW = 64 * windowScale

    def __init__(self):
        self.window = pyglet.window.Window()
        self.window.set_minimum_size(windowW, windowH)

    def drawPixel(self, x, y):
        # pixelSize = self.windowScale
        pyglet.graphics.draw(4, poly, ('2vi',(
            x, y,
            x+1, y,
            x+1, y+1,
            x, y+1
            ))
        )


class Chip8(object):
    def __init__(self):
        self.memory = [0]*4096  # RAM
        self.V = [0]*16         # GP Reg
        self.I = 0           # Index Reg
        self.PC = 0             # Program Counter

        self.DelayT = 0
        self.SoundT = 0

        self.display = [False]* (windoW * windowH)

    def loadProgram(self,file):
        with open(file, 'rb') as game:
            for i, byte in enumerate(game):
                self.memory[i] = byte
        print("Loaded %s".format(file))

    def pa
