#
# Chip8
#

import pyglet
from pyglet.window import key as keyCode
import random
import time

windowScale = 1
windowH = 32 * windowScale
windowW = 64 * windowScale
pixQt = windowH*windowW



class screen(object):
    poly = pyglet.gl.GL_POLYGON
    chip8_fontset = (
        0xF0, 0x90, 0x90, 0x90, 0xF0, # 0
        0x20, 0x60, 0x20, 0x20, 0x70, # 1
        0xF0, 0x10, 0xF0, 0x80, 0xF0, # 2
        0xF0, 0x10, 0xF0, 0x10, 0xF0, # 3
        0x90, 0x90, 0xF0, 0x10, 0x10, # 4
        0xF0, 0x80, 0xF0, 0x10, 0xF0, # 5
        0xF0, 0x80, 0xF0, 0x90, 0xF0, # 6
        0xF0, 0x10, 0x20, 0x40, 0x40, # 7
        0xF0, 0x90, 0xF0, 0x90, 0xF0, # 8
        0xF0, 0x90, 0xF0, 0x10, 0xF0, # 9
        0xF0, 0x90, 0xF0, 0x90, 0x90, # A
        0xE0, 0x90, 0xE0, 0x90, 0xE0, # B
        0xF0, 0x80, 0x80, 0x80, 0xF0, # C
        0xE0, 0x90, 0x90, 0x90, 0xE0, # D
        0xF0, 0x80, 0xF0, 0x80, 0xF0, # E
        0xF0, 0x80, 0xF0, 0x80, 0x80  # F
    )


    def __init__(self):
        self.window = pyglet.window.Window()
        self.window.set_minimum_size(windowW, windowH)
        pyglet.app.run()

    def drawPixel(self, x, y):
        # pixelSize = self.windowScale
        pix = pyglet.graphics.draw(4, poly, ('2vi',(
            x, y,
            x+1, y,
            x+1, y+1,
            x, y+1
            )))
        pix.draw()

    def drawFrame(self, display):
        self.window.clear()
        for i, pixel in enumerate(display):
            if pixel:
                x = i % windowW
                y = i / windowW
                drawPixel(x, y)

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

        self.Keys = [0]*16       # Keyboard storage

        self.display = [[False]*windowH]*windowW
        self.updateDisplay = False
        self.Screen = screen()
        
        for i, byte in enumerate(chip8_fontset):
            memory[i] = byte

    def loadProgram(self,file):
        with open(file, 'rb') as game:
            for i, byte in enumerate(game):
                self.memory[i] = byte
        print("Loaded %s".format(file))

    def runOp(self,offset):
        opCode = memory[offset] << 8 | memory[offset+1]

        fo = opCode & 0xF000
        if fo == 0x0000:
            if opCode&0xFFF == 0xE0:
                # 0x00E0 Clear the display
                self.display = [[False]*windowH]*windowW
                self.updateDisplay = True
                self.PC += 2
            elif opCode&0xFFF == 0xEE:
                # 0x00EE Return
                self.PC = self.Stack[self.SP] + 2
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
            self.Stack[self.SP] = self.PC
            self.SP += 1
            self.PC = opCode & 0x0FFF
        elif fo == 0x3000:
            # 0x3XNN Skip next if Vx == NN
            self.PC += 2
            if self.V[opCode&0xF00>>8] == opCode&0xFF:
                self.PC += 2
        elif fo == 0x4000:
            # 0x4XNN Skip next if Vx != NN
            self.PC += 2
            if self.V[opCode&0xF00>>8] != opCode&0xFF:
                self.PC += 2
        elif fo == 0x5000:
            # 0x5XY0 Skip next if Vx == Vy
            self.PC += 2
            if self.V[opCode&0xF00 >> 8] == self.V[opCode&0xF0 >> 4]:
                self.PC += 2
        elif fo == 0x6000:
            # 0x6XNN Set Vx to NN
            self.V[opCode&0xF00 >> 8] = opCode&0xFF
            self.PC += 2
        elif fo == 0x7000:
            # 0x7XNNN Add NN to Vx (no carry flag)
            self.V[opCode&0xF00 >> 8] += opCode&0xFF
            self.V[opCode&0xF00 >> 8] &= 0xFF
            self.PC += 2
        elif fo == 0x8000:
            # 0x8000 2-Var math
            pass
        elif fo == 0x9000:
            # 0x9XY0 Skip next if Vx != Vy
            self.PC += 2
            if self.V[opCode&0xF00 >> 8] != self.V[opCode&0xF0 >> 4]:
                self.PC += 2
        elif fo == 0xA000:
            # 0xANNN Set I to NNN
            self.I = opCode&0xFFF
            self.PC += 2
        elif fo == 0xB000:
            # 0xBNNN Jump to V0 + NNN
            self.PC = self.V[0] + opCode&0xFFF
        elif fo == 0xC000:
            # 0xCXNN Set Vx to (Rand&NN)
            self.V[opCode&0xF00 >> 8] = random.randint(0x00,0xFF) & (opCode&0xFF)
            self.PC += 2
        elif fo == 0xD000:
            # 0xDXYN Draw sprite at (Vx,Vy) width of 8px height of N
            x = self.V[opCode&0xF00 >> 8]
            y = self.V[opCode&0x0F0 >> 4]
            h = opCode&0x00F

            self.V[0xF] = 0 # Collision flag
            for line in range(h):
                for i in range(8):
                    old = self.display[x + 64*y + i]
                    new = self.memory[self.I + line][i]
                    self.display[x + 64*y + i] = new^old # Set bit
                    if new and old:
                        self.V[0xf] = 1 # Collision made
            self.updateDisplay = True
            self.PC += 2
        elif fo == 0xE000:
            # 0xE000 Keyboard Handling
            if opCode&0xFF == 0x9E:
                # 0xEX9E Skip next if key in Vx is pressed
                self.PC += 2
                if Keyboard[V[opCode&0xF00 >> 8]]:
                    self.PC += 2
            else:
                # 0xEXA1 Skip next if key in Vx is not pressed
                self.PC += 2
                if not Keyboard[V[opCode&0xF00 >> 8]]:
                    self.PC += 2
        elif fo == 0xF000:
            # 0xF000 Misc Functions
            selector = opCode&0xFF
            x = opCode&0xF00 >> 8
            if selector == 0x07:
                # 0xFX07 Set Vx to value of delayT
                self.V[x] = self.DelayT
                self.PC += 1
            elif selector == 0x0A:
                lastKey = Keys[:]
                while True:
                    for i, key in enumerate(lastKey):
                        updateKeys()
                        if Keys[i] != key:
                            V[x] = Keys[i]
                            break
                self.PC += 2
            elif selector == 0x15:
                # 0xFX15 Set DelayT to Vx
                self.DelayT = V[x]
                self.PC += 2
            elif selector == 0x18:
                # 0xFX18 Set SoundT to Vx
                self.SoundT = V[x]
                self.PC += 2
            elif selector == 0x1E:
                # 0xFX1E Add Vx to I
                self.I = self.I + self.V[x]
                if self.I > 0xFFF:
                    self.I &= 0xFFF
                    self.V[0xF] = 1
                else:
                    self.V[0xF] = 0
                self.PC += 2
            elif selector == 0x29:
                # 0xFX29 Sets I to the address for charactor in Vx
                self.I = self.V[x]*5
                self.PC += 2
            elif selector == 0x33:
                # 0xFX33 BCD of Vx stored in I
                num = self.V[x]
                self.memory[self.I] = num / 100
                self.memory[self.I+1] = (num / 10) % 10
                self.memory[self.I+2] = (num%100) % 10
                self.PC += 2
            elif selector == 0x55:
                # 0xFX55 Store V0-x in memory starting at I
                for num in range(x):
                    self.I += num
                    self.memory[self.I] = self.V[num]
                self.PC += 2
            elif selector == 0x65:
                # 0xFX65 Store memory to V0-x starting at I
                for num in range(x):
                    self.I += num
                    self.V[num] = self.memory[self.I]
                self.PC += 2
        else:
            # Unhandled Opcode
            print("Cannot parse %s. Opcode not found.".format(str(hex(opCode))))

    def updateKeys(self):
        keyboard = keyCode.KeyStateHandler()
        self.screen.window.push_handlers(keyboard)
        self.Keys = [
            keyCode._1, keyCode._2, keyCode._4, keyCode._4,
            keyCode.Q, keyCode.W, keyCode.E, keyCode.R,
            keyCode.A, keyCode.S, keyCode.D, keyCode.F,
            keyCode.Z, keyCode.X, keyCode.C, keyCode.V ]

    def runCycle(self):
        updateKeys()
        runOp(self.PC)
        if updateDisplay:
            self.screen.drawFrame(self.display)

if __name__ == "__main__":
    emu = Chip8()
    emu.loadProgram('pong.ch8')
