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

# Python 2 and 3 compatibility

# removed from string module
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

