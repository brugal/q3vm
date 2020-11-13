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
from DecompileStack import DecompileStack
from LEBinFile import LEBinFile
from PythonCompat import atoi, xord, xchr

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

# detect hex or base 10, also explicitly require 0[xX] hex notation to make
# it easier to check if something is a number or a symbol.  Ex: c.isdigit()
def parse_int (s):
    # skip '+' and '-'
    if len(s) > 0  and  (s[0] == '+'  or  s[0] == '-'):
        st = s[1:]
    else:
        st = s

    if len(st) > 2  and  st[0] == '0'  and  (st[1] == 'x'  or  st[1] == 'X'):
        return atoi(s, 16)
    else:
        return atoi(s, 10)

def valid_symbol_name (s):
    if s == None  or len(s) == 0:
        return False
    c = s[0]
    if c.isdigit()  or  c == '+'  or  c == '-':
        return False
    if s == "void"  or  s in basicTypes:
        return False
    return True

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
TEMPLATES_DEFAULT_FILE = "templates-default.dat"
TEMPLATES_FILE = "templates.dat"

QVM_MAGIC_VER1 = 0x12721444
QVM_MAGIC_VER2 = 0x12721445

def output (msg):
    sys.stdout.write(msg)

SuppressWarnings = False

def warning_msg (msg):
    global SuppressWarnings
    if SuppressWarnings:
        return
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

OPCODE_NAME = 0
OPCODE_PARM_SIZE = 1
OPCODE_JUMP_PARM = 2
OPCODE_STACK_CHANGE = 3
OPCODE_DESC = 4  # from q3vm_specs.html and ioquake3 source code (2020-01-30)
OPCODE_C_CODE = 5  # 2020-02-16  q3 code/qcommon/vm_interpreted.c:  r2 = $PARM, r1 = NIS, r0 = TOS

opcodes = [ \
    ["undef", 0, False, 0, "undefined opcode.", ""],
    ["ignore", 0, False, 0, "no-operation (nop) instruction.", ""],
    ["break", 0, False, 0, "set debugging break point.", ""],
    ["enter", 4, False, 0, "Begin procedure body, adjust stack $PARM octets for frame (always at least 8 (i.e. 2 words)).  Frame contains all local storage/variables and arguments space for any calls within this procedure.", ""],  # establishes current stack so 0 relative change
    ["leave", 4, False, 0, "End procedure body, $PARM is same as that of the matching ENTER.", ""],
    ["call", 0, False, -1, "make call to procedure (code address <- TOS).", ""],  # call address is removed, but by convention the called function leaves a value on the stack
    ["push", 0, False, 1, "push nonsense (void) value to opstack (TOS <- 0).", ""],
    ["pop", 0, False, -1, "pop a value from stack (remove TOS, decrease stack by 1).", ""],
    ["const", 4, False, 1, "push literal value onto stack (TOS <- $PARM)", "r1 = r0;\nr0 = opStack[opStackOfs] = r2;"],
    ["local", 4, False, 1, "get address of local storage (local variable or argument) (TOS <- (frame + $PARM)).", "r1 = r0;\nr0 = opStack[opStackOfs] = r2+programStack;"],
    ["jump", 0, False, -1, "branch (code address <- TOS)", ""],
    ["eq", 4, True, -2, "check equality (signed integer) (compares NIS vs TOS, jump to $PARM if true).", "if ( r1 == r0 ) { programCounter = r2; }"],
    ["ne", 4, True, -2, "check inequality (signed integer) (NIS vs TOS, jump to $PARM if true).", "if ( r1 != r0 ) { programCounter = r2; }"],
    ["lti", 4, True, -2, "check less-than (signed integer) (NIS vs TOS, jump to $PARM if true).", "if ( r1 < r0 ) { programCounter = r2; }"],
    ["lei", 4, True, -2, "check less-than or equal-to (signed integer) (NIS vs TOS, jump to $PARM if true).", "if ( r1 <= r0 ) { programCounter = r2; }"],
    ["gti", 4, True, -2, "check greater-than (signed integer) (NIS vs TOS), jump to $PARM if true.", "if ( r1 > r0 ) { programCounter = r2; }"],
    ["gei", 4, True, -2, "check greater-than or equal-to (signed integer) (NIS vs TOS), jump to $PARM if true.", "if ( r1 >= r0 ) { programCounter = r2; }"],
    ["ltu", 4, True, -2, "check less-than (unsigned integer) (NIS vs TOS), jump to $PARM if true.", "if ( ((unsigned)r1) < ((unsigned)r0) ) { programCounter = r2; }"],
    ["leu", 4, True, -2, "check less-than or equal-to (unsigned integer) (NIS vs TOS), jump to $PARM if true.", "if ( ((unsigned)r1) <= ((unsigned)r0) ) { programCounter = r2; }\n"],
    ["gtu", 4, True, -2, "check greater-than (unsigned integer) (NIS vs TOS), jump to $PARM if true.", "if ( ((unsigned)r1) > ((unsigned)r0) ) { programCounter = r2; }\n"],
    ["geu", 4, True, -2, "check greater-than or equal-to (unsigned integer) (NIS vs TOS), jump to $PARM if true.", "if ( ((unsigned)r1) >= ((unsigned)r0) ) { programCounter = r2; }"],
    ["eqf", 4, True, -2, "check equality (float) (NIS vs TOS, jump to $PARM if true).", "if(((float *) opStack)[(uint8_t) (opStackOfs + 1)] == ((float *) opStack)[(uint8_t) (opStackOfs + 2)]) { programCounter = r2; }"],
    ["nef", 4, True, -2, "check inequality (float) (NIS vs TOS, jump to $PARM if true).", "if(((float *) opStack)[(uint8_t) (opStackOfs + 1)] != ((float *) opStack)[(uint8_t) (opStackOfs + 2)]) { programCounter = r2; }"],
    ["ltf", 4, True, -2, "check less-than (float) (NIS vs TOS, jump to $PARM if true).", "if(((float *) opStack)[(uint8_t) (opStackOfs + 1)] < ((float *) opStack)[(uint8_t) (opStackOfs + 2)]) { programCounter = r2; }"],
    ["lef", 4, True, -2, "check less-than or equal-to (float) (NIS vs TOS, jump to $PARM if true).", "if(((float *) opStack)[(uint8_t) ((uint8_t) (opStackOfs + 1))] <= ((float *) opStack)[(uint8_t) ((uint8_t) (opStackOfs + 2))]) { programCounter = r2; }"],
    ["gtf", 4, True, -2, "check greater-than (float) (NIS vs TOS, jump to $PARM if true).", "if(((float *) opStack)[(uint8_t) (opStackOfs + 1)] > ((float *) opStack)[(uint8_t) (opStackOfs + 2)]) { programCounter = r2; }"],
    ["gef", 4, True, -2, "check greater-than or equal-to (float) (NIS vs TOS, jump to $PARM if true).", "if(((float *) opStack)[(uint8_t) (opStackOfs + 1)] >= ((float *) opStack)[(uint8_t) (opStackOfs + 2)]) { programCounter = r2; }"],
    ["load1", 0, False, 0, "Load 1-octet value from address in TOS (TOS <- [TOS])", "r0 = opStack[opStackOfs] = image[ r0 & dataMask ];"],
    ["load2", 0, False, 0, "Load 2-octet value from address in TOS (TOS <- [TOS])", "r0 = opStack[opStackOfs] = *(unsigned short *)&image[ r0 & dataMask ];"],
    ["load4", 0, False, 0, "Load 4-octet value from address in TOS (TOS <- [TOS])", "r0 = opStack[opStackOfs] = *(int *) &image[ r0 & dataMask ];"],
    ["store1", 0, False, -2, "lowest octet of TOS is 1-octet value to store, destination address in next-in-stack ([NIS] <- TOS).", "image[ r1 & dataMask ] = r0;"],
    ["store2", 0, False, -2, "lowest two octets of TOS is 2-octet value to store, destination address in next-in-stack ([NIS] <- TOS).", "*(short *)&image[ r1 & dataMask ] = r0;"],
    ["store4", 0, False, -2, "TOS is 4-octet value to store, destination address in next-in-stack ([NIS] <- TOS).", "*(int *)&image[ r1 & dataMask ] = r0;"],
    ["arg", 1, False, -1, "TOS is 4-octet value to store into arguments-marshalling space of the indicated octet offset (ARGS[offset] <- TOS).", "*(int *)&image[ (codeImage[programCounter] + programStack) & dataMask ] = r0;"],
    ["block_copy", 4, False, -2, "copy $PARM bytes from TOS into NIS.", "VM_BlockCopy(r1, r0, r2);"],  # q3vm_specs.html wrong about parameter size
    ["sex8", 0, False, 0, "Sign-extend 8-bit (TOS <- TOS).", "opStack[opStackOfs] = (signed char) opStack[opStackOfs];"],
    ["sex16", 0, False, 0, "Sign-extend 16-bit (TOS <- TOS).", "opStack[opStackOfs] = (short) opStack[opStackOfs];"],
    ["negi", 0, False, 0, "Negate signed integer (TOS <- -TOS).", "opStack[opStackOfs] = -r0;"],
    ["add", 0, False, -1, "Add integer-wise (TOS <- NIS + TOS).", "opStack[opStackOfs] = r1 + r0;"],
    ["sub", 0, False, -1, "Subtract integer-wise (TOS <- NIS - TOS).", "opStack[opStackOfs] = r1 - r0;"],
    ["divi", 0, False, -1, "Divide integer-wise (TOS <- NIS / TOS).", "opStack[opStackOfs] = r1 / r0;"],
    ["divu", 0, False, -1, "Divide unsigned integer (TOS <- NIS / TOS).", "opStack[opStackOfs] = ((unsigned) r1) / ((unsigned) r0);"],
    ["modi", 0, False, -1, "Modulo (signed integer) (TOS <- NIS mod TOS).", "opStack[opStackOfs] = r1 % r0;"],
    ["modu", 0, False, -1, "Modulo (unsigned integer) (TOS <- NIS mod TOS).", "opStack[opStackOfs] = ((unsigned) r1) % ((unsigned) r0);"],
    ["muli", 0, False, -1, "Multiply (signed integer) (TOS <- NIS * TOS).", "opStack[opStackOfs] = r1 * r0;"],
    ["mulu", 0, False, -1, "Multiply (unsigned integer) (TOS <- NIS * TOS).", "opStack[opStackOfs] = ((unsigned) r1) * ((unsigned) r0);"],
    ["band", 0, False, -1, "Bitwise AND (TOS <- NIS & TOS).", "opStack[opStackOfs] = ((unsigned) r1) & ((unsigned) r0);"],
    ["bor", 0, False, -1, "Bitwise OR (TOS <- NIS | TOS).", "opStack[opStackOfs] = ((unsigned) r1) | ((unsigned) r0);"],
    ["bxor", 0, False, -1, "Bitwise XOR (TOS <- NIS ^ TOS).", "opStack[opStackOfs] = ((unsigned) r1) ^ ((unsigned) r0);"],
    ["bcom", 0, False, 0, "Bitwise complement (TOS <- ~TOS).", "opStack[opStackOfs] = ~((unsigned) r0);"],
    ["lsh", 0, False, -1, "Bitwise left-shift (TOS <- NIS << TOS).", "opStack[opStackOfs] = r1 << r0;"],
    ["rshi", 0, False, -1, "Algebraic (signed) right-shift (TOS <- NIS >> TOS).", "opStack[opStackOfs] = r1 >> r0;"],
    ["rshu", 0, False, -1, "Bitwise (unsigned) right-shift (TOS <- NIS >> TOS).", "opStack[opStackOfs] = ((unsigned) r1) >> r0;"],
    ["negf", 0, False, 0, "Negate float value (TOS <- -TOS).", "((float *) opStack)[opStackOfs] =  -((float *) opStack)[opStackOfs];"],
    ["addf", 0, False, -1, "Add floats (TOS <- NIS + TOS).", "((float *) opStack)[opStackOfs] = ((float *) opStack)[opStackOfs] + ((float *) opStack)[(uint8_t) (opStackOfs + 1)];"],
    ["subf", 0, False, -1, "Subtract floats (TOS <- NIS - TOS).", "((float *) opStack)[opStackOfs] = ((float *) opStack)[opStackOfs] - ((float *) opStack)[(uint8_t) (opStackOfs + 1)];"],
    ["divf", 0, False, -1, "Divide floats (TOS <- NIS / TOS).", "((float *) opStack)[opStackOfs] = ((float *) opStack)[opStackOfs] / ((float *) opStack)[(uint8_t) (opStackOfs + 1)];"],
    ["mulf", 0, False, -1, "Multiply floats (TOS <- NIS x TOS).", "((float *) opStack)[opStackOfs] = ((float *) opStack)[opStackOfs] * ((float *) opStack)[(uint8_t) (opStackOfs + 1)];"],
    ["cvif", 0, False, 0, "Convert signed integer to float (TOS <- TOS).", "((float *) opStack)[opStackOfs] = (float) opStack[opStackOfs];"],
    ["cvfi", 0, False, 0, "Convert float to signed integer (TOS <- TOS).", "opStack[opStackOfs] = Q_ftol(((float *) opStack)[opStackOfs]);"]
]


