#!/usr/bin/env python
import os, subprocess, sys

# converts q3asm .map file to hash map file (.hmap)

def usage ():
    sys.stderr.write("usage: %s <qvm .map file> <qvm file>\n" % sys.argv[0])
    sys.stderr.write("    example:  %s cgame.map cgame.qvm > cgame-func.hmap\n" % sys.argv[0])
    sys.exit(1)

def output (msg):
    sys.stdout.write(msg)

def atoi (s, base=10):
    return int(s, base)

def main ():
    if len(sys.argv) < 2:
        usage()

    qvmMapFile = sys.argv[1]
    qvmFile = sys.argv[2]

    f = open(qvmMapFile)
    lines = f.readlines()
    f.close()
    names = {}
    for line in lines:
        words = line.split()
        if len(words) > 2:
            if words[0] == "0":
                addr = atoi(words[1], 16)
                n = words[2]
                # skip system calls and stack func
                if addr < 0x7fffffff and not n in ("_stackStart", "_stackEnd"):
                    names[addr] = n

    currentDir = os.path.dirname(os.path.realpath(__file__))
    parentDir = os.path.dirname(currentDir)
    qvmdis = os.path.join(parentDir, "qvmdis")

    procOut = subprocess.check_output([qvmdis, "--func-hash", qvmFile]).decode()
    hashes = {}

    lines = procOut.splitlines()
    for line in lines:
        words = line.split()
        addr = atoi(words[0], 16)
        funcHash = words[2]
        hashes[addr] = funcHash

    k = sorted(names.keys())

    for addr in k:
        output("0x%x %s %s\n" % (addr, names[addr], hashes[addr]))

if __name__ == "__main__":
    main()
