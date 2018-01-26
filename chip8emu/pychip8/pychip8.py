#
# Chip8
#

import pyglet

windowScale = 1
windowH = 32 * windowScale
windowW = 64 * windowScale

class screen(object):
    poly = pyglet.gl.GL_POLYGON

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
        self.I = 0              # Index Reg
        self.PC = 0x200         # Program Counter

        self.DelayT = 0         # Delay Timer
        self.SoundT = 0         # Sound Timer

        self.Stack = [0]*16     # Program Counter Stack
        self.SP = 0             # Stack Pointer

        self.display = [False]* (self.windowW * self.windowH)
        self.updateDisplay = False
        # load fontset here

    def loadProgram(self,file):
        with open(file, 'rb') as game:
            for i, byte in enumerate(game):
                self.memory[i] = byte
        print("Loaded %s".format(file))

    def runOp(self,offset):
        opCode = memory[offset] << 8 | memory[offset+1]

        fo = opCode & 0xF000
        if fo == 0x0000:
            if opCode&0xFFF == 0xE0
                # 0x00E0 Display clear
                self.display = [False]*(self.windowW*self.windowH)
                self.updateDisplay = True
            elif opCode&0xFFF == 0xEE:
                # 0x00EE Return
                self.PC = self.Stack[self.SP]
                if self.SP == 0:
                    exception("Cannot return from subroutine.")
                else:
                    self.Stack[self.SP] = self.Stack[self.SP-1]
                self.SP -= 1
            else:
                # 0x0NNN Call
                self.Stack[self.SP] = self.PC
                self.SP += 1
                self.PC = opCode & 0x0FFF
        elif fo == 0x1000:
            # 0x1NNN goto
            self.PC = opCode & 0xFFF
        elif fo == 0x2000:
            # 0x2NNN call subroutine
            self.