(
OP_UNDEF,

OP_IGNORE,

OP_BREAK,

OP_ENTER,
OP_LEAVE,
OP_CALL,
OP_PUSH,
OP_POP,

OP_CONST,
OP_LOCAL,

OP_JUMP,

OP_EQ,
OP_NE,

OP_LTI,
OP_LEI,
OP_GTI,
OP_GEI,

OP_LTU,
OP_LEU,
OP_GTU,
OP_GEU,

OP_EQF,
OP_NEF,

OP_LTF,
OP_LEF,
OP_GTF,
OP_GEF,

OP_LOAD1,
OP_LOAD2,
OP_LOAD4,
OP_STORE1,
OP_STORE2,
OP_STORE4,
OP_ARG,

OP_BLOCK_COPY,

OP_SEX8,
OP_SEX16,

OP_NEGI,
OP_ADD,
OP_SUB,
OP_DIVI,
OP_DIVU,
OP_MODI,
OP_MODU,
OP_MULI,
OP_MULU,

OP_BAND,
OP_BOR,
OP_BXOR,
OP_BCOM,

OP_LSH,
OP_RSHI,
OP_RSHU,

OP_NEGF,
OP_ADDF,
OP_SUBF,
OP_DIVF,
OP_MULF,

OP_CVIF,
OP_CVFI ) = range(60)

# in qvms double and long types are still only 4 bytes
basicTypes = ("byte", "char", "uchar", "short", "ushort", "int", "uint", "float")

SYMBOL_RANGE = 0  # size specified directly
SYMBOL_TEMPLATE = 1
SYMBOL_POINTER_VOID = 2
SYMBOL_POINTER_BASIC = 3  # pointer to basic type
SYMBOL_POINTER_TEMPLATE = 4
# basic types
SYMBOL_BYTE = 5  # unsigned char
SYMBOL_CHAR = 6
SYMBOL_UCHAR = 7
SYMBOL_SHORT = 8
SYMBOL_USHORT = 9
SYMBOL_INT = 10
SYMBOL_UINT = 11
SYMBOL_FLOAT = 12

class ArraySize:
    def __init__ (self, value, name=None):
        self.value = value
        self.name = name

class RangeException(Exception):
    pass

class RangeElement:
    def __init__ (self, size=0, symbolName="", symbolType=SYMBOL_RANGE, isPointer=False, pointerType="", pointerDepth=0, isArray=False, arrayLevels=[], arrayTemplate="", arrayElementSize=0):
        self.size = size;
        self.symbolName = symbolName

        # templates should have been expanded by the time they are added as ranges
        if symbolType == SYMBOL_TEMPLATE  and  not isArray:
            raise RangeException("non-array range element created with template symbol")

        self.symbolType = symbolType
        self.isPointer = isPointer
        # note this is the string name of the type, overriding that type will use the new setting even in previously defined templates
        self.pointerType = pointerType
        self.pointerDepth = pointerDepth

        self.isArray = isArray
        self.arrayLevels = arrayLevels  # [size1:ArraySize, size2:ArraySize, ...]
        self.arrayTemplate = arrayTemplate  # '' if basic type or pointer
        self.arrayElementSize = arrayElementSize

        # turn arrays into ranges
        if isArray:
            self.symbolType = SYMBOL_RANGE

class TemplateMember:
    def __init__ (self, offset=0, size=0, name="", symbolType=SYMBOL_RANGE, isPointer=False, pointerType="", pointerDepth=0, parentTemplatesInfo=[], isArray=False, arrayLevels=[], arrayTemplate="", arrayElementSize=0, aliasUsed=False, origName=""):
        self.offset = offset
        self.size = size
        self.name = name
        self.symbolType = symbolType
        self.isPointer = isPointer
        self.pointerType = pointerType
        self.pointerDepth = pointerDepth

        self.isArray = isArray
        self.arrayLevels = arrayLevels  # [size1:ArraySize, size2:ArraySize, ...]
        self.arrayTemplate = arrayTemplate
        self.arrayElementSize = arrayElementSize

        # for debugging
        self.aliasUsed = aliasUsed
        self.origName = origName  # without alias expanded

        # info with respect to parent templates
        self.parentTemplatesInfo = parentTemplatesInfo  # [ [parentTemplate1:str, name1:str, offset1:int, isTemplateRange1:bool, ourTemplate1:str], [parentTemplate2:str, name2:str, offset2:int, isTemplateRange2:bool, ourTemplate2:str], ... ]

class AliasInfo:
    def __init__ (self, name, declaration, expansion):
        self.name = name
        self.declaration = declaration
        self.expansion = expansion

