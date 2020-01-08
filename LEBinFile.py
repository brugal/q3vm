# little endian binary file
import struct

class LEBinFile:
    def __init__ (self, fname):
        self._file = open(fname, "rb")

    def read (self, numBytes=1):
        return self._file.read(numBytes)

    def read_int (self):
        data = self.read(4)
        w = struct.unpack("<l", data)[0]
        return w

    def read_byte (self):
        return ord(self.read())

    def read_char (self):
        return self.read()

    def seek (self, p):
        self._file.seek(p)

    def tell (self):
        return self._file.tell()

