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

class DecompileStack:

    def __init__ (self):
        # C strings representing decompilation.  Ex:
        # [
        #   "&local8",
        #   "(unsigned int)*(unsigned int *)local14 ^ (unsigned int)*(byte *)&locala",
        #   ...
        # ]
        self.stack = []
        self._valid = True

    def clear (self):
        self.stack = []
        self._valid = True

    def markInvalid (self):
        self._valid = False

    def isValid (self):
        return self._valid

    def push (self, s):
        if self._valid:
            self.stack.append(s)

    def pop (self):
        if self._valid:
            return self.stack.pop()
        else:
            #FIXME warning?
            return "<invalid pop>"

    def result (self):
        # meant to be called after store*
        # make sure it's the only thing left in the stack
        if self._valid:
            if len(self.stack) != 1:
                return " -- size --"
            elif len(self.stack) == 1:
                return self.stack[0]
        else:
            #FIXME warning?
            return "----"

    def op_const (self, value):
        #FIXME check for string?
        # don't delete const reference comment
        self.push(value)

    # between:  store1, store2, store4, block_copy, arg
    #   assumes those wont be nested.  Ex:
    #         store4
    #         local 0x14
    #         local 0x18
    #            local 0x1c
    #            local 0x20
    #            load4
    #            store4
    #         load4
    #         store4

    # invalid:  enter, leave, call
    #           jump, eq, ne, lti, lei, gti, gei, ltu, leu, gtu, geu, eqf, nef, ltf, lef, gtf, gef

    def op_load1 (self):
        v = self.pop()
        self.push("*(byte *)" + "(" + v + ")")

    def op_load2 (self):
        v = self.pop()
        self.push("*(unsigned short *)" + "(" +  v + ")")

    def op_load4 (self):
        #print(self.stack)
        #print("valid: ")
        #print(self._valid)
        v = self.pop()
        self.push("*(int *)" + "(" + v + ")")

    def op_store1 (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("*(byte *)" + "(" + r1 + ")" + " = " + r0)

    def op_store2 (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("*(short *)" + "(" + r1 + ")" + " = " + r0)

    def op_store4 (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("*(int *)" + "(" + r1 + ")" + " = " + r0)

    def op_arg (self, parm):
        r0 = self.pop()
        self.push("arg[" + parm + "] = " + r0)

    def op_block_copy (self, parm):
        r0 = self.pop()
        r1 = self.pop()
        self.push("VM_BlockCopy(" + r1 + ", " + r0 + ", " + parm + ")")

    def op_sex8 (self):
        v = self.pop()
        self.push("(signed char)" + "(" + v + ")")

    def op_sex16 (self):
        v = self.pop()
        self.push("(short)" + "(" + v + ")")

    def op_negi (self):
        v = self.pop()
        #FIXME double 'negi' calls?
        if v[0] == '-':
            #FIXME warning
            self.push(v[1:])

        self.push("-" + "(" + v + ")")

    def op_add (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(" + r1 + ")"  + " + " + "(" + r0 + ")")

    def op_sub (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(" + r1 + ")" + " - " + "(" + r0 + ")")

    def op_divi (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(" + r1 + ")"  + " / " + "(" + r0 + ")")

    def op_divu (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("((unsigned int)" + "(" + r1 + ")" + ") / (" + "(unsigned int)" + "(" + r0 + ")" + ")")

    def op_modi (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(" + r1 + ")" + " % " + "(" + r0 + ")")

    def op_modu (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("((unsigned int)" + "(" + r1 + ")" + ") % (" + "(unsigned int)" + "(" + r0 + ")" + ")")

    def op_muli (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(" + r1 + ")"  + " * " + "(" + r0 + ")")

    def op_mulu (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("((unsigned int)"  + "(" + r1 + ")" + ") * (" + "(unsigned int)" + "(" + r0 + ")" + ")")

    def op_band (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("((unsigned int)" + "(" + r1 + ")" + ") & (" + "(unsigned int)" + "(" + r0 + ")" + ")")

    def op_bor (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("((unsigned int)" + "(" + r1 + ")" + ") | (" + "(unsigned int)" + "(" + r0 + ")" + ")")

    def op_bxor (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("((unsigned int)" + "(" + r1 + ")" + ") ^ (" + "(unsigned int)" + "(" + r0 + ")" + ")")

    def op_bcom (self):
        v = self.pop()
        self.push("~((unsigned int)" + "(" + v + ")" + ")")

    def op_lsh (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(" + r1 + ")" + " << " + "(" + r0 + ")")

    def op_rshi (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(" + r1 + ")" + " >> " + "(" + r0 + ")")

    def op_rshu (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("((unsigned int)" + "(" + r1 + ")" + ") >> " + "(" + r0 + ")")

    def op_negf (self):
        v = self.pop()
        #FIXME double 'negf' calls?
        if v[0] == '-':
            #FIXME warning
            self.push(v[1:])

        self.push("-(float)" + "(" + v + ")")

    def op_addf (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(float)" + "(" + r1 + ")" + " + " + "(float)" + "(" + r0 + ")")

    def op_subf (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(float)" + "(" + r1 + ")" + " - " + "(float)" + "(" + r0 + ")")

    def op_divf (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(float)" + "(" + r1 + ")" + " / " + "(float)" + "(" + r0 + ")")

    #FIXME paren here...
    def op_mulf (self):
        r0 = self.pop()
        r1 = self.pop()
        self.push("(float)" + "(" + r1 + ")" + " * " + "(float)" + "(" + r0 + ")")

    def op_cvif (self):
        v = self.pop()
        self.push("(float)" + "(" + v + ")")

    def op_cvfi (self):
        v = self.pop()
        self.push("Q_ftol((float)" + "(" + v + ")" + ")")
