#!/usr/bin/env python

# Copyright (C) 2012, 2020 Angelo Cano
#
# This file is part of Qvmdis.
#
# Qvmdis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Qvmdis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Qvmdis.  If not, see <https://www.gnu.org/licenses/>.

# allow importing from parent directory
# https://stackoverflow.com/questions/714063/importing-modules-from-parent-folder
#  answered Jun 22 '12 at 14:30  Remi
import inspect, os, sys
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from LEBinFile import LEBinFile
import sys

def output (msg):
    sys.stdout.write(msg)

# python 3 byte string ord() and chr() compatibility
#
#  s = b'\x00\x01\x02\x03'
#    python 2:  b[0] is '\x00'
#    python 3:  b[0] is 0
#
# slices are ok:  s[0:2] is b'\x00\x01' in both versions
#
# probably would have been easier to always access as slice to get a byte
# string instead of xord() and xchr().  Ex:  s[0:1] instead of s[0]

def xord (s):
    if isinstance(s, int):
        return s
    else:
        return ord(s)

def xchr (i):
    if isinstance(i, str):
        return i
    else:
        return chr(i)

# q3vm_specs.html wrong about header

class Opcode:
    def __init__ (self, val, name, parmSize):
        self.val = val
        self.name = name
        self.parmSize = parmSize

OP_NAME = 0
OP_PARM_SIZE = 1

opcodes = [ \
    ["undef", 0],
    ["ignore", 0],
    ["break", 0],
    ["enter", 4],
    ["leave", 4],
    ["call", 0],
    ["push", 0],
    ["pop", 0],
    ["const", 4],
    ["local", 4],
    ["jump", 0],
    ["eq", 4],
    ["ne", 4],
    ["lti", 4],
    ["lei", 4],
    ["gti", 4],
    ["gei", 4],
    ["ltu", 4],
    ["leu", 4],
    ["gtu", 4],
    ["geu", 4],
    ["eqf", 4],
    ["nef", 4],
    ["ltf", 4],
    ["lef", 4],
    ["gtf", 4],
    ["gef", 4],
    ["load1", 0],
    ["load2", 0],
    ["load4", 0],
    ["store1", 0],
    ["store2", 0],
    ["store4", 0],
    ["arg", 1],
    ["block_copy", 4],  # docs wrong?
    ["sex8", 0],
    ["sex16", 0],
    ["negi", 0],
    ["add", 0],
    ["sub", 0],
    ["divi", 0],
    ["divu", 0],
    ["modi", 0],
    ["modu", 0],
    ["muli", 0],
    ["mulu", 0],
    ["band", 0],
    ["bor", 0],
    ["bxor", 0],
    ["bcom", 0],
    ["lsh", 0],
    ["rshi", 0],
    ["rshu", 0],
    ["negf", 0],
    ["addf", 0],
    ["subf", 0],
    ["divf", 0],
    ["mulf", 0],
    ["cvif", 0],
    ["cvfi", 0]
]

class InvalidQvmFile(Exception):
    pass

