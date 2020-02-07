#!/usr/bin/env python

####
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
####

import os.path, re, struct, sys
from LEBinFile import LEBinFile

# python hash() builtin gives different values for 32-bit and 64-bit implementations
# http://effbot.org/zone/python-hash.htm

def c_mul(a, b):
    #v = eval(hex((long(a) * b) & 0xFFFFFFFFL)[:-1])
    # 32-bit signed
    v = a * b
    v = v & 0xffffffff

    if v > 0x7fffffff:
        v = -(0x100000000 - v)
    return v

def hash32BitSigned (str):
    if not str:
        return 0  # empty
    value = ord(str[0]) << 7
    for char in str:
        value = c_mul(1000003, value) ^ ord(char)
    value = value ^ len(str)
    if value == -1:
        value = -2
    return value

def atoi (s, base=10):
    return int(s, base)

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

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

CGAME_SYSCALLS_ASM_FILE = "cg_syscalls.asm"
GAME_SYSCALLS_ASM_FILE = "g_syscalls.asm"
UI_SYSCALLS_ASM_FILE = "ui_syscalls.asm"

BASEQ3_CGAME_FUNCTIONS_FILE = "baseq3-cgame-functions.hmap"
BASEQ3_GAME_FUNCTIONS_FILE = "baseq3-game-functions.hmap"
BASEQ3_UI_FUNCTIONS_FILE = "baseq3-ui-functions.hmap"

SYMBOLS_FILE = "symbols.dat"
FUNCTIONS_FILE = "functions.dat"
CONSTANTS_FILE = "constants.dat"
COMMENTS_FILE = "comments.dat"

QVM_MAGIC_VER1 = 0x12721444
QVM_MAGIC_VER2 = 0x12721445

def output (msg):
    sys.stdout.write(msg)

def warning_msg (msg):
    # send to both stdout and stderr since output is usually redirected to file
    sys.stdout.write("; warning : %s\n" % msg)
    sys.stderr.write("warning: %s\n" % msg)

def error_msg (msg):
    # send to both stdout and stderr since output is usually redirected to file
    sys.stdout.write("---- error occurred : %s\n" % msg)
    sys.stderr.write("ERROR: %s\n" % msg)

def error_exit (msg, exitValue = 1):
    error_msg(msg)
    sys.exit(exitValue)

OP_NAME = 0
OP_PARM_SIZE = 1
OP_JUMP_PARM = 2
OP_STACK_CHANGE = 3
OP_DESC = 4  # from q3vm_specs.html and ioquake3 source code (2020-01-30)

opcodes = [ \
    ["undef", 0, False, 0, "undefined opcode."],
    ["ignore", 0, False, 0, "no-operation (nop) instruction."],
    ["break", 0, False, 0, "set debugging break point."],
    ["enter", 4, False, 0, "Begin procedure body, adjust stack $PARM octets for frame (always at least 8 (i.e. 2 words)).  Frame contains all local storage/variables and arguments space for any calls within this procedure."],  # establishes current stack so 0 relative change
    ["leave", 4, False, 0, "End procedure body, $PARM is same as that of the matching ENTER."],
    ["call", 0, False, -1, "make call to procedure (code address <- TOS)."],  # call address is removed, but by convention the called function leaves a value on the stack
    ["push", 0, False, 1, "push nonsense (void) value to opstack (TOS <- 0)."],
    ["pop", 0, False, -1, "pop a value from stack (remove TOS, decrease stack by 1)."],
    ["const", 4, False, 1, "push literal value onto stack (TOS <- $PARM)"],
    ["local", 4, False, 1, "get address of local storage (local variable or argument) (TOS <- (frame + $PARM))."],
    ["jump", 0, False, -1, "branch (code address <- TOS)"],
    ["eq", 4, True, -2, "check equality (signed integer) (compares NIS vs TOS, jump to $PARM if true)."],
    ["ne", 4, True, -2, "check inequality (signed integer) (NIS vs TOS, jump to $PARM if true)."],
    ["lti", 4, True, -2, "check less-than (signed integer) (NIS vs TOS, jump to $PARM if true)."],
    ["lei", 4, True, -2, "check less-than or equal-to (signed integer) (NIS vs TOS, jump to $PARM if true)."],
    ["gti", 4, True, -2, "check greater-than (signed integer) (NIS vs TOS), jump to $PARM if true."],
    ["gei", 4, True, -2, "check greater-than or equal-to (signed integer) (NIS vs TOS), jump to $PARM if true."],
    ["ltu", 4, True, -2, "check less-than (unsigned integer) (NIS vs TOS), jump to $PARM if true."],
    ["leu", 4, True, -2, "check less-than or equal-to (unsigned integer) (NIS vs TOS), jump to $PARM if true."],
    ["gtu", 4, True, -2, "check greater-than (unsigned integer) (NIS vs TOS), jump to $PARM if true."],
    ["geu", 4, True, -2, "check greater-than or equal-to (unsigned integer) (NIS vs TOS), jump to $PARM if true."],
    ["eqf", 4, True, -2, "check equality (float) (NIS vs TOS, jump to $PARM if true)."],
    ["nef", 4, True, -2, "check inequality (float) (NIS vs TOS, jump to $PARM if true)."],
    ["ltf", 4, True, -2, "check less-than (float) (NIS vs TOS, jump to $PARM if true)."],
    ["lef", 4, True, -2, "check less-than or equal-to (float) (NIS vs TOS, jump to $PARM if true)."],
    ["gtf", 4, True, -2, "check greater-than (float) (NIS vs TOS, jump to $PARM if true)."],
    ["gef", 4, True, -2, "check greater-than or equal-to (float) (NIS vs TOS, jump to $PARM if true)."],
    ["load1", 0, False, 0, "Load 1-octet value from address in TOS (TOS <- [TOS])"],
    ["load2", 0, False, 0, "Load 2-octet value from address in TOS (TOS <- [TOS])"],
    ["load4", 0, False, 0, "Load 4-octet value from address in TOS (TOS <- [TOS])"],
    ["store1", 0, False, -2, "lowest octet of TOS is 1-octet value to store, destination address in next-in-stack ([NIS] <- TOS)."],
    ["store2", 0, False, -2, "lowest two octets of TOS is 2-octet value to store, destination address in next-in-stack ([NIS] <- TOS)."],
    ["store4", 0, False, -2, "TOS is 4-octet value to store, destination address in next-in-stack ([NIS] <- TOS)."],
    ["arg", 1, False, -1, "TOS is 4-octet value to store into arguments-marshalling space of the indicated octet offset (ARGS[offset] <- TOS)."],
    ["block_copy", 4, False, -2, "copy $PARM bytes from TOS into NIS."],  # q3vm_specs.html wrong about parameter size
    ["sex8", 0, False, 0, "Sign-extend 8-bit (TOS <- TOS)."],
    ["sex16", 0, False, 0, "Sign-extend 16-bit (TOS <- TOS)."],
    ["negi", 0, False, 0, "Negate signed integer (TOS <- -TOS)."],
    ["add", 0, False, -1, "Add integer-wise (TOS <- NIS + TOS)."],
    ["sub", 0, False, -1, "Subtract integer-wise (TOS <- NIS - TOS)."],
    ["divi", 0, False, -1, "Divide integer-wise (TOS <- NIS / TOS)."],
    ["divu", 0, False, -1, "Divide unsigned integer (TOS <- NIS / TOS)."],
    ["modi", 0, False, -1, "Modulo (signed integer) (TOS <- NIS mod TOS)."],
    ["modu", 0, False, -1, "Modulo (unsigned integer) (TOS <- NIS mod TOS)."],
    ["muli", 0, False, -1, "Multiply (signed integer) (TOS <- NIS * TOS)."],
    ["mulu", 0, False, -1, "Multiply (unsigned integer) (TOS <- NIS * TOS)."],
    ["band", 0, False, -1, "Bitwise AND (TOS <- NIS & TOS)."],
    ["bor", 0, False, -1, "Bitwise OR (TOS <- NIS | TOS)."],
    ["bxor", 0, False, -1, "Bitwise XOR (TOS <- NIS ^ TOS)."],
    ["bcom", 0, False, 0, "Bitwise complement (TOS <- ~TOS)."],
    ["lsh", 0, False, -1, "Bitwise left-shift (TOS <- NIS << TOS)."],
    ["rshi", 0, False, -1, "Algebraic (signed) right-shift (TOS <- NIS >> TOS)."],
    ["rshu", 0, False, -1, "Bitwise (unsigned) right-shift (TOS <- NIS >> TOS)."],
    ["negf", 0, False, 0, "Negate float value (TOS <- -TOS)."],
    ["addf", 0, False, -1, "Add floats (TOS <- NIS + TOS)."],
    ["subf", 0, False, -1, "Subtract floats (TOS <- NIS - TOS)."],
    ["divf", 0, False, -1, "Divide floats (TOS <- NIS / TOS)."],
    ["mulf", 0, False, -1, "Multiply floats (TOS <- NIS x TOS)."],
    ["cvif", 0, False, 0, "Convert signed integer to float (TOS <- TOS)."],
    ["cvfi", 0, False, 0, "Convert float to signed integer (TOS <- TOS)."]
]


