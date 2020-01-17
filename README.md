# Qvmdis : Quake3 QVM disassembler

```
  Usage:  qvmdis <qvm file> [cgame|game|ui]
    optionally specify cgame, game, or ui qvm to match syscalls and function hashes
```

Features:

* Indicates stack size change for opcodes
* Labels jump locations
* Identifies which other functions call a particular function
* Identifies syscalls
* Identifies references to function arguments
* Adds comments for possible string reference values
* Adds comments for possible data reference values
* Computes function hashes and compares to stock QVM to identify possible
matches
* Function names, arguments, and local variables can be labeled in separate
functions.dat file
* Symbol names can be labeled using separate symbols.dat file
* Constants can be labeled in constants.dat
* Comments can be added in comments.dat

The .dat files are opened from the current working directory.  Comments in
.dat files are specified with ';'.

## Format of .dat files:

### *functions.dat* ###

    0x0000 vmMain
      arg0 command
      local 0x14 commandTmp

    0x1223 CG_DrawAttacker
    0x28ae CG_Draw3DModel
      arg0 x
      local 0x18 0x170 refdef  ; also specifies the size

Local variables can optionally specify a size to identify references within a
range.  See *symbols.dat* description for notes regarding ranges.

### *symbols.dat* ###

    0xab2a3 serverTime
    0xb23fa 0x1000 clientData

Size can optionally be specified to identify references within a range.
Symbol lookups without a size specified take precedence.  Multiple ranges
beginning at the same address are printed as a comma separated list.  Ex:

    0xe87c8 0x26754 cgs
      0x87c8 0x4e84 cgs.gameState

output:

```0000104e  const           1   0xe87c8   ; cgs, cgs.gameState```

Since the first element in a structure shares the same starting address as the
structure itself, you can make sure they are both output by specifing a size
for the element.  Ex:

    0xcba90 0x1cd38 cg
      ; usually don't specify size for ints, but for first element allows
      ; printing parent reference
      0xcba90 0x4 cg.clientFrame
      0xcba94 cg.clientNum

output:

```00001094  const           1   0xcba90   ; cg, cg.clientFrame```

### *constants.dat* ###

    0x3f31 DEFAULT_SPEED 0x0

The last value in the contants.dat entry is used to double check that the value
is correct.

### *comments.dat* ###

    0x5a11 inline This is an inline comment added to the end of the line
    0x5ba1 before

    This is a comment block
    added before the address.

    <<<
    0x6aa2 after 2 2
    This comment is
    after the address.

    <<<

    d 0x30bc inline fullName

Before and after comments are terminated with a line that only has '<<<'.
They can also specify a number of blank lines before and after the comment.
A 'd' before the address specifies it's a data segment comment.
