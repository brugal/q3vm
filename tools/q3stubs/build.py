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

import os, sys

def error_exit (msg):
    sys.stderr.write("ERROR: %s\n" % msg)
    sys.exit(1)

def usage ():
    sys.stderr.write("%s [-h, --help] [quake3 sdk location]\n" % os.path.basename(sys.argv[0]))
    sys.exit(1)

Q3sdk = os.path.join(os.sep, "home", "acano", "tmp", "sdk1", "mod-sdk-1.32")

def main ():
    global Q3sdk

    for a in sys.argv[1:]:
        if a in ("-h", "--help"):
            usage()

    if len(sys.argv) > 1:
        Q3sdk = sys.argv[1]

    if not os.path.exists(Q3sdk):
        error_exit("quake3 sdk location doesn't exist: %s" % Q3sdk)

    stubBaseNames = ("cgame", "game", "q3_ui")

    for s in stubBaseNames:
        cmd = "gcc -Wall -m32 -c -I\"%s\" %s.c -o %s.o" % (Q3sdk, s, s)
        ret = os.system(cmd)
        if ret != 0:
            error_exit("failed to create stub")

if __name__ == "__main__":
    main()