(
OPC_UNDEF,

OPC_IGNORE,

OPC_BREAK,

OPC_ENTER,
OPC_LEAVE,
OPC_CALL,
OPC_PUSH,
OPC_POP,

OPC_CONST,
OPC_LOCAL,

OPC_JUMP,

OPC_EQ,
OPC_NE,

OPC_LTI,
OPC_LEI,
OPC_GTI,
OPC_GEI,

OPC_LTU,
OPC_LEU,
OPC_GTU,
OPC_GEU,

OPC_EQF,
OPC_NEF,

OPC_LTF,
OPC_LEF,
OPC_GTF,
OPC_GEF,

OPC_LOAD1,
OPC_LOAD2,
OPC_LOAD4,
OPC_STORE1,
OPC_STORE2,
OPC_STORE4,
OPC_ARG,

OPC_BLOCK_COPY,

OPC_SEX8,
OPC_SEX16,

OPC_NEGI,
OPC_ADD,
OPC_SUB,
OPC_DIVI,
OPC_DIVU,
OPC_MODI,
OPC_MODU,
OPC_MULI,
OPC_MULU,

OPC_BAND,
OPC_BOR,
OPC_BXOR,
OPC_BCOM,

OPC_LSH,
OPC_RSHI,
OPC_RSHU,

OPC_NEGF,
OPC_ADDF,
OPC_SUBF,
OPC_DIVF,
OPC_MULF,

OPC_CVIF,
OPC_CVFI ) = range(60)


class InvalidQvmFile(Exception):
    pass