class ForwardDeclaration:
    def __init__ (self, symbolName, lineCount, fname, line):
        self.symbolName = symbolName
        self.lineCount = lineCount
        self.fname = fname
        self.line = line

class Template:
    def __init__ (self, size, paddingSize, paddingUsed, members=[]):
        self.size = size
        self.paddingSize = paddingSize
        self.paddingUsed = paddingUsed
        self.members = members  # [ member1:TemplateMember, member2:TemplateMember, ... ]

class TemplateManager:
    def __init__ (self):
        self.symbolTemplates = {}  # name:str -> template:Template
        self.arrayConstants = {}  # name:str -> value:int
        self.templateAliases = {}  # name:str -> sub:AliasInfo
        self.forwardDeclarations = []  # [ declaration1:ForwardDeclaration ... ]

    def pad_up (self, offset, paddingSize):
        if paddingSize < 0:
            error_exit("invalid padding size: %d" % paddingSize)
        if paddingSize == 0:
            return offset
        if offset % paddingSize == 0:
            return offset
        return (offset + paddingSize) - (offset % paddingSize)

    def check_for_template_alias (self, typeString):
        s = typeString

        pdEnd = 0
        for c in s:
            if c == '*':
                pdEnd += 1
            else:
                break

        if pdEnd > 0:
            pointerDeclaration = s[:pdEnd]
            s = s[pdEnd:]
        else:
            pointerDeclaration = ""

        symEnd = 0
        for c in s:
            if c != '[':
                symEnd += 1
            else:
                break

        if symEnd > 0:
            symbolDeclaration = s[:symEnd]
            s = s[symEnd:]
        else:
            symbolDeclaration = ""

        arrayDeclaration = s

        if symbolDeclaration in self.templateAliases:
            symbolDeclaration = self.templateAliases[symbolDeclaration].expansion
            aliasUsed = True
        else:
            aliasUsed = False

        s = pointerDeclaration + symbolDeclaration + arrayDeclaration

        #print("xxxxxx   %s   ->   %s" % (s, symbolDeclaration))
        return (aliasUsed, s)


    def check_for_array_declaration (self, typeString):
        isArray = False
        arrayLevels = []
        isValid = True

        name = typeString

        # ex: 'matrix[3][6]'  -> ['matrix', '3]', '6]']
        match = typeString.split('[')

        if len(match) == 1:  # ex: ['float']
            return (True, typeString, False, [])

        isArray = True
        for m in match[1:]:
            # check for invalid or unsupported declarations
            # ex: nested array 'hello[11[22]]' -> ['hello', '11', '22]]']
            if m[-1] != ']':
                isValid = False
                break
            m = m[:-1]
            if ']' in m:
                isValid = False
                break

            name = None

            if m in self.arrayConstants:
                name = m
                size = self.arrayConstants[m]
            else:
                try:
                    size = parse_int(m)
                except ValueError:
                    isValid = False
                    break

            if size < 0:
                isValid = False
                break

            arrayLevels.append(ArraySize(size, name=name))

        return (isValid, match[0], isArray, arrayLevels)

    def parse_symbol_or_size (self, words, lineCount, fname, line, currentParsingTemplate=None):
        # currently only checks words[0] but could potentially allow spaces
        # for pointer or array declarations

        def ferror_exit (msg):
            error_exit("%s in line %d of %s: %s" % (msg, lineCount + 1, fname, line))

        size = 0
        template = None
        symbolType = SYMBOL_RANGE
        isPointer = False
        pointerType = ""
        pointerDepth = 0
        isArray = False
        arrayLevels = []  # ex: [ArraySize(3), ArraySize(3)] for float[3][3]
        arrayElementSize = 0
        aliasUsed = False

        word = words[0]
        firstChar = word[0]
        if firstChar.isdigit()  or  firstChar in ('+', '-'):
            try:
                size = parse_int(word)
            except ValueError:
                ferror_exit("couldn't parse size")
            if size < 0:
                ferror_exit("invalid size")
        else:  # template or basic type
            # check for aliases
            (aliasUsed, word) = self.check_for_template_alias(word)

            # check for array

            # Note: pointer to array isn't supported, if both pointer and
            # array declarations are used it will be array of pointers
            (isValid, word, isArray, arrayLevels) = self.check_for_array_declaration(word)
            if not isValid:
                ferror_exit("invalid array declaration")

            # check for pointer and pointer depth
            wlen = len(word)
            for i in range(wlen):
                if word[i] == '*':
                    isPointer = True
                    pointerDepth += 1
                else:
                    break

            if isPointer:
                w = word[i:]
                pointerType = w
                symbolType = SYMBOL_POINTER_TEMPLATE
                if pointerType == "void":
                    symbolType = SYMBOL_POINTER_VOID
                elif pointerType in basicTypes:
                    symbolType = SYMBOL_POINTER_BASIC
                else:
                    if not valid_symbol_name(pointerType):
                        ferror_exit("invalid pointer name")
                    # check that it exists or is the current template being parsed
                    if pointerType not in self.symbolTemplates  and  pointerType != currentParsingTemplate:
                        #ferror_exit("unknown pointer type")
                        # check later
                        self.forwardDeclarations.append(ForwardDeclaration(pointerType, lineCount, fname, line))
                    symbolType = SYMBOL_POINTER_TEMPLATE
                size = 0x4
            else:  # template or basic type
                w = word
                if w == "byte":
                    symbolType = SYMBOL_BYTE
                    size = 0x1
                elif w == "char":
                    symbolType = SYMBOL_CHAR
                    size = 0x1
                elif w == "uchar":
                    symbolType = SYMBOL_UCHAR
                    size = 0x1
                elif w == "short":
                    symbolType = SYMBOL_SHORT
                    size = 0x2
                elif w == "ushort":
                    symbolType = SYMBOL_USHORT
                    size = 0x2
                elif w == "int":
                    symbolType = SYMBOL_INT
                    size = 0x4
                elif w == "uint":
                    symbolType = SYMBOL_UINT
                    size = 0x4
                elif w == "float":
                    symbolType = SYMBOL_FLOAT
                    size = 0x4
                else:
                    symbolType = SYMBOL_TEMPLATE
                    template = w
                    if not valid_symbol_name(template):
                        ferror_exit("invalid template name")
                    if template not in self.symbolTemplates:
                        ferror_exit("parsed unknown template")
                    size = self.symbolTemplates[template].size

        if isArray:
            arrayElementSize = size
            for a in arrayLevels:
                size *= a.value

        return (size, symbolType, template, isPointer, pointerType, pointerDepth, isArray, arrayLevels, arrayElementSize, aliasUsed)

    def load_symbol_templates_file (self, fname, allowOverride=False):
        # ex:
        # vmCvar_t 0x110
        # {
        #   0x0 0x4 handle
        #   0x4 0x4 modificationCount
        #   ...
        # }

        def ferror_exit (msg):
            error_exit("%s in line %d of %s: %s" % (msg, lineCount + 1, fname, line))
        def fwarning_msg (msg):
            warning_msg("%s in line %d of %s: %s" % (msg, lineCount + 1, fname, line))

        f = open(fname)
        lines = f.readlines()
        f.close()
        lineCount = 0
        haveTemplateInfo = False
        skipOpeningBrace = False
        for line in lines:
            # strip comments and trailing/ending whitespace
            line = line.split(";")[0]
            line = line.strip()
            words = line.split()

            # skip empty lines
            if len(words) == 0:
                lineCount += 1
                continue

            if haveTemplateInfo  and  skipOpeningBrace:
                if len(words) != 1  or  words[0] != "{":
                    ferror_exit("invalid opening brace")
                skipOpeningBrace = False
                lineCount += 1
                continue

            if not haveTemplateInfo:
                if words[0] == "%alias":
                    if len(words) != 3:
                        ferror_exit("invalid alias declaration")
                    aliasString = words[1]
                    aliasName = words[2]
                    if not valid_symbol_name(aliasName):
                        ferror_exit("invalid alias name")

                    if aliasName in self.symbolTemplates:
                        ferror_exit("template exists with same name")

                    if not allowOverride  and  aliasName in self.templateAliases:
                        ferror_exit("alias already exists")

                    # expand other possible alias reference
                    (aliasUsed, aliasString) = self.check_for_template_alias(aliasString)

                    self.templateAliases[aliasName] = AliasInfo(name=aliasName, declaration=words[1], expansion=aliasString)
                    lineCount += 1
                    continue

                if words[0] == "%arrayConstant":
                    if len(words) != 3:
                        ferror_exit("invalid array constant declaration")
                    cname = words[1]
                    c = cname[0]
                    if c.isdigit()  or  c == '+'  or  c == '-':
                        ferror_exit("invalid array constant name")
                    try:
                        cvalue = parse_int(words[2])
                    except ValueError:
                        ferror_exit("couldn't parse array constant value")

                    if not allowOverride  and  cname in self.arrayConstants:
                        ferror_exit("array constant already exists")

                    self.arrayConstants[cname] = cvalue
                    lineCount += 1
                    continue

                # getting template info

                # size and opening brace optional, ex:  sx_t 0x100 {
                haveTemplateSize = False
                parseTemplateSize = False

                if len(words) == 1:
                    # just name
                    pass
                elif len(words) == 2:
                    # name plus size or opening brace
                    if words[1] != "{":
                        parseTemplateSize = True
                elif len(words) == 3:
                    # name plus size plus opening brace
                    parseTemplateSize = True
                else:
                    ferror_exit("invalid word count in template declaration")

                templateName = words[0]
                if not valid_symbol_name(templateName):
                    ferror_exit("invalid template name")

                if templateName in self.templateAliases:
                    ferror_exit("alias exists with same name")

                if not allowOverride  and  templateName in self.symbolTemplates:
                    ferror_exit("template already exists")

                if parseTemplateSize:
                    try:
                        templateSize = parse_int(words[1])
                    except ValueError:
                        ferror_exit("couldn't parse template size")
                    if templateSize < 0:
                        ferror_exit("invalid template size")
                    haveTemplateSize = True

                haveTemplateInfo = True

                if words[-1] == "{":
                    skipOpeningBrace = False
                else:
                    skipOpeningBrace = True

                paddingSize = 0
                currentOffset = 0
                memberList = []
                lineCount += 1
                continue

            # parsing template at this point

            if words[0] == "}":
                if len(words) != 1:
                    ferror_exit("invalid closing brace")

                paddingUsed = 0
                if not haveTemplateSize:
                    templateSize = 0
                    if len(memberList) > 0:
                        m = memberList[-1]
                        ts = m.offset + m.size
                        templateSize = self.pad_up(ts, paddingSize)
                        paddingUsed = templateSize - ts

                self.symbolTemplates[templateName] = Template(size=templateSize, paddingSize=paddingSize, paddingUsed=paddingUsed, members=memberList)
                lineCount += 1
                haveTemplateInfo = False
                continue

            # parsing members (offset optional), ex:  '0x0 0x4 handle'  or  'int count'

            if len(words) not in (2, 3):
                ferror_exit("invalid word count in member declaration")

            haveOffset = False
            symbolIndex = 1

            if len(words) == 3:
                try:
                    memberOffset = parse_int(words[0])
                except ValueError:
                    ferror_exit("couldn't get member offset")
                if memberOffset < 0:
                    ferror_exit("invalid offset")
                haveOffset = True
                symbolIndex = 1
            else:  # len(words) == 2
                haveOffset = False
                symbolIndex = 0

            (memberSize, memberSymbolType, memberTemplate, memberIsPointer, memberPointerType, memberPointerDepth, memberIsArray, memberArrayLevels, memberArrayElementSize, memberAliasUsed) = self.parse_symbol_or_size(words[symbolIndex:], lineCount, fname, line, currentParsingTemplate=templateName)

            memberName = words[symbolIndex + 1]
            if not valid_symbol_name(memberName):
                ferror_exit("invalid member name")
            # make sure name is unique
            for m in memberList:
                if m.name == memberName:
                    ferror_exit("duplicate member name")

            if memberTemplate  and  not memberIsArray:
                memberTemplateSize = self.symbolTemplates[memberTemplate].size
                if self.symbolTemplates[memberTemplate].paddingSize > paddingSize:
                    paddingSize = self.symbolTemplates[memberTemplate].paddingSize
                if not haveOffset:
                    memberOffset = self.pad_up(currentOffset, self.symbolTemplates[memberTemplate].paddingSize)
                    haveOffset = True

                memberTemplateMembers = self.symbolTemplates[memberTemplate].members
                # add member template itself
                memberList.append(TemplateMember(offset=memberOffset, size=memberTemplateSize, name=memberName, parentTemplatesInfo=[[templateName, memberName, memberOffset, True, memberTemplate]], aliasUsed=memberAliasUsed, origName=words[1]))
                # check if it overrides, only need to check previous member if
                # there's also a check that members are added in order
                if len(memberList) > 1:
                    prevMember = memberList[-2]
                    if memberOffset < prevMember.offset:
                        fwarning_msg("member template '%s' out of order" % memberName)
                    elif memberOffset < (prevMember.offset + prevMember.size):
                        fwarning_msg("member template '%s' overrides previous member" % memberName)

                for m in memberTemplateMembers:
                    adjOffset = memberOffset + m.offset

                    ptinfo = m.parentTemplatesInfo[:]
                    # ptinfo[-1][3] : keep specifying that it's the range for entire template, also keep the template name
                    ptinfo.append([templateName, "%s.%s" % (memberName, m.name), m.offset, ptinfo[-1][3], ptinfo[-1][4]])

                    # don't need to check for override or order since this is a previously defined template
                    memberList.append(TemplateMember(offset=adjOffset, size=m.size, name="%s.%s" % (memberName, m.name), symbolType=m.symbolType, isPointer=m.isPointer, pointerType=m.pointerType, pointerDepth=m.pointerDepth, parentTemplatesInfo=ptinfo[:], isArray=m.isArray, arrayLevels=m.arrayLevels, arrayTemplate=m.arrayTemplate, arrayElementSize=m.arrayElementSize, aliasUsed=m.aliasUsed, origName=m.origName))

                currentOffset += memberTemplateSize
            else:  # basic type, range, pointer, or array
                # padding check
                psize = 4
                msymt = memberSymbolType

                if msymt == SYMBOL_RANGE:
                    psize = 0
                elif msymt in (SYMBOL_BYTE, SYMBOL_CHAR, SYMBOL_UCHAR):
                    psize = 1
                elif msymt in (SYMBOL_SHORT, SYMBOL_USHORT):
                    psize = 2
                elif msymt == SYMBOL_TEMPLATE:  # it is array of templates, straight templates handled before
                    psize = self.symbolTemplates[memberTemplate].paddingSize

                if psize > paddingSize:
                    paddingSize = psize

                if not haveOffset:
                    memberOffset = self.pad_up(currentOffset, psize)
                    currentOffset = memberOffset
                    haveOffset = True
                else:
                    currentOffset = memberOffset

                memberList.append(TemplateMember(offset=memberOffset, size=memberSize, name=memberName, symbolType=memberSymbolType, isPointer=memberIsPointer, pointerType=memberPointerType, pointerDepth=memberPointerDepth, parentTemplatesInfo=[[templateName, memberName, memberOffset, False, ""]], isArray=memberIsArray, arrayLevels=memberArrayLevels, arrayTemplate=memberTemplate, arrayElementSize=memberArrayElementSize, aliasUsed=memberAliasUsed, origName=words[1]))

                # check if it overrides, only need to check previous member if
                # there's also a check that members are added in order
                if len(memberList) > 1:
                    prevMember = memberList[-2]
                    if memberOffset < prevMember.offset:
                        fwarning_msg("member '%s' out of order" % memberName)
                    elif memberOffset < (prevMember.offset + prevMember.size):
                        fwarning_msg("member '%s' overrides previous member" % memberName)

                currentOffset += memberSize
            lineCount += 1

        if haveTemplateInfo:
            # never finished parsing last template
           ferror_exit("last template not closed")

        # check that forward declarations exist
        for d in self.forwardDeclarations:
            if d.symbolName not in self.symbolTemplates:
                error_exit("undefined declaration %s in line %d of %s: %s" % (d.symbolName, d.lineCount + 1, d.fname, d.line))

    def load_default_templates (self):
        fname = TEMPLATES_DEFAULT_FILE
        if os.path.exists(fname):
            # override default one
            self.load_symbol_templates_file(fname, allowOverride=False)
        else:
            fname = os.path.join(BASE_DIR, TEMPLATES_DEFAULT_FILE)
            if os.path.exists(fname):
                self.load_symbol_templates_file(fname, allowOverride=False)

        fname = TEMPLATES_FILE
        if os.path.exists(fname):
            self.load_symbol_templates_file(fname, allowOverride=True)


