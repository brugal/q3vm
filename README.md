# Qvmdis : Quake3 QVM disassembler

```
  Usage: qvmdis [--func-hash, -q] <qvm file> [cgame|game|ui]
    optionally specify cgame, game, or ui qvm to match syscalls and function hashes
    --func-hash  :  only print function hash values
    --q          :  suppress warnings

    ex: qvmdis cgame.qvm cgame > cgame.dis
```

Sample:

```c
000009b2  const           1   0x0
000009b3  eq             -2   0x9d2

;----------------------------------- from  0x9af

  ; "sprites/foe"
000009b4  const           1   0x2ae2
000009b5  arg            -1   0x8
000009b6  local           1   0x198
000009b7  const           1  -0x28   ; trap_R_RegisterShader()
000009b8  call           -1
000009b9  store4         -2
    ;; dec: ----
000009ba  const           1   0x1098f8
```

Features:

* Indicates stack size change for opcodes
* Labels jump locations
* Identities q3asm switch jump tables
* Identifies which other functions call a particular function
* Identifies syscalls
* Identifies references to function arguments
* Identifies simple pointer dereferencing
* Adds comments for possible string reference values
* Adds comments for possible data reference values
* Computes function hashes and compares to stock QVM to identify possible
matches
* Decompile between store1, store2, store4, and block_copy  operations that don't have branching operations between them
* Function names, arguments, and local variables can be labeled in separate
*functions.dat* file
* Symbol names can be labeled using separate *symbols.dat* file
* Symbol templates to identify types using a separate *templates.dat* file
* Constants can be labeled in *constants.dat*
* Comments can be added in *comments.dat*

The *.dat* files are opened from the current working directory.  Comments in
*.dat* files are specified with ';'.  Hex values need to be declared using '0x' or '0X' notation.

## Format of *.dat* files:

### *functions.dat* ###

    ; addr name
    0x0000 vmMain
      ; argX [size or type] name
      ;  or
      ; local addr [size or type] name
      arg0 int command
      local 0x14 commandTmp

    0x1223 CG_DrawAttacker
    0x28ae CG_Draw3DModel
      arg0 x
      local 0x18 0x170 refdef  ; also specifies the size
      local 0x300 vec3_t angles  ; specifies the type

Local variables can optionally specify a size, template type, or basic type to
identify references within a range.  See *symbols.dat* description for
information regarding ranges.  See *templates.dat* description for information
regarding template and types.

### *symbols.dat* ###

    ; addr [size or type] name
    0xab2a3 serverTime
    0xb23fa 0x1000 clientData

Size or type can optionally be specified to identify references within a range.
Symbol lookups without a size or type specified take precedence.  Multiple
ranges beginning at the same address are printed as a comma separated list.
Ex:

    0xe87c8 0x26754 cgs
      0xe87c8 0x4e84 cgs.gameState

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

Templates or types automatically fill in ranges.  See the *templates.dat*
section for a description of template types.  Ex:

    0xe87c8 0x26754 cgs
      0xe87c8 gameState_t cgs.gameState

output:

```00001051  const           1   0xe97c8   ; cgs.gameState.stringData[]```

### *constants.dat* ###

    ; addr name value
    0x3f31 DEFAULT_SPEED 0x0

The last value in the *contants.dat* entry is used to double check that the
value is correct.

### *comments.dat* ###

    ; addr inline comment...
    ;   or
    ; addr before|after [spaceBefore spaceAfter]
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

Before and after comments are terminated with a line that only has _'<<<'_.
They can also specify a number of blank lines before and after the comment.

A _'d'_ before the address specifies it's a data segment comment.

A _'@'_ character before the comment type (ex: _@before_) allows symbol and
function name replacement within the comment.  The format is
`@[d|f]{addr ...}`.  Text after the address and before the closing brace is
treated as a comment and discarded.  Ex:

    @f{0x89}
    @d{0xcba94 could be clientNum}

### *templates.dat* ###

    ; template [size]
    ; {
    ;    [offset] <size or type> name
    ;    ...
    ; }


    ; typedef struct {
    ;        cvarHandle_t    handle;
    ;        int             modificationCount;
    ;        float           value;
    ;        int             integer;
    ;        char            string[MAX_CVAR_VALUE_STRING];
    ; } vmCvar_t;

    %arrayConstant MAX_CVAR_VALUE_STRING 256
    %alias int cvarHandle_t

    vmCvar_t {
      cvarHandle_t handle
      int modificationCount
      float value
      int integer
      char[MAX_CVAR_VALUE_STRING] string
    }

    ; using explicit sizes and offsets:
    ;
    ; vmCvar_t 0x110
    ; {
    ;   0x0 cvarHandle_t handle
    ;   0x4 int modificationCount
    ;   0x8 float value
    ;   0xc int integer
    ;   0x10 char[MAX_CVAR_VALUE_STRING] string
    ; }

Templates allow the repeated specification of structures.

Default templates are loaded from the *templates-default.dat* file in the
installation directory.  To ignore those definitions, you can include an empty
*templates-default.dat* in the current directory.  *templates.dat* is read
after the default one and allows additional definitions and overriding of the
default ones.  Note that pointer references to templates use the string name so
overriding a template will also affect previously declared templates.

Template member declarations can use previously defined template types.

Pointers to templates/types are specified with '*'.  Ex:

    0xcbab0 *snapshot_t cg.snap
    ...
    0xf1f23 **buffer bx  ; pointer to pointer

If both pointer and array declarations are used the result will be an array of
pointers.  Ex:

    0xab922 *int[128] elements  ; elements[n] == pointer to integer

Template and member names can't contain spaces or start with a digit, '+', or
'-'.  Template names can't match basic type names or 'void'.

Basic types are:

      byte, char, uchar, short, ushort, int, uint, float

Template sizes and member offsets are optional.  If they are not specified
C style padding is applied.  Members will begin at offsets that are a multiple
of their basic type size.  Range types are not padded.  Template size is
padded based on the largest member padding.

Note that messages regarding dereferencing use '.' and '->' notation appended
to the symbol name.  Pointer and array declaractions can't contain spaces.
Template opening braces can be at the end of the same line as declarations or
be the first and single character in the subsequent line.  Template closing
braces need to be the first and single character in a line.

Defines for array sizes can be declared with `%arrayConstant name value`.  The
declaration can't be used while a template is currently being defined.
Constant names can't start with a digit, '+', or '-'.

Template aliases are string substitutions similar to C typedefs.  They are
declared as `%alias type aliasName`.  'type' can also be another alias.