class QvmFile(LEBinFile):
    magic = 0x12721444

    def __init__ (self, fname):
        self._file = open(fname, "rb")
        m = self.read_int()
        if m != self.magic:
            raise InvalidQvmFile("not a valid qvm file  0x%x != 0x%x" % (m, self.magic))

        self.instructionCount = self.read_int()
        self.codeSegOffset = self.read_int()
        self.codeSegLength = self.read_int()
        self.dataSegOffset = self.read_int()
        self.dataSegLength = self.read_int()
        self.litSegOffset = self.dataSegOffset + self.dataSegLength
        self.litSegLength = self.read_int()
        self.bssSegOffset = self.dataSegOffset + self.dataSegLength + self.litSegLength
        self.bssSegLength = self.read_int()

        self.seek (self.codeSegOffset)
        self.codeData = self.read(self.codeSegLength)

        self.seek (self.dataSegOffset)
        self.dataData = self.read(self.dataSegLength)

        self.seek (self.litSegOffset)
        self.litData = self.read(self.litSegLength)

    def print_header (self):
        output("instruction count: 0x%x\n" % self.instructionCount)
        output("CODE seg offset: 0x%08x  length: 0x%x  %d\n" % (self.codeSegOffset, self.codeSegLength, self.codeSegLength))
        output("DATA seg offset: 0x%08x  length: 0x%x  %d\n" % (self.dataSegOffset, self.dataSegLength, self.dataSegLength))
        output("LIT  seg offset: 0x%08x  length: 0x%x  %d\n" % (self.litSegOffset, self.litSegLength, self.litSegLength))
        output("BSS  seg offset: 0x%08x  length: 0x%x  %d\n" % (self.bssSegOffset, self.bssSegLength, self.bssSegLength))

    def print_code_disassembly (self):
        output("/* Code Segment */\n")
        self.seek (self.codeSegOffset)
        count = 0
        while count <= self.instructionCount:
            count = count + 1

            comment = None
            pos = self.tell()
            opc = self.read_byte()
            name = opcodes[opc][OP_NAME]
            psize = opcodes[opc][OP_PARM_SIZE]

            if psize == 0:
                parm = None
                #self.read_int()
            elif psize == 1:
                parm = self.read_byte()
                #self.read (3)
            elif psize == 4:
                parm = self.read_int()
            else:
                output("FIXME bad opcode size\n")
                sys.exit (1)

            if name == "enter":
                output("\n")
                if (count - 1) in self.functions:
                    output("%s ()\n" % self.functions[count - 1])
                output("========================\n")
            elif name == "const":
                origPos = self.tell()
                nextOp = self.read_byte()
                self.seek (origPos)

                if parm >= self.dataSegLength  and  parm < self.dataSegLength + self.litSegLength  and  opcodes[nextOp][OP_NAME] not in ("call", "jump"):
                    #output("\"%s\"\n" % litData[parm - self.dataSegLength])
                    chars = []
                    i = 0
                    while 1:
                        c = xord(self.litData[parm - self.dataSegLength + i])
                        if c == xord(b'\0'):
                            break
                        elif c == xord(b'\n'):
                            chars.extend(('\\', 'n'))
                        elif c == xord(b'\t'):
                            chars.extend(('\\', 't'))
                        else:
                            chars.append(xchr(c))
                        i = i + 1
                    output("\n  \"%s\"\n" % "".join(chars))
                elif parm >= 0  and  parm < self.dataSegLength  and  opcodes[nextOp][OP_NAME] not in ("call", "jump"):
                    b0 = self.dataData[parm]
                    b1 = self.dataData[parm + 1]
                    b2 = self.dataData[parm + 2]
                    b3 = self.dataData[parm + 3]

                    output("\n  %02x %02x %02x %02x  (0x%x)\n" % (xord(b0), xord(b1), xord(b2), xord(b3), struct.unpack("<L", self.dataData[parm:parm+4])[0]))

                    if parm in self.symbols:
                        comment = self.symbols[parm]

                elif opcodes[nextOp][OP_NAME] == "call":
                    if parm < 0  and  parm in self.syscalls:
                        comment = "%s ()" % self.syscalls[parm]
                    elif parm in self.functions:
                        comment = "%s ()" % self.functions[parm]

            output("%08x  %-13s " % (count - 1, name))
            if parm != None:
                if parm < 0:
                    output(" -0x%x " % -parm)
                else:
                    output("  0x%x " % parm)
            if comment:
                output("  // %s\n" % comment)
            else:
                output("\n")

    def print_data_disassembly (self):
        output("/* Data Segment */\n")
        i = 0
        while i < self.dataSegLength:
            output("0x%08x   " % i)
            b0 = self.dataData[i]
            b1 = self.dataData[i + 1]
            b2 = self.dataData[i + 2]
            b3 = self.dataData[i + 3]

            output("%02x %02x %02x %02x    0x%x\n" % (xord(b0), xord(b1), xord(b2), xord(b3), struct.unpack("<L", self.dataData[i:i+4])[0]))

            i = i + 4

    def print_lit_disassembly (self):
        output("/* Lit Segment */\n")
        pos = self.dataSegLength
        offset = 0
        while offset < self.litSegLength:
            output("0x%08x  " % (offset + pos))
            chars = []
            i = 0
            while 1:
                c = xord(self.litData[offset + i])
                if c == xord(b'\n'):
                    chars.extend(('\\', 'n'))
                elif c == xord(b'\t'):
                    chars.extend(('\\', 't'))
                elif xord(c) > 31  and  xord(c) < 127:
                    chars.append(xchr(c))
                elif c == xord(b'\0')  or  offset + i >= self.litSegLength:
                    output("\"%s\"\n" %  "".join(chars))
                    offset = offset + i
                    break
                else:
                    # not printable (< 31 or > 127) and not tab or newline
                    if len(chars) > 0:
                        output("\"%s\" " % "".join(chars))
                        chars = []
                    output(" 0x%x  " % xord(c))
                    pass

                i = i + 1

            offset = offset + 1

    def get_code (self):
        code = []
        ins = 0
        pos = 0
        while ins < self.instructionCount:
            # use a slice so you get a byte string in python 3
            opcStr = self.codeData[pos:pos + 1]
            opc = xord(opcStr)
            ins = ins + 1
            pos = pos + 1
            name = opcodes[opc][OP_NAME]
            psize = opcodes[opc][OP_PARM_SIZE]
            if psize:
                parmStr = self.codeData[pos : pos + psize]
            else:
                parmStr = None
            pos = pos + psize
            code.append(opcStr)
            if parmStr:
                code.append(parmStr)

        return b"".join(code)

    def close (self):
        self._file.close()

def main ():
    pass

if __name__ == "__main__":
    main ()
