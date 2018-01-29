#
# Chip8
#

import pygame
import random, math
import time
import code

windowScale = 5
windowH = 32 * windowScale
windowW = 64 * windowScale
pixQt = windowH*windowW
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
def fhex(i, l=4):
    return "{0:#0{1}x}".format(i,l+2)

class screen(object):
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode([windowW,windowH])

    def drawPixel(self, i):
        # pixelSize = self.windowScale
        x = i % windowW
        y = math.floor(i / windowW)
        #print("Pixel at:",x,y)
        pygame.draw.rect(self.window,
            (0, 255, 255), # Color
            (x*windowScale, y*windowScale, windowScale, windowScale) # Rect
        )
            

    def drawFrame(self, display):
        for i, pixel in enumerate(display):
            if pixel:
                self.drawPixel(i)
        pygame.display.flip()

class Chip8(object):
    def __init__(self):
        self.level = 0
        self.memory = [0]*4096  # RAM
        self.V = [0]*16         # GP Reg
        self.I = 0              # Index Reg
        self.PC = 0x200         # Program Counter

        self.DelayT = 0         # Delay Timer
        self.SoundT = 0         # Sound Timer

        self.Stack = [0]*16     # Program Counter Stack
        self.SP = 0             # Stack Pointer

        self.Keys = [0]*16       # Keyboard storage

        self.display = [0]*64*32
        self.updateDisplay = False
        self.Screen = screen()
        
        for i, byte in enumerate(chip8_fontset):
            self.memory[i] = byte

    def loadProgram(self,file):
        with open(file, 'rb') as game:
            for i, byte in enumerate(game.read()):
                self.memory[0x200+i] = byte
        print("Loaded file:", file)
        if __debug__:
            print("  Addr | Instr. | V Reg.")

    def runOp(self,offset):
        opCode = self.memory[offset] << 8 | self.memory[offset+1]
        if __debug__:
            print("-"*self.level,fhex(offset,3), "|", fhex(opCode), "|",\
                self.V, "|", [hex(x) for x in self.Stack if x!=0])

        fo = opCode & 0xF000
        if fo == 0x0000:
            if opCode&0xFFF == 0xE0:
                # 0x00E0 Clear the display
                self.display = [0]*32*64
                self.updateDisplay = True
                self.PC += 2
            elif opCode&0xFFF == 0xEE:
                # 0x00EE Return
                self.SP -= 1
                self.PC = self.Stack[self.SP] + 2
                if self.SP == -1:
                    assert False
                else:
                    self.Stack[self.SP] = 0
                self.level -= 1
            else:
                # 0x0NNN Call
                self.Stack[self.SP] = self.PC
                self.SP += 1
                self.PC = opCode & 0x0FFF
                self.level += 1
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
            if self.V[(opCode&0xF00)>>8] == opCode&0xFF:
                self.PC += 2
        elif fo == 0x4000:
            # 0x4XNN Skip next if Vx != NN
            self.PC += 2
            if self.V[(opCode&0xF00)>>8] != opCode&0xFF:
                self.PC += 2
        elif fo == 0x5000:
            # 0x5XY0 Skip next if Vx == Vy
            self.PC += 2
            if self.V[(opCode&0xF00) >> 8] == self.V[(opCode&0x0F0) >> 4]:
                self.PC += 2
        elif fo == 0x6000:
            # 0x6XNN Set Vx to NN
            self.V[(opCode&0xF00) >> 8] = opCode&0xFF
            self.PC += 2
        elif fo == 0x7000:
            # 0x7XNNN Add NN to Vx (no carry flag)
            self.V[(opCode&0xF00) >> 8] += opCode&0xFF
            self.V[(opCode&0xF00) >> 8] &= 0xFF
            self.PC += 2
        elif fo == 0x8000:
            # 0x8000 2-Var math
            x = opCode&0xF00 >> 8
            y = opCode&0x0F0 >> 4
            selector = opCode&0x00F

            if selector == 0x1:
                # 0x8YX1 Set Vx to Vx|Vy
                self.V[x] |= self.V[y]
            elif selector == 0x2:
                # 0x8YX2 Set Vx to Vx&Vy
                self.V[x] &= self.V[y]
            elif selector == 0x3:
                # 0x8YX3 Set Vx to Vx^Vy
                self.V[x] ^= self.V[y]
            elif selector == 0x4:
                # 0x8YX4 Set Vx to Vx+Vy
                self.V[x] += self.V[y]
            elif selector == 0x5:
                # 0x8YX5 Set Vx to Vx-Vy
                self.V[x] -= self.V[y]
            elif selector == 0x6:
                # 0x8YX6 Set Vx and Vy to Vy >> 1
                self.V[x] = self.V[y] >> 1
                self.V[y] = self.V[x]
            elif selector == 0x7:
                # 0x8YX7 Set Vx to Vy-Vx
                self.V[x] = self.V[y] - V[x]
                if self.V[x]&0xF0 > self.V[y]&0xF0:
                   self.V[0xF] = 1
                elif self.V[x]&0xF > self.V[y]&0xF:
                   self.V[0xF] = 1
                else:
                    self.V[0xF] = 0
            elif selector == 0xE:
                # 0x8XYE Set Vx and Vy to Vy << 1
                self.V[x] = self.V[y] << 1
                self.V[y] = self.V[x]
            self.PC += 2
        elif fo == 0x9000:
            # 0x9XY0 Skip next if Vx != Vy
            self.PC += 2
            if self.V[(opCode&0xF00) >> 8] != self.V[(opCode&0x0F0) >> 4]:
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
            self.V[(opCode&0xF00) >> 8] = random.randint(0x00,0xFF) & (opCode&0xFF)
            self.PC += 2
        elif fo == 0xD000:
            # 0xDXYN Draw sprite at (Vx,Vy) width of 8px height of N
            x = self.V[(opCode&0xF00) >> 8]
            y = self.V[(opCode&0x0F0) >> 4] * 64
            h = opCode&0x00F
            #print("New sprite at",x,int(y/64), h)

            self.V[0xF] = 0 # Collision flag
            for line in range(h):
                byte = [int(i) for i in bin(self.memory[self.I + line*8])[2:].rjust(8,'0')]
                for i, new in enumerate(byte): # Width of 8px
                    old = self.display[x + y + i]
                    self.display[x + y + i] = new^old # Set bit
                    if new and old:
                        self.V[0xF] = 1 # Collision made
            self.updateDisplay = True
            self.PC += 2
        elif fo == 0xE000:
            # 0xE000 Keyboard Handling
            if opCode&0xFF == 0x9E:
                # 0xEX9E Skip next if key in Vx is pressed
                self.PC += 2
                if self.Keys[self.V[(opCode&0xF00) >> 8]]:
                    self.PC += 2
            else:
                # 0xEXA1 Skip next if key in Vx is not pressed
                self.PC += 2
                if not self.Keys[self.V[(opCode&0xF00) >> 8]]:
                    self.PC += 2
        elif fo == 0xF000:
            # 0xF000 Misc Functions
            selector = opCode&0xFF
            x = opCode&0xF00 >> 8
            if selector == 0x07:
                # 0xFX07 Set Vx to value of delayT
                self.V[x] = self.DelayT
                self.PC += 2
            elif selector == 0x0A:
                lastKey = self.Keys[:]
                while True:
                    for i, key in enumerate(lastKey):
                        self.updateKeys()
                        if self.Keys[i] != key:
                            self.V[x] = self.Keys[i]
                            break
                self.PC += 2
            elif selector == 0x15:
                # 0xFX15 Set DelayT to Vx
                self.DelayT = self.V[x]
                self.PC += 2
            elif selector == 0x18:
                # 0xFX18 Set SoundT to Vx
                self.SoundT = self.V[x]
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
                self.memory[self.I] = int(num / 100)
                self.memory[self.I+1] = int((num / 10) % 10)
                self.memory[self.I+2] = (num%100) % 10
                self.PC += 2
            elif selector == 0x55:
                # 0xFX55 Store V0-x in self.memory starting at I
                for num in range(x):
                    self.I += num
                    self.memory[self.I] = self.V[num]
                self.PC += 2
            elif selector == 0x65:
                # 0xFX65 Store self.memory to V0-x starting at I
                for num in range(x):
                    self.I += num
                    self.V[num] = self.memory[self.I]
                self.PC += 2
            else:

                print(hex(opCode),"not found. Address", offset)
                assert False
        else:
            # Unhandled Opcode
            print("Cannot parse %s. Opcode not found.".format(str(hex(opCode))))
            assert False

    def updateKeys(self):
        cKey = pygame.key.get_pressed()
        self.Keys = [
            cKey[pygame.K_1], cKey[pygame.K_2], cKey[pygame.K_4], cKey[pygame.K_4],
            cKey[pygame.K_q], cKey[pygame.K_w], cKey[pygame.K_e], cKey[pygame.K_r],
            cKey[pygame.K_a], cKey[pygame.K_s], cKey[pygame.K_d], cKey[pygame.K_f],
            cKey[pygame.K_z], cKey[pygame.K_x], cKey[pygame.K_c], cKey[pygame.K_v]]

    def runCycle(self):
        self.updateKeys()
        self.runOp(self.PC)
        if self.updateDisplay:
            self.Screen.drawFrame(self.display)

if __name__ == "__main__":
    emu = Chip8()
    emu.loadProgram('pong.ch8')
    #code.interact(local=locals())
    while True:
        emu.runCycle()
        time.sleep(1.0/60)