class QvmFile(LEBinFile):

    # qvmType:("cgame", "game", "ui", None)
    def __init__ (self, qvmFileName, qvmType=None):
        self._file = open(qvmFileName, "rb")
        self.magic = self.read_int()
        if self.magic != QVM_MAGIC_VER1  and  self.magic != QVM_MAGIC_VER2:
            raise InvalidQvmFile("not a valid qvm file, magic 0x%x != (0x%x | 0x%x)" % (self.magic, QVM_MAGIC_VER1, QVM_MAGIC_VER2))

        # q3vm_specs.html wrong about header, it's offset and then length

        self.instructionCount = self.read_int()
        self.codeSegOffset = self.read_int()
        self.codeSegLength = self.read_int()
        self.dataSegOffset = self.read_int()
        self.dataSegLength = self.read_int()
        self.litSegOffset = self.dataSegOffset + self.dataSegLength
        self.litSegLength = self.read_int()
        self.bssSegOffset = self.dataSegOffset + self.dataSegLength + self.litSegLength
        self.bssSegLength = self.read_int()

        if self.magic != QVM_MAGIC_VER1:
            self.jumpTableOffset = self.litSegOffset + self.litSegLength
            self.jumpTableLength = self.read_int()
        else:
            self.jumpTableLength = 0


        # validate header values
        if self.instructionCount < 0:
            raise InvalidQvmFile("bad header: instructionCount %d" % self.instructionCount)
        if self.codeSegOffset < 0:
            raise InvalidQvmFile("bad header: codeSegOffset %d" % self.codeSegOffset)
        if self.codeSegLength < 0:
            raise InvalidQvmFile("bad header: codeSegLength %d" % self.codeSegLength)
        if self.dataSegOffset < 0:
            raise InvalidQvmFile("bad header: dataSegOffset %d" % self.dataSegOffset)
        if self.dataSegLength < 0:
            raise InvalidQvmFile("bad header: dataSegLength %d" % self.dataSegLength)
        if self.litSegLength < 0:
            raise InvalidQvmFile("bad header: litSegLength %d" % self.litSegLength)
        if self.bssSegLength < 0:
            raise InvalidQvmFile("bad header: bssSegLength %d" % self.bssSegLength)
        if self.jumpTableLength < 0:
            raise InvalidQvmFile("bad header: jumpTableLength %d" % self.jumpTableLength)

        self.seek(self.codeSegOffset)
        self.codeData = self.read(self.codeSegLength)
        self.codeData = self.codeData + b"\x00\x00\x00\x00\x00"  # for look ahead
        self.seek(self.dataSegOffset)
        self.dataData = self.read(self.dataSegLength)
        self.dataData = self.dataData + b"\x00\x00\x00\x00"  # for look ahead

        self.seek(self.litSegOffset)
        self.litData = self.read(self.litSegLength)
        self.litData = self.litData + b"\x00\x00\x00\x00"  # for look ahead

        if self.magic != QVM_MAGIC_VER1:
            self.jumpTableData = self.read(self.jumpTableLength)
        else:
            self.jumpTableData = b""

        self.syscalls = {}  # num:int -> name:str
        self.functions = {}  # addr:int -> name:str

        # user labels
        self.functionsArgLabels = {}  # addr:int -> { argX:str -> sym:str }
        self.functionsLocalLabels = {}  # addr:int -> { localAddr:int -> sym:str }
        self.functionsLocalRangeLabels = {}  # addr:int -> { localAddr:int -> [ [size1:int, sym1:str], [size2:int, sym2:str], ... ] }

        self.functionHashes = {}  # addr:int -> hash:int
        self.functionRevHashes = {}  # hash:int -> [funcAddr1:int, funcAddr2:int, ...]
        self.functionSizes = {}  # addr:int -> instructionCount:int
        self.functionMaxArgsCalled = {}  # addr:int -> maxArgs:int
        self.functionParmNum = {}  # addr:int -> num:int

        self.baseQ3FunctionRevHashes = {}  # hash:int -> [ funcName1, funcName2, ... ]

        self.symbols = {}  # addr:int -> sym:str
        self.symbolsRange = {}  # addr:int -> [ [size1:int, sym1:str], [size2:int, sym2:str], ... ]
        self.constants = {}  # codeAddr:int -> [ name:str, value:int ]

        # code segment comments
        self.commentsInline = {}  # addr:int -> comment:str
        self.commentsBefore = {}  # addr:int -> [ line1:str, line2:str, ... ]
        self.commentsBeforeSpacing = {}  # addr:int -> [ spaceBefore:int, spaceAfter:int ]
        self.commentsAfter = {}  # addr:int -> [ line1:str, line2:str, ... ]
        self.commentsAfterSpacing = {}  # addr:int -> [ spaceBefore:int, spaceAfter: int ]

        # data segment comments
        self.dataCommentsInline = {}  # addr:int -> comment:str
        self.dataCommentsBefore = {}  # addr:int -> [ line1:str, line2:str, ... ]
        self.dataCommentsBeforeSpacing = {}  # addr:int -> [ spaceBefore:int, spaceAfter:int ]
        self.dataCommentsAfter = {}  # addr:int -> [ line1:str, line2:str, ... ]
        self.dataCommentsAfterSpacing = {}  # addr:int -> [ spaceBefore:int, spaceAfter: int ]

        self.jumpPoints = {}  # targetAddr:int -> [ jumpPointAddr1:int, jumpPointAddr2:int, ... ]
        self.switchStartStatements = []  # [ addr1:int, addr2:int, ... ]
        self.switchJumpStatements = {}  # addr:int -> [ minValue:int, maxValue:int, switchJumpTableAddress:int ]
        self.switchJumpPoints = {}  # targetAddr:int -> [ [ jumpPointAddr1:int, caseValue:int ], [ jumpPointAddr2:int, caseValue:int ],  ... ]
        self.callPoints = {}  # targetAddr:int -> [ callerAddr1:int, callerAddr2:int, ... ]

        self.jumpTableTargets = []  # [ targetAddr1:int, targetAddr2:int, targetAddr3:int, ... ]

        self.set_qvm_type(qvmType)
        self.load_address_info()
        self.parse_jump_table()
        self.compute_function_info()

    def set_qvm_type (self, qvmType):
        self.qvmType = qvmType

        if qvmType not in ("cgame", "game", "ui"):
            return

        if qvmType == "cgame":
            fname = CGAME_SYSCALLS_ASM_FILE
        elif qvmType == "game":
            fname = GAME_SYSCALLS_ASM_FILE
        elif qvmType == "ui":
            fname = UI_SYSCALLS_ASM_FILE

        if os.path.exists(fname):
            f = open(fname)
        else:
            f = open(os.path.join(BASE_DIR, fname))

        lines = f.readlines()
        f.close()

        lineCount = 0
        for line in lines:
            words = line.split()
            if len(words) == 3:
                try:
                    self.syscalls[atoi(words[2])] = words[1]
                except ValueError:
                    error_exit("couldn't parse system call number in line %d of %s: %s" % (lineCount + 1, fname, line))
            lineCount += 1

        if qvmType == "cgame":
            fname = BASEQ3_CGAME_FUNCTIONS_FILE
        elif qvmType == "game":
            fname = BASEQ3_GAME_FUNCTIONS_FILE
        elif qvmType == "ui":
            fname = BASEQ3_UI_FUNCTIONS_FILE

        if os.path.exists(fname):
            f = open(fname)
        else:
            f = open(os.path.join(BASE_DIR, fname))

        lines = f.readlines()
        f.close()
        lineCount = 0
        for line in lines:
            words = line.split()
            if len(words) > 2:
                n = words[1]
                try:
                    h = atoi(words[2], 16)
                except ValueError:
                    error_exit("couldn't parse hash value in line %d of %s: %s" % (lineCount + 1, fname, line))
                if h in self.baseQ3FunctionRevHashes:
                    self.baseQ3FunctionRevHashes[h].append(n)
                else:
                    self.baseQ3FunctionRevHashes[h] = [n]
            lineCount += 1

    # addr:int, symbolsRange:{} addr:int -> [ [size1:int, sym1:str], [size2:int, sym2:str], ... ]
    def find_in_symbol_range (self, addr, symbolsRange):
        exactMatches = []  #FIXME sorted
        match = None
        matchDiff = 0
        matchSym = ""
        matchRangeSize = 0
        for rangeAddr in symbolsRange:
            for r in symbolsRange[rangeAddr]:
                size = r[0]
                sym = r[1]
                if addr == rangeAddr:
                    exactMatches.append(sym)
                elif addr >= rangeAddr  and  addr < (rangeAddr + size):
                    if match == None:
                        match = rangeAddr
                        matchSym = sym
                        matchDiff = addr - rangeAddr
                        matchRangeSize = size
                    elif (addr - rangeAddr) < matchDiff:
                        match = rangeAddr
                        matchSym = sym
                        matchDiff = addr - rangeAddr
                        matchRangeSize = size
                    elif (addr - rangeAddr) == matchDiff:  # multiple ranges beginning at same address
                        # pick smallest
                        if size < matchRangeSize:
                            match = rangeAddr
                            matchSym = sym
                            matchDiff = addr - rangeAddr
                            matchRangeSize = size

        return (match, matchSym, matchDiff, exactMatches)

    def substitute_variables (self, line):
        # ex: x = @f{0x89}("testing", 0x68, @d{0xcba94 could be clientNum});

        def matchFunc (match):
            t = match.group("type")
            v = match.group("value")

            try:
                addr = atoi(v, 16)
            except ValueError as ex:
                error_msg("couldn't parse address: %s" % v)
                # raise again to let caller print file and line number
                raise ex

            if t == 'd':
                if addr in self.symbols:
                    return self.symbols[addr]
                else:  # check symbol ranges
                    (matchAddr, matchSym, matchDiff, exactMatches) = self.find_in_symbol_range(addr, self.symbolsRange)
                    if len(exactMatches) > 0:
                        return ":".join(exactMatches)
                    else:
                        if matchAddr != None:
                            return "%s+0x%x" % (matchSym, matchDiff)
            else:  # 'f'
                if addr in self.functions:
                    return self.functions[addr]

            # not found
            return "@%s{%s}" % (t, v)

        c = re.compile("@(?P<type>f|d){\s*(?P<value>\w+)\s?.*?}")
        r = c.sub(matchFunc, line)
        return r

    def load_address_info (self):
        fname = SYMBOLS_FILE
        if os.path.exists(fname):
            f = open(fname)
            lines = f.readlines()
            f.close()
            lineCount = 0
            for line in lines:
                # strip comments
                line = line.split(";")[0]
                words = line.split()
                if len(words) == 2:
                    try:
                        self.symbols[atoi(words[0], 16)] = words[1]
                    except ValueError:
                        error_exit("couldn't parse address in line %d of %s: %s" % (lineCount + 1, fname, line))
                elif len(words) == 3:
                    try:
                        addr = atoi(words[0], 16)
                        size = atoi(words[1], 16)
                    except ValueError:
                        error_exit("couldn't parse address or size in line %d of %s: %s" % (lineCount + 1, fname, line))
                    sym = words[2]
                    if not addr in self.symbolsRange:
                        self.symbolsRange[addr] = []
                    self.symbolsRange[addr].append([size, sym])

                lineCount += 1

        fname = FUNCTIONS_FILE
        if os.path.exists(fname):
            f = open(fname)
            lines = f.readlines()
            f.close()
            lineCount = 0
            currentFuncAddr = None
            while lineCount < len(lines):
                line = lines[lineCount]
                # strip comments
                line = line.split(";")[0]
                words = line.split()
                if len(words) > 1:
                    if words[0].startswith("arg"):
                        if currentFuncAddr == None:
                            error_exit("function not defined yet in line %d of %s: %s" % (lineCount + 1, fname, line))
                        if not currentFuncAddr in self.functionsArgLabels:
                            self.functionsArgLabels[currentFuncAddr] = {}
                        self.functionsArgLabels[currentFuncAddr][words[0]] = words[1]
                    elif words[0] == "local":
                        if currentFuncAddr == None:
                            error_exit("function not defined yet in line %d of %s: %s" % (lineCount + 1, fname, line))
                        if len(words) < 3:
                            error_exit("invalid local specification in line %d of %s: %s" % (lineCount + 1, fname, line))
                        if len(words) > 3:  # range specified
                            try:
                                localAddr = atoi(words[1], 16)
                                size = atoi(words[2], 16)
                            except ValueError:
                                error_exit("couldn't parse address or size of range in line %d of %s: %s" % (lineCount + 1, fname, line))

                            sym = words[3]
                            if not currentFuncAddr in self.functionsLocalRangeLabels:
                                self.functionsLocalRangeLabels[currentFuncAddr] = {}
                            if not localAddr in self.functionsLocalRangeLabels[currentFuncAddr]:
                                self.functionsLocalRangeLabels[currentFuncAddr][localAddr] = []
                            self.functionsLocalRangeLabels[currentFuncAddr][localAddr].append([size, sym])
                        else:
                            if not currentFuncAddr in self.functionsLocalLabels:
                                self.functionsLocalLabels[currentFuncAddr] = {}
                            try:
                                self.functionsLocalLabels[currentFuncAddr][atoi(words[1], 16)] = words[2]
                            except ValueError:
                                error_exit("couldn't parse address in line %d of %s: %s" % (lineCount + 1, fname, line))
                    else:
                        # function definition
                        try:
                            funcAddr = atoi(words[0], 16)
                        except ValueError:
                            error_exit("couldn't parse address in line %d of %s: %s" % (lineCount + 1, fname, line))
                        self.functions[funcAddr] = words[1]
                        currentFuncAddr = funcAddr

                lineCount += 1

        fname = CONSTANTS_FILE
        if os.path.exists(fname):
            f = open(fname)
            lines = f.readlines()
            f.close()
            lineCount = 0
            for line in lines:
                # strip comments
                line = line.split(";")[0]
                words = line.split()
                if len(words) > 2:
                    try:
                        codeAddr = atoi(words[0], 16)
                        n = words[1]
                        val = atoi(words[2], 16)
                    except ValueError:
                        error_exit("couldn't parse address or value in line %d of %s: %s" % (lineCount + 1, fname, line))
                    self.constants[codeAddr] = [n, val]

                lineCount += 1

        # load after functions and symbols files to allow variable substitutions
        fname = COMMENTS_FILE
        if os.path.exists(fname):
            f = open(fname)
            lines = f.readlines()
            f.close()
            lineCount = 0
            while lineCount < len(lines):
                line = lines[lineCount]
                # strip comments
                line = line.split(";")[0]

                # ex:
                #     d 0x30bc inline fullName
                #     0x89 before 2 2
                #       this is a before comment
                #     <<<

                words = line.split()
                dataComment = False
                if len(words) > 1:
                    if words[0] == "d":
                        dataComment = True
                        del words[0]

                if len(words) > 1:
                    try:
                        codeAddr = atoi(words[0], 16)
                    except ValueError:
                        error_exit("couldn't get address in line %d of %s: %s" % (lineCount + 1, fname, line))
                    commentType = words[1]
                    useVariableSubstitution = False
                    if commentType[0] == "@":
                        useVariableSubstitution = True
                        commentType = commentType[1:]

                    if commentType == "inline":
                        if len(words) > 2:
                            comment = line[line.find(words[2]):].rstrip()
                            if useVariableSubstitution:
                                try:
                                    comment = self.substitute_variables(comment)
                                except ValueError:
                                    error_exit("couldn't substitute variable in line %d of %s: %s" % (lineCount + 1, fname, line))

                            if dataComment:
                                self.dataCommentsInline[codeAddr] = comment
                            else:
                                self.commentsInline[codeAddr] = comment
                    elif commentType == "before"  or  commentType == "after":
                        spaceBefore = 0
                        spaceAfter = 0
                        if len(words) > 2:
                            try:
                                spaceBefore = atoi(words[2])
                                if len(words) > 3:
                                    spaceAfter = atoi(words[3])
                            except ValueError:
                                error_exit("couldn't get space before or after value in line %d of %s: %s" % (lineCount + 1, fname, line))

                        if spaceBefore > 0  or spaceAfter > 0:
                            if commentType == "before":
                                if dataComment:
                                    self.dataCommentsBeforeSpacing[codeAddr] = [spaceBefore, spaceAfter]
                                else:
                                    self.commentsBeforeSpacing[codeAddr] = [spaceBefore, spaceAfter]
                            else:
                                if dataComment:
                                    self.dataCommentsAfterSpacing[codeAddr] = [spaceBefore, spaceAfter]
                                else:
                                    self.commentsAfterSpacing[codeAddr] = [spaceBefore, spaceAfter]
                        if commentType == "before":
                            if dataComment:
                                self.dataCommentsBefore[codeAddr] = []
                            else:
                                self.commentsBefore[codeAddr] = []
                        else:
                            if dataComment:
                                self.dataCommentsAfter[codeAddr] = []
                            else:
                                self.commentsAfter[codeAddr] = []

                        lineCount += 1
                        while lineCount < len(lines):
                            line = lines[lineCount]
                            if line[:-1] == "<<<":
                                break
                            else:
                                commentLine = line[:-1]
                                if useVariableSubstitution:
                                    try:
                                        commentLine = self.substitute_variables(commentLine)
                                    except ValueError:
                                        error_exit("couldn't substitute variable in line %d of %s: %s" % (lineCount + 1, fname, line))
                                if commentType == "before":
                                    if dataComment:
                                        self.dataCommentsBefore[codeAddr].append(commentLine)
                                    else:
                                        self.commentsBefore[codeAddr].append(commentLine)
                                else:
                                    if dataComment:
                                        self.dataCommentsAfter[codeAddr].append(commentLine)
                                    else:
                                        self.commentsAfter[codeAddr].append(commentLine)
                            lineCount += 1
                    else:
                        error_exit("invalid comment type in line %d of %s: %s" % (lineCount + 1, fname, line))

                lineCount += 1

    def parse_jump_table (self):
        if self.magic == QVM_MAGIC_VER1:
            return  # no jump table data
        count = 0
        while count < self.jumpTableLength:
            addr = struct.unpack("<L", self.jumpTableData[count:count+4])[0]
            self.jumpTableTargets.append(addr)
            count += 4

    def print_header (self):
        output("; magic 0x%x\n" % self.magic)
        output("; instruction count: 0x%x\n" % self.instructionCount)
        output("; CODE seg offset: 0x%08x  length: 0x%x\n" % (self.codeSegOffset, self.codeSegLength))
        output("; DATA seg offset: 0x%08x  length: 0x%x\n" % (self.dataSegOffset, self.dataSegLength))
        output("; LIT  seg offset: 0x%08x  length: 0x%x\n" % (self.litSegOffset, self.litSegLength))
        output("; BSS  seg offset: 0x%08x  length: 0x%x\n" % (self.bssSegOffset, self.bssSegLength))
        if self.magic != QVM_MAGIC_VER1:
            output("; jump table length: 0x%x\n" % (self.jumpTableLength))

    def print_code_disassembly (self):
        pos = 0

        count = -1
        currentFuncAddr = None
        while count < self.instructionCount - 1:
            count += 1

            comment = None
            opcStr = self.codeData[pos]
            opc = xord(opcStr)
            pos += 1
            name = opcodes[opc][OP_NAME]
            psize = opcodes[opc][OP_PARM_SIZE]

            if name != "enter"  and  count in self.commentsBefore:
                if count in self.commentsBeforeSpacing:
                    for i in range(self.commentsBeforeSpacing[count][0]):
                        output("\n")
                for line in self.commentsBefore[count]:
                    output("; %s\n" % line)
                if count in self.commentsBeforeSpacing:
                    for i in range(self.commentsBeforeSpacing[count][1]):
                        output("\n")

            if psize == 0:
                parm = None
            elif psize == 1:
                parmStr = self.codeData[pos]
                parm = xord(parmStr)
                pos += 1
            elif psize == 4:
                parmStr = self.codeData[pos : pos + psize]
                parm = struct.unpack("<l", parmStr)[0]
                pos += 4
            else:
                error_exit("FIXME bad opcode size")

            if count in self.jumpPoints:
                if count in self.jumpTableTargets:
                    output("\n;----------------------------------- *from ")
                else:
                    output("\n;----------------------------------- from ")

                for jp in self.jumpPoints[count]:
                    output(" 0x%x" % jp)
                output("\n")
            elif count in self.jumpTableTargets  and  count not in self.switchJumpPoints:
                output("\n;----------------------------------- table jump\n")

            if count in self.switchJumpPoints:
                if count in self.jumpTableTargets:
                    output("\n;----------------------------------- case *from ")
                else:
                    output("\n;----------------------------------- case from ")
                for jp in self.switchJumpPoints[count]:
                    output(" 0x%x(0x%x)" % (jp[0], jp[1]))
                output("\n")

            if name == "enter":
                addr = count
                currentFuncAddr = addr
                stackAdjust = parm
                if count in self.callPoints:
                    output("\n; called from")
                    for caller in self.callPoints[count]:
                        if caller in self.functions:
                            output(" %s()" % self.functions[caller])
                        elif self.functionHashes[caller] in self.baseQ3FunctionRevHashes:
                            for n in self.baseQ3FunctionRevHashes[self.functionHashes[caller]]:
                                output(" ?%s()" % n)
                        else:
                            output(" 0x%x" % caller)
                    output("\n")

                output("\n")

                if addr in self.functions:
                    output("; func %s()\n" % self.functions[count])
                elif self.functionHashes[addr] in self.baseQ3FunctionRevHashes:
                    output(";")
                    for n in self.baseQ3FunctionRevHashes[self.functionHashes[addr]]:
                        output(" ?%s()" % n)
                    output("\n")
                if addr in self.functionParmNum:
                    output(";")
                    p = self.functionParmNum[addr]
                    if p == 0:
                        output(" no")
                    elif p == -1:
                        output(" var")
                    else:
                        output(" 0x%x" % p)
                    output(" args\n")

                output("; max local arg 0x%x\n" % self.functionMaxArgsCalled[addr])
                output("; ========================\n")

                if count in self.commentsBefore:
                    if count in self.commentsBeforeSpacing:
                        for i in range(self.commentsBeforeSpacing[count][0]):
                            output("\n")
                    for line in self.commentsBefore[count]:
                        output("; %s\n" % line)
                    if count in self.commentsBeforeSpacing:
                        for i in range(self.commentsBeforeSpacing[count][1]):
                            output("\n")

            elif name == "local":
                if count in self.switchStartStatements:
                    output("; possible switch start\n")

                argNum = parm - stackAdjust - 0x8
                if argNum >= 0:
                    argstr = "arg%d" % (argNum / 4)
                    comment = argstr
                    if currentFuncAddr in self.functionsArgLabels:
                        if argstr in self.functionsArgLabels[currentFuncAddr]:
                            comment = comment + " : " + self.functionsArgLabels[currentFuncAddr][argstr]
                else:
                    if currentFuncAddr in self.functionsLocalLabels:
                        if parm in self.functionsLocalLabels[currentFuncAddr]:
                            comment = self.functionsLocalLabels[currentFuncAddr][parm]
                    elif currentFuncAddr in self.functionsLocalRangeLabels:
                        (match, matchSym, matchDiff, exactMatches) = self.find_in_symbol_range(parm, self.functionsLocalRangeLabels[currentFuncAddr])

                        if len(exactMatches) > 0:
                            comment =  ", ".join(exactMatches)
                        else:
                            if match != None:
                                comment = "%s + 0x%x" % (matchSym, matchDiff)
            elif name == "const":
                nextOp = xord(self.codeData[pos])

                if count in self.constants:
                    if parm != self.constants[count][1]:
                        comment = "FIXME constant val != to code val"
                    else:
                        comment = self.constants[count][0]

                elif parm >= self.dataSegLength  and  parm < self.dataSegLength + self.litSegLength  and  opcodes[nextOp][OP_NAME] not in ("call", "jump"):
                    output("\n  ; ")
                    self.print_lit_string(parm)
                    output("\n");
                elif parm >= 0  and  parm < self.dataSegLength  and  opcodes[nextOp][OP_NAME] not in ("call", "jump"):
                    b0 = xchr(self.dataData[parm])
                    b1 = xchr(self.dataData[parm + 1])
                    b2 = xchr(self.dataData[parm + 2])
                    b3 = xchr(self.dataData[parm + 3])

                    output("\n  ; %02x %02x %02x %02x  (0x%x)\n" % (xord(b0), xord(b1), xord(b2), xord(b3), struct.unpack("<L", self.dataData[parm:parm+4])[0]))

                    if parm in self.symbols:
                        comment = self.symbols[parm]
                    else:  # check symbol ranges
                        (match, matchSym, matchDiff, exactMatches) = self.find_in_symbol_range(parm, self.symbolsRange)

                        if len(exactMatches) > 0:
                            comment =  ", ".join(exactMatches)
                        else:
                            if match != None:
                                comment = "%s + 0x%x" % (matchSym, matchDiff)

                elif opcodes[nextOp][OP_NAME] == "call":
                    if parm < 0  and  parm in self.syscalls:
                        comment = "%s()" % self.syscalls[parm]
                    elif parm in self.functions:
                        comment = "%s()" % self.functions[parm]
                    elif parm in self.functionHashes:
                        if self.functionHashes[parm] in self.baseQ3FunctionRevHashes:
                            comment = ""
                            for n in self.baseQ3FunctionRevHashes[self.functionHashes[parm]]:
                                comment += " ?%s()" % n
                        else:
                            comment = ":unknown function:"

                elif parm >= self.dataSegLength  and  opcodes[nextOp][OP_NAME] not in ("call", "jump"):
                    # bss segment
                    #FIXME check that it doesn't go past??
                    if parm in self.symbols:
                        comment = self.symbols[parm]
                    else:  # check symbol ranges
                        exactMatches = []  #FIXME sorted
                        match = None
                        matchDiff = 0
                        matchSym = ""
                        matchRangeSize = 0
                        for rangeAddr in self.symbolsRange:
                            for r in self.symbolsRange[rangeAddr]:
                                size = r[0]
                                sym = r[1]
                                if parm == rangeAddr:
                                    exactMatches.append(sym)
                                elif parm >= rangeAddr  and  parm < (rangeAddr + size):
                                    if match == None:
                                        match = rangeAddr
                                        matchSym = sym
                                        matchDiff = parm - rangeAddr
                                        matchRangeSize = size
                                    elif (parm - rangeAddr) < matchDiff:
                                        match = rangeAddr
                                        matchSym = sym
                                        matchDiff = parm - rangeAddr
                                        matchRangeSize = size
                                    elif (parm - rangeAddr) == matchDiff:  # multiple ranges beginning at same address
                                        # pick smallest
                                        if size < matchRangeSize:
                                            match = rangeAddr
                                            matchSym = sym
                                            matchDiff = parm - rangeAddr
                                            matchRangeSize = size
                        if len(exactMatches) > 0:
                            comment =  ", ".join(exactMatches)
                        else:
                            if match != None:
                                comment = "%s + 0x%x" % (matchSym, matchDiff)
            elif name == "jump":
                if count in self.switchJumpStatements:
                    tmin = self.switchJumpStatements[count][0]
                    tmax = self.switchJumpStatements[count][1]
                    taddr = self.switchJumpStatements[count][2]
                    output("; possible switch jump: 0x%x (0x%x -> 0x%x)\n" % (taddr, tmin, tmax))

            sc = opcodes[opc][OP_STACK_CHANGE]
            if sc != 0  or parm != None:
                output("%08x  %-13s" % (count, name))
            else:
                output("%08x  %s" % (count, name))

            if sc < 0:
                output("  %d" % sc)
            elif sc > 0:
                output("   %d" % sc)
            else:
                if parm != None  or  comment  or count in self.commentsInline:
                    output("    ")

            if parm != None:
                if parm < 0:
                    output("  -0x%x" % -parm)
                else:
                    output("   0x%x" % parm)

            if comment:
                output("  ; %s" % comment)

            if count in self.commentsInline:
                output("  ; %s" % self.commentsInline[count])

            # finish printing line
            output("\n")

            if count in self.commentsAfter:
                if count in self.commentsAfterSpacing:
                    for i in range(self.commentsAfterSpacing[count][0]):
                        output("\n")
                for line in self.commentsAfter[count]:
                    output("; %s\n" % line)
                if count in self.commentsAfterSpacing:
                    for i in range(self.commentsAfterSpacing[count][1]):
                        output("\n")

    def print_data_disassembly (self):
        count = 0
        while count < self.dataSegLength:
            if count in self.dataCommentsBefore:
                if count in self.dataCommentsBeforeSpacing:
                    for i in range(self.dataCommentsBeforeSpacing[count][0]):
                        output("\n")
                for line in self.dataCommentsBefore[count]:
                    output("; %s\n" % line)
                if count in self.dataCommentsBeforeSpacing:
                    for i in range(self.dataCommentsBeforeSpacing[count][1]):
                        output("\n")

            output("0x%08x  " % count)
            b0 = self.dataData[count]
            b1 = self.dataData[count + 1]
            b2 = self.dataData[count + 2]
            b3 = self.dataData[count + 3]

            output(" %02x %02x %02x %02x    0x%x" % (xord(b0), xord(b1), xord(b2), xord(b3), struct.unpack("<L", self.dataData[count:count+4])[0]))
            if count in self.dataCommentsInline:
                output("  ; %s" % self.dataCommentsInline[count])

            # finish printing line
            output("\n")

            if count in self.dataCommentsAfter:
                if count in self.dataCommentsAfterSpacing:
                    for i in range(self.dataCommentsAfterSpacing[count][0]):
                        output("\n")
                for line in self.dataCommentsAfter[count]:
                    output("; %s\n" % line)
                if count in self.dataCommentsAfterSpacing:
                    for i in range(self.dataCommentsAfterSpacing[count][1]):
                        output("\n")

            count += 4

    def print_lit_disassembly (self):
        pos = self.dataSegLength
        offset = 0
        while offset < self.litSegLength:
            count = offset + pos
            if count in self.dataCommentsBefore:
                if count in self.dataCommentsBeforeSpacing:
                    for i in range(self.dataCommentsBeforeSpacing[count][0]):
                        output("\n")
                for line in self.dataCommentsBefore[count]:
                    output("; %s\n" % line)
                if count in self.dataCommentsBeforeSpacing:
                    for i in range(self.dataCommentsBeforeSpacing[count][1]):
                        output("\n")

            output("0x%08x  " % (offset + pos))
            self.print_lit_string(offset + self.dataSegLength)

            if count in self.dataCommentsInline:
                output("  ; %s" % self.dataCommentsInline[count])

            # finish printing line
            output("\n")

            # skip string data
            i = 0
            while 1:
                c = xord(self.litData[offset + i])
                if c == xord(b'\0')  or  offset + i >= self.litSegLength:
                    break
                i += 1
            offset += i

            if count in self.dataCommentsAfter:
                if count in self.dataCommentsAfterSpacing:
                    for j in range(self.dataCommentsAfterSpacing[count][0]):
                        output("\n")
                for line in self.dataCommentsAfter[count]:
                    output("; %s\n" % line)
                if count in self.dataCommentsAfterSpacing:
                    for j in range(self.dataCommentsAfterSpacing[count][1]):
                        output("\n")

            offset += 1

    def print_jump_table (self):
        count = 0
        while count < self.jumpTableLength:
            output("0x%08x  " % count)
            b0 = self.jumpTableData[count]
            b1 = self.jumpTableData[count + 1]
            b2 = self.jumpTableData[count + 2]
            b3 = self.jumpTableData[count + 3]

            output(" %02x %02x %02x %02x    0x%x" % (xord(b0), xord(b1), xord(b2), xord(b3), struct.unpack("<L", self.jumpTableData[count:count+4])[0]))

            # finish printing line
            output("\n")
            count += 4

    def compute_function_info (self):
        pos = 0
        funcStartInsNum = -1
        funcInsCount = 0
        funcOffset = 0
        funcHashSum = ""
        maxArgs = 0x8
        lastArg = 0x0

        opcStr = "\x00"
        opc = 0
        parmStr = "\x00"
        parm = 0

        prevOpcStr = "\x00"
        prevOpc = 0
        prevOpcParmStr = "\x00"
        prevOpcParm = 0

        # list of [opcodes, parameters] in this function
        funcOps = []

        ins = -1
        while ins < self.instructionCount - 1:
            ins += 1

            prevOpcStr = opcStr
            prevOpc = opc
            prevParmStr = parmStr
            prevParm = parm

            opcStr = xchr(self.codeData[pos])
            opc = xord(opcStr)
            funcInsCount += 1
            funcHashSum += "%d" % opc
            pos += 1
            name = opcodes[opc][OP_NAME]
            psize = opcodes[opc][OP_PARM_SIZE]
            if psize:
                parmStr = self.codeData[pos : pos + psize]
                if psize == 1:
                    parm = xord(parmStr)
                elif psize == 4:
                    parm = struct.unpack("<l", parmStr)[0]
                else:
                    parm = None
            else:
                parmStr = None
                parm = None
            pos += psize

            funcOps.append([opc, parm])

            if name == "const":
                if parm < 0:
                    funcHashSum += "%d" % parm
            elif name == "pop":
                lastArg = 0
            elif name == "local":
                funcHashSum += "%d" % parm
            elif name == "arg":
                if parm > maxArgs:
                    maxArgs = parm
                lastArg = parm
            elif name == "enter":
                if pos > 5:   # else it's first function of file  vmMain()
                    self.functionSizes[funcStartInsNum] = funcInsCount
                    h = hash32BitSigned(funcHashSum)
                    self.functionHashes[funcStartInsNum] = h
                    if h in self.functionRevHashes:
                        self.functionRevHashes[h].append(funcStartInsNum)
                    else:
                        self.functionRevHashes[h] = [funcStartInsNum]
                    self.functionMaxArgsCalled[funcStartInsNum] = maxArgs
                funcStartInsNum = ins
                funcOffset = pos - psize - 1
                funcInsCount = 1
                funcHashSum = ""
                maxArgs = 0x8
                lastArg = 0
                funcOps = []
            elif opcodes[opc][OP_NAME] == "jump":
                if opcodes[prevOpc][OP_NAME] == "const":
                    if prevParm in self.jumpPoints:
                        self.jumpPoints[prevParm].append(ins)
                    else:
                        self.jumpPoints[prevParm] = [ins]
                else:
                    # check for C switch jump table (16 ops)
                    #
                    #   switch { case 1: ...; break; case 2: ...; break; }
                    #
                    # implemented by q3asm as a list of jump addresses in
                    # the data segment

                    #
                    # local ...  ; switch value pointer, ex: 0x10
                    # load4
                    # const ...  ; min switch value, ex: 0x0
                    # lti ...    ; goto switch out of range, ex 0x1585
                    # local ...  ; switch value pointer, ex: 0x10
                    # load4
                    # const ...  ; max switch value, ex: 0x7
                    # gti ...    ; goto switch out of range, ex: 0x1585
                    # local ...  ; switch value pointer, ex: 0x10
                    # load4
                    # const 0x2
                    # lsh
                    # const ...  ; switch jump table address, ex: 0xa94
                    # add
                    # load4
                    # jump
                    if len(funcOps) >= 16:
                        if (
                            funcOps[-16][0] == OPC_LOCAL and
                            funcOps[-15][0] == OPC_LOAD4 and
                            funcOps[-14][0] == OPC_CONST and
                            funcOps[-13][0] == OPC_LTI and
                            funcOps[-12][0] == OPC_LOCAL and
                            funcOps[-11][0] == OPC_LOAD4 and
                            funcOps[-10][0] == OPC_CONST and
                            funcOps[-9][0] == OPC_GTI and
                            funcOps[-8][0] == OPC_LOCAL and
                            funcOps[-7][0] == OPC_LOAD4 and
                            funcOps[-6][0] == OPC_CONST and
                            funcOps[-5][0] == OPC_LSH and
                            funcOps[-4][0] == OPC_CONST and
                            funcOps[-3][0] == OPC_ADD and
                            funcOps[-2][0] == OPC_LOAD4
                        ):
                            tmin = funcOps[-14][1]
                            tmax = funcOps[-10][1]
                            taddr = funcOps[-4][1]

                            validValues = True
                            # validate values
                            if tmin < 0:
                                warning_msg("invalid min value for switch at 0x%x: %d" % (ins, tmin))
                                validValues = False
                            if tmax < 0:
                                warning_msg("invalid max value for switch at 0x%x: %d" % (ins, tmax))
                                validValues = False
                            if tmin > tmax:
                                warning_msg("min greater than max for switch at 0x%x: %d -> %d" % (ins, tmin, tmax))
                                validValues = False

                            minAddr = taddr + (tmin * 4)
                            if minAddr < 0  or  minAddr >= len(self.dataData):
                                warning_msg("invalid min switch address at 0x%x: 0x%x" % (ins, minAddr))
                                validValues = False

                            maxAddr = taddr + (tmax * 4)
                            if maxAddr < 0  or  maxAddr >= len(self.dataData):
                                warning_msg("invalid max switch address at 0x%x: 0x%x" % (ins, maxAddr))
                                validValues = False

                            #FIXME could also validate that minAddr and maxAddr fall within current function

                            if validValues:
                                self.switchStartStatements.append(ins - 15)
                                self.switchJumpStatements[ins] = [tmin, tmax, taddr]
                                for offset in range(tmin, tmax + 1):
                                    addr = struct.unpack("<L", self.dataData[taddr + (offset * 4): taddr + (offset * 4) + 4])[0]

                                    if addr < 0  or  addr >= len(self.codeData):
                                        warning_msg("invalid switch target address at 0x%x: 0x%x" % (ins, addr))
                                    else:
                                        if addr in self.switchJumpPoints:
                                            self.switchJumpPoints[addr].append([ins, offset])
                                        else:
                                            self.switchJumpPoints[addr] = [[ins, offset]]

            elif opcodes[opc][OP_JUMP_PARM]:
                if parm in self.jumpPoints:
                    self.jumpPoints[parm].append(ins)
                else:
                    self.jumpPoints[parm] = [ins]
            elif name == "call":
                if opcodes[prevOpc][OP_NAME] == "const":
                    if prevParm in self.callPoints:
                        self.callPoints[prevParm].append(funcStartInsNum)
                    else:
                        self.callPoints[prevParm] = [funcStartInsNum]
                    if prevParm in self.functionParmNum:
                        x = self.functionParmNum[prevParm]
                        if x != -1:
                            if x != lastArg:
                                self.functionParmNum[prevParm] = -1
                    else:
                        self.functionParmNum[prevParm] = lastArg

        self.functionSizes[funcStartInsNum] = funcInsCount
        h = hash32BitSigned(funcHashSum)
        self.functionHashes[funcStartInsNum] = h
        if h in self.functionRevHashes:
            self.functionRevHashes[h].append(funcStartInsNum)
        else:
            self.functionRevHashes[h] = [funcStartInsNum]
        self.functionMaxArgsCalled[funcStartInsNum] = maxArgs

    def print_function_hashes (self):
        ks = sorted(self.functionHashes.keys())

        for addr in ks:
            output("0x%08x  0x%x  %x" % (addr, self.functionSizes[addr], self.functionHashes[addr]))
            if self.functionHashes[addr] in self.baseQ3FunctionRevHashes:
                output("\tpossible match to")
                for n in self.baseQ3FunctionRevHashes[self.functionHashes[addr]]:
                    output(" %s" % n)
            output("\n")

    # Test opcode parsing code.  The byte string returned by this should equal
    # self.codeData[:].
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

    def print_lit_string (self, addr):
        offset = addr - self.dataSegLength
        i = 0
        lastCharPrintable = False
        while 1:
            c = xord(self.litData[offset + i])
            if c == xord(b'\0')  or  offset + i >= self.litSegLength:
                break

            # close previous quote if non-printable, or add quote if starting new printable sequence
            if c > 31  and  c < 127:
                if not lastCharPrintable:
                    if i != 0:  # no space if this starts everything
                        output(" ")
                    output("\"")
                lastCharPrintable = True
            else:  # not printable
                if lastCharPrintable:
                    output("\" ")
                lastCharPrintable = False

            if c > 31  and  c < 127:
                output(xchr(c))
            elif c == xord(b'\a'):
                output("\\a")
            elif c == xord(b'\b'):
                output("\\b")
            elif c == xord(b'\t'):
                output("\\t")
            elif c == xord(b'\n'):
                output("\\n")
            elif c == xord(b'\v'):
                output("\\v")
            elif c == xord(b'\f'):
                output("\\f")
            elif c == xord(b'\r'):
                output("\\r")
            else:
                output("\\x%02x" % c)

            i += 1

        if i == 0:
            output("\"\"")  # empty string
        elif lastCharPrintable:
            output("\"")  # close quote