class InvalidQvm(Exception):
    pass

class Qvm:

    # qvmType:("cgame", "game", "ui", None)
    def __init__ (self, qvmFileName, qvmType=None):
        qvmFile = LEBinFile(qvmFileName)

        self.magic = qvmFile.read_int()
        if self.magic != QVM_MAGIC_VER1  and  self.magic != QVM_MAGIC_VER2:
            qvmFile.close()
            raise InvalidQvm("not a valid qvm file, magic 0x%x != (0x%x | 0x%x)" % (self.magic, QVM_MAGIC_VER1, QVM_MAGIC_VER2))

        # q3vm_specs.html wrong about header, it's offset and then length

        self.instructionCount = qvmFile.read_int()
        self.codeSegOffset = qvmFile.read_int()
        self.codeSegLength = qvmFile.read_int()
        self.dataSegOffset = qvmFile.read_int()
        self.dataSegLength = qvmFile.read_int()
        self.litSegOffset = self.dataSegOffset + self.dataSegLength
        self.litSegLength = qvmFile.read_int()
        self.bssSegOffset = self.dataSegOffset + self.dataSegLength + self.litSegLength
        self.bssSegLength = qvmFile.read_int()

        if self.magic != QVM_MAGIC_VER1:
            self.jumpTableOffset = self.litSegOffset + self.litSegLength
            self.jumpTableLength = qvmFile.read_int()
        else:
            self.jumpTableLength = 0

        # validate header values
        if self.instructionCount < 0:
            qvmFile.close()
            raise InvalidQvm("bad header: instructionCount %d" % self.instructionCount)
        if self.codeSegOffset < 0:
            qvmFile.close()
            raise InvalidQvm("bad header: codeSegOffset %d" % self.codeSegOffset)
        if self.codeSegLength < 0:
            qvmFile.close()
            raise InvalidQvm("bad header: codeSegLength %d" % self.codeSegLength)
        if self.dataSegOffset < 0:
            qvmFile.close()
            raise InvalidQvm("bad header: dataSegOffset %d" % self.dataSegOffset)
        if self.dataSegLength < 0:
            qvmFile.close()
            raise InvalidQvm("bad header: dataSegLength %d" % self.dataSegLength)
        if self.litSegLength < 0:
            qvmFile.close()
            raise InvalidQvm("bad header: litSegLength %d" % self.litSegLength)
        if self.bssSegLength < 0:
            qvmFile.close()
            raise InvalidQvm("bad header: bssSegLength %d" % self.bssSegLength)
        if self.jumpTableLength < 0:
            qvmFile.close()
            raise InvalidQvm("bad header: jumpTableLength %d" % self.jumpTableLength)

        qvmFile.seek(self.codeSegOffset)
        self.codeData = qvmFile.read(self.codeSegLength)
        self.codeData = self.codeData + b"\x00\x00\x00\x00\x00"  # for look ahead
        qvmFile.seek(self.dataSegOffset)
        self.dataData = qvmFile.read(self.dataSegLength)
        self.dataData = self.dataData + b"\x00\x00\x00\x00"  # for look ahead

        qvmFile.seek(self.litSegOffset)
        self.litData = qvmFile.read(self.litSegLength)
        self.litData = self.litData + b"\x00\x00\x00\x00"  # for look ahead

        if self.magic != QVM_MAGIC_VER1:
            self.jumpTableData = qvmFile.read(self.jumpTableLength)
        else:
            self.jumpTableData = b""

        qvmFile.close()

        self.syscalls = {}  # num:int -> name:str
        self.functions = {}  # addr:int -> name:str

        # user labels

        # ArgRangeLabels could just be part of LocalRangeLabels but local
        # address isn't known when the function is defined
        self.functionsArgRangeLabels = {}  # addr:int -> { argX:str -> range:RangeElement }

        self.functionsLocalLabels = {}  # addr:int -> { localAddr:int -> sym:str }
        self.functionsLocalRangeLabels = {}  # addr:int -> { localAddr:int -> [ range1:RangeElement, range2:RangeElement, ... ] }

        self.functionHashes = {}  # addr:int -> hash:int
        self.functionRevHashes = {}  # hash:int -> [funcAddr1:int, funcAddr2:int, ...]
        self.functionSizes = {}  # addr:int -> instructionCount:int
        self.functionMaxArgsCalled = {}  # addr:int -> maxArgs:int
        self.functionParmNum = {}  # addr:int -> num:int

        self.baseQ3FunctionRevHashes = {}  # hash:int -> [ funcName1, funcName2, ... ]

        self.symbols = {}  # addr:int -> sym:str
        self.symbolsRange = {}  # addr:int -> [ range1:RangeElement, range2:RangeElement, ... ]

        self.templateManager = TemplateManager()

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
        self.switchDataTable = {}  # addr:int -> [ switchCodeAddr1:int, switchCodeAddr2:int, ... ]
        self.callPoints = {}  # targetAddr:int -> [ callerAddr1:int, callerAddr2:int, ... ]

        self.jumpTableTargets = []  # [ targetAddr1:int, targetAddr2:int, targetAddr3:int, ... ]

        self.pointerDereference = {}  # addr:int -> [ local:bool, pointerAddr:int, offset:int ]

        self.set_qvm_type(qvmType)
        self.load_address_info()
        self.parse_jump_table()
        self.compute_function_info()

    def set_qvm_type (self, qvmType):

        def ferror_exit (msg):
            error_exit("%s in line %d of %s: %s" % (msg, lineCount + 1, fname, line))

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
                    self.syscalls[parse_int(words[2])] = words[1]
                except ValueError:
                    ferror_exit("couldn't parse system call number")
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
                    # hex value without leading '0x':  2ad89a6d
                    h = atoi(words[2], 16)
                except ValueError:
                    ferror_exit("couldn't parse hash value")
                if h in self.baseQ3FunctionRevHashes:
                    self.baseQ3FunctionRevHashes[h].append(n)
                else:
                    self.baseQ3FunctionRevHashes[h] = [n]
            lineCount += 1

    # addr:int, symbolsRange:{} addr:int -> [ range1:RangeElement, range2:RangeElement, ... ]
    def find_in_symbol_range (self, addr, symbolsRange):
        exactMatches = []  #FIXME sorted
        match = None
        matchDiff = 0
        matchSym = ""
        matchRangeSize = 0
        for rangeAddr in symbolsRange:
            for r in symbolsRange[rangeAddr]:
                size = r.size
                sym = r.symbolName
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
                addr = parse_int(v)
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

        def ferror_exit (msg):
            error_exit("%s in line %d of %s: %s" % (msg, lineCount + 1, fname, line))
        def fwarning_msg (msg):
            warning_msg("%s in line %d of %s: %s" % (msg, lineCount + 1, fname, line))

        # symbol templates
        self.templateManager.load_default_templates()

        # symbols
        fname = SYMBOLS_FILE
        if os.path.exists(fname):
            f = open(fname)
            lines = f.readlines()
            f.close()
            prevAddr = -1
            lineCount = 0
            for line in lines:
                # strip comments
                line = line.split(";")[0]
                words = line.split()
                # skip blank lines
                if len(words) == 0:
                    lineCount += 1
                    continue

                if len(words) == 1:
                    ferror_exit("invalid word count")

                if len(words) == 2:
                    try:
                        addr = parse_int(words[0])
                    except ValueError:
                        ferror_exit("couldn't parse address")
                    if addr < 0:
                        ferror_exit("invalid address")
                    # check if it replaces previous symbol
                    if addr in self.symbols:
                        fwarning_msg("replacing simple symbol")
                    # check if it is out of order
                    if addr < prevAddr:
                        fwarning_msg("simple symbol out of order")
                    prevAddr = addr;

                    self.symbols[addr] = words[1]
                    # check if it would override previously declared range
                    if addr in self.symbolsRange:
                        fwarning_msg("simple symbol overrides range")

                elif len(words) == 3:
                    try:
                        addr = parse_int(words[0])
                    except ValueError:
                        ferror_exit("couldn't parse address")
                    if addr < 0:
                        ferror_exit("invalid address")

                    if addr < prevAddr:
                        fwarning_msg("symbol out of order")
                    prevAddr = addr

                    (size, symbolType, template, isPointer, pointerType, pointerDepth, isArray, arrayLevels, arrayElementSize, aliasUsed) = self.templateManager.parse_symbol_or_size(words[1:], lineCount, fname, line)

                    sym = words[2]

                    if template  and  not isArray:
                        # add template
                        if not addr in self.symbolsRange:
                            self.symbolsRange[addr] = []
                        templateSize = self.templateManager.symbolTemplates[template].size
                        members = self.templateManager.symbolTemplates[template].members
                        # add template itself
                        self.symbolsRange[addr].append(RangeElement(size=templateSize, symbolName=sym))
                        # check if it matches previously declared simple symbol
                        if addr in self.symbols:
                            fwarning_msg("template range would be overriden by simple symbol")

                        for m in members:
                            maddr = addr + m.offset
                            if not maddr in self.symbolsRange:
                                self.symbolsRange[maddr] = []
                            self.symbolsRange[maddr].append(RangeElement(size=m.size, symbolType=m.symbolType, symbolName="%s.%s" % (sym, m.name), isPointer=m.isPointer, pointerType=m.pointerType, pointerDepth=m.pointerDepth, isArray=m.isArray, arrayLevels=m.arrayLevels, arrayTemplate=m.arrayTemplate, arrayElementSize=m.arrayElementSize))
                            # check if it matches previously declared simple symbol
                            if addr in self.symbols:
                                fwarning_msg("member template range would be overriden by simple symbol")

                    else:  # basic type, range, pointer, or array
                        if not addr in self.symbolsRange:
                            self.symbolsRange[addr] = []
                        self.symbolsRange[addr].append(RangeElement(size=size, symbolType=symbolType, symbolName=sym, isPointer=isPointer, pointerType=pointerType, pointerDepth=pointerDepth, isArray=isArray, arrayLevels=arrayLevels, arrayTemplate=template, arrayElementSize=arrayElementSize))
                        # check if it would be overriden by previously declared simple symbol
                        if addr in self.symbols:
                            fwarning_msg("range would be overriden by simple symbol")

                else:  # len(words) > 3
                    ferror_exit("extra text specified")

                lineCount += 1

        # functions
        fname = FUNCTIONS_FILE
        if os.path.exists(fname):
            f = open(fname)
            lines = f.readlines()
            f.close()

            lineCount = 0
            currentFuncAddr = None
            lastArgNum = -1
            lastLocalAddr = -1
            while lineCount < len(lines):
                line = lines[lineCount]
                # strip comments
                line = line.split(";")[0]
                words = line.split()
                # skip blank lines
                if len(words) == 0:
                    lineCount += 1
                    continue

                if len(words) == 1:
                    ferror_exit("invalid word count")

                if len(words) > 1:
                    # arg0, arg1, ...
                    if words[0].startswith("arg"):
                        if currentFuncAddr == None:
                            ferror_exit("function not defined yet")

                        # validate arg number
                        numStr = words[0][len("arg"):]
                        if not numStr.isdigit():
                            ferror_exit("invalid arg number '%s'" % numStr)

                        # don't allow zero padding (ex: arg0001) since arg
                        # dictionary is checked using "arg%d" % num
                        if numStr[0] == '0'  and  len(numStr) > 1:
                            ferror_exit("zero padded arg number")

                        # check if out of order
                        argNum = atoi(numStr)
                        if argNum < lastArgNum:
                            fwarning_msg("arg number out of order")
                        lastArgNum = argNum

                        if not currentFuncAddr in self.functionsArgRangeLabels:
                            self.functionsArgRangeLabels[currentFuncAddr] = {}

                        # check if replacing
                        if words[0] in self.functionsArgRangeLabels[currentFuncAddr]:
                            fwarning_msg("replacing arg")

                        if len(words) > 2:
                            (size, symbolType, template, isPointer, pointerType, pointerDepth, isArray, arrayLevels, arrayElementSize, aliasUsed) = self.templateManager.parse_symbol_or_size(words[1:], lineCount, fname, line)
                            # validate
                            if symbolType == SYMBOL_RANGE  and  size > 4:
                                ferror_exit("invalid argument range size, arguments are integers (values or pointers)")
                            elif symbolType == SYMBOL_TEMPLATE:
                                ferror_exit("invalid argument type, arguments are integers (values or pointers)")

                            # validates, it is either a basice type or pointer
                            self.functionsArgRangeLabels[currentFuncAddr][words[0]] = RangeElement(size=size, symbolName=words[2], symbolType=symbolType, isPointer=isPointer, pointerType=pointerType, pointerDepth=pointerDepth)
                        else:
                            # label
                            self.functionsArgRangeLabels[currentFuncAddr][words[0]] = RangeElement(size=0x4, symbolName=words[1], symbolType=SYMBOL_RANGE, isPointer=False, pointerType="", pointerDepth=0)

                    elif words[0] == "local":
                        if currentFuncAddr == None:
                            ferror_exit("function not defined yet")
                        if len(words) < 3:
                            ferror_exit("invalid local specification")
                        if len(words) > 3:  # range or template/type specified
                            try:
                                localAddr = parse_int(words[1])
                            except ValueError:
                                ferror_exit("couldn't parse local address of range")
                            if localAddr < 0:
                                ferror_exit("invalid local address range")

                            # validate order
                            if localAddr < lastLocalAddr:
                                fwarning_msg("local address out of order")
                            lastLocalAddr = localAddr

                            (size, symbolType, template, isPointer, pointerType, pointerDepth, isArray, arrayLevels, arrayElementSize, aliasUsed) = self.templateManager.parse_symbol_or_size(words[2:], lineCount, fname, line)
                            sym = words[3]

                            if template  and  not isArray:
                                # add template
                                if not currentFuncAddr in self.functionsLocalRangeLabels:
                                    self.functionsLocalRangeLabels[currentFuncAddr] = {}
                                if not localAddr in self.functionsLocalRangeLabels[currentFuncAddr]:
                                    self.functionsLocalRangeLabels[currentFuncAddr][localAddr] = []
                                templateSize = self.templateManager.symbolTemplates[template].size
                                members = self.templateManager.symbolTemplates[template].members
                                # add template itself
                                self.functionsLocalRangeLabels[currentFuncAddr][localAddr].append(RangeElement(size=templateSize, symbolName=sym))
                                # check if it is overriden by previously declared simple symbol
                                if currentFuncAddr in self.functionsLocalLabels:
                                    if localAddr in self.functionsLocalLabels[currentFuncAddr]:
                                        fwarning_msg("local template range would be overriden by local simple symbol")

                                for m in members:
                                    maddr = localAddr + m.offset
                                    if not maddr in self.functionsLocalRangeLabels[currentFuncAddr]:
                                        self.functionsLocalRangeLabels[currentFuncAddr][maddr] = []
                                    self.functionsLocalRangeLabels[currentFuncAddr][maddr].append(RangeElement(size=m.size, symbolType=m.symbolType, symbolName="%s.%s" % (sym, m.name), isPointer=m.isPointer, pointerType=m.pointerType, isArray=m.isArray, arrayLevels=m.arrayLevels, arrayTemplate=m.arrayTemplate, arrayElementSize=m.arrayElementSize))
                                    # check if it matches previously declared simple symbol
                                    if currentFuncAddr in self.functionsLocalLabels:
                                        if maddr in self.functionsLocalLabels[currentFuncAddr]:
                                            fwarning_msg("local member template range would be override by simple symbol")
                            else:  # basic type, range, pointer, or array
                                if not currentFuncAddr in self.functionsLocalRangeLabels:
                                    self.functionsLocalRangeLabels[currentFuncAddr] = {}
                                if not localAddr in self.functionsLocalRangeLabels[currentFuncAddr]:
                                    self.functionsLocalRangeLabels[currentFuncAddr][localAddr] = []
                                self.functionsLocalRangeLabels[currentFuncAddr][localAddr].append(RangeElement(size=size, symbolType=symbolType, symbolName=sym, isPointer=isPointer, pointerType=pointerType, pointerDepth=pointerDepth, isArray=isArray, arrayLevels=arrayLevels, arrayTemplate=template, arrayElementSize=arrayElementSize))
                                # check if it matches previously declared simple symbol
                                if currentFuncAddr in self.functionsLocalLabels:
                                    if localAddr in self.functionsLocalLabels[currentFuncAddr]:
                                        fwarning_msg("local range would be override by simple symbol")
                        else:  # range or template/type not specified
                            if not currentFuncAddr in self.functionsLocalLabels:
                                self.functionsLocalLabels[currentFuncAddr] = {}
                            try:
                                laddr = parse_int(words[1])
                            except ValueError:
                                ferror_exit("couldn't parse address")

                            # check if it replaces previous symbol
                            if laddr in self.functionsLocalLabels[currentFuncAddr]:
                                fwarning_msg("replacing local simple symbol")

                            # check if it is out of order
                            if laddr < lastLocalAddr:
                                fwarning_msg("local address out of order")
                            lastLocalAddr = laddr

                            self.functionsLocalLabels[currentFuncAddr][laddr] = words[2]
                            # check if it overrides previously declared range
                            if currentFuncAddr in self.functionsLocalRangeLabels:
                                if laddr in self.functionsLocalRangeLabels[currentFuncAddr]:
                                    fwarning_msg("local simple symbol overrides range")
                    else:
                        # function definition
                        try:
                            funcAddr = parse_int(words[0])
                        except ValueError:
                            ferror_exit("couldn't parse address")
                        if funcAddr < 0:
                            ferror_exit("invalid address")
                        self.functions[funcAddr] = words[1]

                        # check if it is out of order
                        if currentFuncAddr:
                            if funcAddr < currentFuncAddr:
                                fwarning_msg("function out of order")

                        currentFuncAddr = funcAddr
                        lastArgNum = -1
                        lastLocalAddr = -1

                lineCount += 1

        # constants
        fname = CONSTANTS_FILE
        if os.path.exists(fname):
            f = open(fname)
            lines = f.readlines()
            f.close()

            lineCount = 0
            lastCodeAddr = -1
            for line in lines:
                # strip comments
                line = line.split(";")[0]
                words = line.split()

                # skip blank lines
                if len(words) == 0:
                    lineCount += 1
                    continue

                if len(words) != 3:
                    ferror_exit("invalid word count")

                # at this point len(words) == 3
                try:
                    codeAddr = parse_int(words[0])
                    n = words[1]
                    val = parse_int(words[2])
                except ValueError:
                    ferror_exit("couldn't parse address or value")
                if codeAddr < 0:
                    ferror_exit("invalid address")

                self.constants[codeAddr] = [n, val]

                # check if it is out of order
                if codeAddr < lastCodeAddr:
                    fwarning_msg("constant address out of order")
                lastCodeAddr = codeAddr

                lineCount += 1

        # comments
        # load after functions and symbols files to allow variable substitutions
        fname = COMMENTS_FILE
        if os.path.exists(fname):
            f = open(fname)
            lines = f.readlines()
            f.close()

            lineCount = 0
            lastCodeAddr = -1
            lastDataAddr = -1
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

                # skip blank lines
                if len(words) == 0:
                    lineCount += 1
                    continue

                if len(words) == 1:
                    ferror_exit("invalid word count")

                dataComment = False
                if len(words) > 1:
                    if words[0] == "d":
                        dataComment = True
                        del words[0]

                if len(words) > 1:
                    try:
                        codeAddr = parse_int(words[0])
                    except ValueError:
                        ferror_exit("couldn't get address")
                    if codeAddr < 0:
                        error_exit("invalid address")

                    # check if it is out of order
                    if dataComment:
                        if codeAddr < lastDataAddr:
                            fwarning_msg("data comment out of order")
                        lastDataAddr = codeAddr
                    else:
                        if codeAddr < lastCodeAddr:
                            fwarning_msg("code comment out of order")
                        lastCodeAddr = codeAddr

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
                                    ferror_exit("couldn't substitute variable")

                            if dataComment:
                                self.dataCommentsInline[codeAddr] = comment
                            else:
                                self.commentsInline[codeAddr] = comment
                    elif commentType == "before"  or  commentType == "after":
                        spaceBefore = 0
                        spaceAfter = 0
                        if len(words) > 2:
                            try:
                                spaceBefore = parse_int(words[2])
                                if len(words) > 3:
                                    spaceAfter = parse_int(words[3])
                            except ValueError:
                                ferror_exit("couldn't get space before or after value")
                        if spaceBefore < 0  or  spaceAfter < 0:
                            ferror_exit("invalid space before or after")

                        if spaceBefore > 0  or  spaceAfter > 0:
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
                                        ferror_exit("couldn't substitute variable")
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
                        ferror_exit("invalid comment type")

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
        decStack = DecompileStack()
        pos = 0

        count = -1
        currentFuncAddr = None
        while count < self.instructionCount - 1:
            count += 1

            comment = None
            decStr = None

            opcStr = self.codeData[pos]
            opc = xord(opcStr)
            pos += 1
            name = opcodes[opc][OPCODE_NAME]
            psize = opcodes[opc][OPCODE_PARM_SIZE]

            if opc != OP_ENTER  and  count in self.commentsBefore:
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
                decStack.markInvalid()
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
                decStack.markInvalid()

            if opc == OP_ENTER:
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
                decStack.clear()
            elif opc == OP_LOCAL:
                if count in self.switchStartStatements:
                    output("; possible switch start\n")

                localDecStr = "&local%x" % parm
                argNum = parm - stackAdjust - 0x8
                if argNum >= 0:
                    argstr = "arg%d" % (argNum / 4)
                    comment = argstr
                    localDecStr = "&" + argstr
                    if currentFuncAddr in self.functionsArgRangeLabels:
                        if argstr in self.functionsArgRangeLabels[currentFuncAddr]:
                            sname = self.functionsArgRangeLabels[currentFuncAddr][argstr].symbolName
                            comment = comment + " : " + sname
                            localDecStr = "&" + sname
                else:
                    if currentFuncAddr in self.functionsLocalLabels:
                        if parm in self.functionsLocalLabels[currentFuncAddr]:
                            comment = self.functionsLocalLabels[currentFuncAddr][parm]
                            localDecStr = "&" + comment
                    elif currentFuncAddr in self.functionsLocalRangeLabels:
                        (match, matchSym, matchDiff, exactMatches) = self.find_in_symbol_range(parm, self.functionsLocalRangeLabels[currentFuncAddr])

                        if len(exactMatches) > 0:
                            comment =  ", ".join(exactMatches)
                            # since there's more than one, don't replace decompile string
                        else:
                            if match != None:
                                comment = "%s + 0x%x" % (matchSym, matchDiff)
                                #FIXME 2020-11-13 double check if this is ok
                                localDecStr = "(&" + comment + ")"
                #FIXME symbol eval
                decStack.push(localDecStr)
            elif opc == OP_CONST:
                nextOp = xord(self.codeData[pos])

                localDecStr = "0x%x" % parm
                if count in self.constants:
                    if parm != self.constants[count][1]:
                        comment = "FIXME constant val != to code val"
                    else:
                        comment = self.constants[count][0]
                        localDecStr = comment
                elif parm >= self.dataSegLength  and  parm < self.dataSegLength + self.litSegLength  and  nextOp not in (OP_CALL, OP_JUMP):
                    output("\n  ; ")
                    self.print_lit_string(parm)
                    output("\n");
                elif parm >= 0  and  parm < self.dataSegLength  and  nextOp not in (OP_CALL, OP_JUMP):
                    b0 = xchr(self.dataData[parm])
                    b1 = xchr(self.dataData[parm + 1])
                    b2 = xchr(self.dataData[parm + 2])
                    b3 = xchr(self.dataData[parm + 3])

                    output("\n  ; %02x %02x %02x %02x  (0x%x)\n" % (xord(b0), xord(b1), xord(b2), xord(b3), struct.unpack("<L", self.dataData[parm:parm+4])[0]))
                    if parm in self.symbols:
                        comment = self.symbols[parm]
                        localDecStr = "&" + comment
                    else:  # check symbol ranges
                        (match, matchSym, matchDiff, exactMatches) = self.find_in_symbol_range(parm, self.symbolsRange)
                        if len(exactMatches) > 0:
                            comment =  ", ".join(exactMatches)
                            # if there's more than one, don't replace decompile string
                            if len(exactMatches) == 1:
                                localDecStr = "&" + exactMatches[0]
                        else:
                            if match != None:
                                comment = "%s + 0x%x" % (matchSym, matchDiff)
                                localDecStr = "(&" + comment + ")"

                elif nextOp == OP_CALL:
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

                elif parm >= self.dataSegLength  and  nextOp not in (OP_CALL, OP_JUMP):
                    # bss segment
                    #FIXME check that it doesn't go past??
                    if parm in self.symbols:
                        comment = self.symbols[parm]
                        localDecStr = "&" + comment
                    else:  # check symbol ranges
                        exactMatches = []  #FIXME sorted
                        match = None
                        matchDiff = 0
                        matchSym = ""
                        matchRangeSize = 0
                        for rangeAddr in self.symbolsRange:
                            for r in self.symbolsRange[rangeAddr]:
                                size = r.size
                                sym = r.symbolName
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
                            # since there's more than one, don't replace decompile string
                        else:
                            if match != None:
                                comment = "%s + 0x%x" % (matchSym, matchDiff)
                                localDecStr = "(&" + comment + ")"
                decStack.push(localDecStr)
            elif opc == OP_JUMP:
                if count in self.switchJumpStatements:
                    tmin = self.switchJumpStatements[count][0]
                    tmax = self.switchJumpStatements[count][1]
                    taddr = self.switchJumpStatements[count][2]
                    output("; possible switch jump: 0x%x (0x%x -> 0x%x)\n" % (taddr, tmin, tmax))
                decStack.markInvalid()
            elif (opc == OP_LOAD4  or  opc == OP_LOAD2  or  opc == OP_LOAD1):
                if count in self.pointerDereference:
                    pdr = self.pointerDereference[count]

                    # find template or basic type
                    foundTemplate = False
                    foundBasicType = False
                    btype = ""
                    templateName = ""
                    isLocal = pdr[0]
                    rangeAddr = pdr[1]
                    sym = ""

                    if isLocal:
                        # check if arg first
                        argNum = rangeAddr - stackAdjust - 0x8

                        if argNum >= 0:
                            # hack to use range check below
                            argstr = "arg%d" % (argNum / 4)
                            if currentFuncAddr in self.functionsArgRangeLabels:
                                if argstr in self.functionsArgRangeLabels[currentFuncAddr]:
                                    symbolsRange = { rangeAddr : [self.functionsArgRangeLabels[currentFuncAddr][argstr]] }
                                else:
                                    symbolsRange = {}
                            else:
                                symbolsRange = {}
                        else:
                            if currentFuncAddr in self.functionsLocalRangeLabels:
                                symbolsRange = self.functionsLocalRangeLabels[currentFuncAddr]
                            else:
                                symbolsRange = {}
                    else:
                        symbolsRange = self.symbolsRange

                    if rangeAddr in symbolsRange:
                        for r in symbolsRange[rangeAddr]:
                            # use first match
                            sym = r.symbolName
                            #FIXME support for higher pointerDepth
                            if r.size == 0x4  and  r.isPointer  and  r.pointerDepth == 1:
                                if r.symbolType == SYMBOL_POINTER_TEMPLATE:
                                    templateName = r.pointerType
                                    foundTemplate = True
                                    break
                                elif r.symbolType == SYMBOL_POINTER_VOID  or  r.symbolType == SYMBOL_POINTER_BASIC:
                                    btype = r.pointerType
                                    foundBasicType = True
                                    break

                    if foundTemplate:
                        memberName = "?"
                        if templateName not in self.templateManager.symbolTemplates:
                            error_exit("unknown template %s" % templateName)
                        memberList = self.templateManager.symbolTemplates[templateName].members
                        foundOffset = False
                        for m in memberList:
                            memberName = m.name
                            if m.offset == pdr[2]:
                                foundOffset = True
                                break
                        if not foundOffset:
                            output("; pointer dereference (couldn't match offset) *0x%x -> (0x%x)\n" % (pdr[1], pdr[2]))
                        else:
                            output("; pointer dereference %s->%s\n" % (sym, memberName))
                    elif foundBasicType:
                        output("; pointer dereference  (basic type: %s) *0x%x -> (0x%x)\n" % (btype, pdr[1], pdr[2]))
                    else:
                        output("; pointer dereference  (no template) *0x%x -> (0x%x)\n" % (pdr[1], pdr[2]))
                # decompile
                if opc == OP_LOAD1:
                    decStack.op_load1()
                elif opc == OP_LOAD2:
                    decStack.op_load2()
                elif opc == OP_LOAD4:
                    decStack.op_load4()
            # decompile
            elif opc == OP_STORE1:
                decStack.op_store1()
                decStr = decStack.result()
                decStack.clear()
            elif opc == OP_STORE2:
                decStack.op_store2()
                decStr = decStack.result()
                decStack.clear()
            elif opc == OP_STORE4:
                decStack.op_store4()
                decStr = decStack.result()
                decStack.clear()
            elif opc == OP_ARG:
                decStack.markInvalid()
            elif opc == OP_LEAVE:
                decStack.markInvalid()
            elif opc == OP_CALL:
                decStack.markInvalid()
            elif opc == OP_BLOCK_COPY:
                #FIXME  -- should be just like store*
                decStack.markInvalid()
            elif opc in (OP_EQ, OP_NE, OP_LTI, OP_LEI, OP_GTI, OP_GEI, OP_LTU, OP_LEU, OP_GTU, OP_GEU, OP_EQF, OP_NEF, OP_LTF, OP_LEF, OP_GTF, OP_GEF):
                decStack.markInvalid()
            elif opc == OP_SEX8:
                decStack.op_sex8()
            elif opc == OP_SEX16:
                decStack.op_sex16()
            elif opc == OP_NEGI:
                decStack.op_negi()
            elif opc == OP_ADD:
                decStack.op_add()
            elif opc == OP_SUB:
                decStack.op_sub()
            elif opc == OP_DIVI:
                decStack.op_divi()
            elif opc == OP_DIVU:
                decStack.op_divu()
            elif opc == OP_MODI:
                decStack.op_modi()
            elif opc == OP_MODU:
                decStack.op_modu()
            elif opc == OP_MULI:
                decStack.op_muli()
            elif opc == OP_MULU:
                decStack.op_mulu()
            elif opc == OP_BAND:
                decStack.op_band()
            elif opc == OP_BOR:
                decStack.op_bor()
            elif opc == OP_BXOR:
                decStack.op_bxor()
            elif opc == OP_BCOM:
                decStack.op_bcom()
            elif opc == OP_LSH:
                decStack.op_lsh()
            elif opc == OP_RSHI:
                decStack.op_rshi()
            elif opc == OP_RSHU:
                decStack.op_rshu()
            elif opc == OP_NEGF:
                decStack.op_negf()
            elif opc == OP_ADDF:
                decStack.op_addf()
            elif opc == OP_SUBF:
                decStack.op_subf()
            elif opc == OP_DIVF:
                decStack.op_divf()
            elif opc == OP_MULF:
                decStack.op_mulf()
            elif opc == OP_CVIF:
                decStack.op_cvif()
            elif opc == OP_CVFI:
                decStack.op_cvfi()

            sc = opcodes[opc][OPCODE_STACK_CHANGE]
            if sc != 0  or  parm != None:
                output("%08x  %-13s" % (count, name))
            else:
                output("%08x  %s" % (count, name))

            if sc < 0:
                output("  %d" % sc)
            elif sc > 0:
                output("   %d" % sc)
            else:
                if parm != None  or  comment  or  count in self.commentsInline:
                    output("    ")

            if parm != None:
                if parm < 0:
                    output("  -0x%x" % abs(parm))  # -parm pylint warning
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

            if decStr != None:
                output("    ;; dec: " + decStr + "\n")
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

            if count in self.switchDataTable:
                output("  ; switch table data from")
                for sj in self.switchDataTable[count]:
                    output(" 0x%x" % sj)

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
            psize = opcodes[opc][OPCODE_PARM_SIZE]
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

            if opc == OP_CONST:
                if parm < 0:
                    funcHashSum += "%d" % parm
            elif opc == OP_POP:
                lastArg = 0
            elif opc == OP_LOCAL:
                funcHashSum += "%d" % parm
            elif opc == OP_ARG:
                if parm > maxArgs:
                    maxArgs = parm
                lastArg = parm
            elif (opc == OP_LOAD4  or  opc == OP_LOAD2  or  opc == OP_LOAD1):
                #FIXME check pointer dereference
                #FIXME don't cross jump boundaries
                #FIXME load2 load1

                # offset might be in a local variable.  ex:
                #
                #    000105c6  local           1   0x1c
                #
                #      ; 27 00 00 00  (0x27)
                #    000105c7  const           1   0x8
                #    000105c8  store4         -2
                #    000105c9  const           1   0xcbab4  ; cg.nextSnap
                #    000105ca  load4
                #    000105cb  local           1   0x1c
                #    000105cc  load4
                #    000105cd  add            -1
                #    000105ce  load4
                #
                # offset could also be specified explicitly.  ex:
                #
                #    00010602  const           1   0xcbab0  ; cg.snap
                #    00010603  load4
                #
                #      ; 27 00 00 00  (0x27)
                #    00010604  const           1   0x8
                #    00010605  add            -1
                #    00010606  load4

                #FIXME global var read/write when offset in local variable

                #FIXME global var write

                if len(funcOps) > 4:
                    if (
                            funcOps[-5][0] == OP_CONST  and
                            funcOps[-4][0] == OP_LOAD4  and
                            funcOps[-3][0] == OP_CONST  and
                            funcOps[-2][0] == OP_ADD
                    ):  # explicit global var read
                        pointerAddr = funcOps[-5][1]
                        offset = funcOps[-3][1]
                        local = False

                        #FIXME pointer to pointer to pointer ...
                        self.pointerDereference[ins] = [local, pointerAddr, offset]
                    elif (
                            funcOps[-5][0] == OP_LOCAL  and
                            funcOps[-4][0] == OP_LOAD4  and
                            funcOps[-3][0] == OP_CONST  and
                            funcOps[-2][0] == OP_ADD
                    ):  # explicit local var read
                        pointerAddr = funcOps[-5][1]
                        offset = funcOps[-3][1]
                        local = True

                        #FIXME pointer to pointer to pointer ...
                        self.pointerDereference[ins] = [local, pointerAddr, offset]
            elif opc == OP_ENTER:
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
            elif opc == OP_JUMP:
                if prevOpc == OP_CONST:
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
                            funcOps[-16][0] == OP_LOCAL and
                            funcOps[-15][0] == OP_LOAD4 and
                            funcOps[-14][0] == OP_CONST and
                            funcOps[-13][0] == OP_LTI and
                            funcOps[-12][0] == OP_LOCAL and
                            funcOps[-11][0] == OP_LOAD4 and
                            funcOps[-10][0] == OP_CONST and
                            funcOps[-9][0] == OP_GTI and
                            funcOps[-8][0] == OP_LOCAL and
                            funcOps[-7][0] == OP_LOAD4 and
                            funcOps[-6][0] == OP_CONST and
                            funcOps[-5][0] == OP_LSH and
                            funcOps[-4][0] == OP_CONST and
                            funcOps[-3][0] == OP_ADD and
                            funcOps[-2][0] == OP_LOAD4
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
                                warning_msg("min greater than max for switch at 0x%x: %d > %d" % (ins, tmin, tmax))
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
                                        dataAddr = taddr + (offset * 4)
                                        if dataAddr in self.switchDataTable:
                                            self.switchDataTable[dataAddr].append(ins)
                                        else:
                                            self.switchDataTable[dataAddr] = [ins]

                                        if addr in self.switchJumpPoints:
                                            self.switchJumpPoints[addr].append([ins, offset])
                                        else:
                                            self.switchJumpPoints[addr] = [[ins, offset]]

            elif opcodes[opc][OPCODE_JUMP_PARM]:
                if parm in self.jumpPoints:
                    self.jumpPoints[parm].append(ins)
                else:
                    self.jumpPoints[parm] = [ins]
            elif opc == OP_CALL:
                if prevOpc == OP_CONST:
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
            psize = opcodes[opc][OPCODE_PARM_SIZE]
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
