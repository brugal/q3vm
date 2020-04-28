#!/usr/bin/env python
import os, sys, tempfile
from pycparser import parse_file, c_ast


# if cpp or gcc not used to load ast, it can be preprocessed before hand:
#     gcc -nostdinc -m32 -I /usr/share/python-pycparser/fake_libc_include -E q_shared.h  > /share/tmp/q_shared-E-3.h


# to debug automatic size and offset calculations:
#     add common aliases to default template file (ex:  %alias int qboolean)
#
#     printcstruct.py --print-all --offset ~/tmp/sdk1/mod-sdk-1.32/code/game/q_shared.h > templates.dat
#     templateinfo --no-comments --print-all > /tmp/all-offset.txt
#
#     printcstruct.py --print-all ~/tmp/sdk1/mod-sdk-1.32/code/game/q_shared.h > templates.dat
#     templateinfo --no-comments --print-all > /tmp/all-c-no-type.txt
#
#     diff -Naurbd /tmp/all-offset.txt /tmp/all-c-no-type.txt


# pycparser fake typedef struct from: /usr/share/python[3]-pycparser/fake_libc_include/_fake_typedefs.h
fakeStructs = [ "MirConnection", "MirSurface", "MirSurfaceSpec", "MirScreencast", "MirPromptSession", "MirBufferStream", "MirPersistentId", "MirBlob", "MirDisplayConfig", "xcb_connection_t" ]

def usage ():
    sys.stderr.write("%s [--debug, --debug-node, --print-all, --offset] <c file> [name]\n" % os.path.basename(sys.argv[0]))
    sys.exit(1)

def output (msg):
    sys.stdout.write(msg)

def error_msg (msg):
    sys.stderr.write("ERROR: %s\n" % msg)

def error_exit (msg):
    error_msg(msg)
    sys.exit(1)

# from CFFI  https://cffi.readthedocs.io/en/latest/  : _parse_constant()

def parse_binaryop (exprnode, partial_length_ok=False):
    # for now, limited to expressions that are an immediate number
    # or positive/negative number
    if isinstance(exprnode, c_ast.Constant):
        s = exprnode.value
        if s.startswith('0'):
            if s.startswith('0x') or s.startswith('0X'):
                return int(s, 16)
            return int(s, 8)
        elif '1' <= s[0] <= '9':
            return int(s, 10)
        elif s[0] == "'" and s[-1] == "'" and (
                len(s) == 3 or (len(s) == 4 and s[1] == "\\")):
            return ord(s[-2])
        else:
            #raise CDefError("invalid constant %r" % (s,))
            error_exit("invalid constant %r" % (s,))
    #
    if (isinstance(exprnode, c_ast.UnaryOp) and
            exprnode.op == '+'):
        return parse_binaryop(exprnode.expr)
    #
    if (isinstance(exprnode, c_ast.UnaryOp) and
            exprnode.op == '-'):
        return -parse_binaryop(exprnode.expr)

    # load previously defined int constant
    ##if (isinstance(exprnode, c_ast.ID) and
    ##        exprnode.name in self._int_constants):
    ##    return self._int_constants[exprnode.name]
    #
    ##if (isinstance(exprnode, pycparser.c_ast.ID) and
    ##            exprnode.name == '__dotdotdotarray__'):
    ##    if partial_length_ok:
    ##        self._partial_length = True
    ##        return '...'
    ##    raise FFIError(":%d: unsupported '[...]' here, cannot derive "
    ##                   "the actual array length in this context"
    ##                   % exprnode.coord.line)

    #
    if (isinstance(exprnode, c_ast.BinaryOp) and
            exprnode.op == '+'):
        return (parse_binaryop(exprnode.left) +
                parse_binaryop(exprnode.right))
    #
    if (isinstance(exprnode, c_ast.BinaryOp) and
            exprnode.op == '-'):
        return (parse_binaryop(exprnode.left) -
                parse_binaryop(exprnode.right))
    if (isinstance(exprnode, c_ast.BinaryOp) and
	    exprnode.op == '*'):
        return (parse_binaryop(exprnode.left) *
                parse_binaryop(exprnode.right))
    if (isinstance(exprnode, c_ast.BinaryOp) and
            exprnode.op == '/'):
        return (parse_binaryop(exprnode.left) /
                parse_binaryop(exprnode.right))

    #
    ##raise FFIError(":%d: unsupported expression: expected aw "
    ##               "simple numeric constant" % exprnode.coord.line)
    error_exit(":%d: unsupported expression: expected a simple numeric constant: %s" % (exprnode.coord.line, exprnode))

# t: c_ast.IdentifierType
def convert_identifier_type (t):
    if type(t) != c_ast.IdentifierType:
        error_exit("convert_identifier_type() unknown type: %s" % type(t))
    if len(t.names) < 1:
        error_exit("convert_identifier_type() empty names array")

    #print("convert_identifier_type()  names: %s" % t.names)

    if len(t.names) == 1:
        return t.names[0]

    if len(t.names) > 1:
        if t.names[1] == "char":
            if t.names[0] == "signed":
                return "char"
            elif t.names[0] == "unsigned":
                return "uchar"
            else:
                error_exit("convert_identifier_type() unknown char type: %s" % t.names[0])
        elif t.names[1] == "short":
            if t.names[0] == "signed":
                return "short"
            elif t.names[0] == "unsigned":
                return "ushort"
            else:
                error_exit("convert_identifier_type() unknown short type: %s" % t.names[0])
        elif t.names[1] == "int":
            if t.names[0] == "signed":
                return "int"
            elif t.names[0] == "unsigned":
                return "uint"
            else:
                error_exit("convert_identifier_type() unknown int type: %s" % t.names[0])
        else:
            error_exit("convert_identifier_type() unknown type: %s" % t.names)

# structNames: [ name1:str, name2:str, ... ]
# arrayConstants: dotname:str -> [ level1:str, level2:str, ... ]

def print_struct_offset (ast, cFileName, printAll=False, structNames=[], arrayConstants={}, debugLevel=0):
    # use gcc to print offset info
    codeFile = tempfile.NamedTemporaryFile(prefix="qvmdis-struct-", suffix=".c", delete=False)

    codeFile.write("#include <stdio.h>\n")
    codeFile.write("#include <stddef.h>\n")
    codeFile.write("#include \"%s\"\n" % cFileName)
    codeFile.write("\n")
    codeFile.write("int main (int argc, char *argv[]) {\n")

    for node in ast.ext:

        # typedef struct [name] { ... } tname;
        # struct name { ... };

        if (type(node) == c_ast.Typedef  and  type(node.type) == c_ast.TypeDecl  and  type(node.type.type) == c_ast.Struct)  or  (type(node) == c_ast.Decl  and  type(node.type) == c_ast.Struct):

            if type(node) == c_ast.Typedef  and  type(node.type) == c_ast.TypeDecl  and  type(node.type.type) == c_ast.Struct:  # typedef ...
                isTypedef = True
                structNode = node.type.type
                structName = node.name
            else:  # struct ...
                isTypedef = False
                structNode = node.type
                structName = structNode.name

            if not printAll  and  structName not in structNames:
                continue

            if structName in fakeStructs:
                continue

            if debugLevel > 0:
                if debugLevel > 1:
                    output("%s : \n" % node.name)
                    output("%s\n\n" % node)
                output("%s (members) : \n" % structName)
                output("%s\n" % structNode.decls)
                output("\n")

            codeFile.write("  {\n")
            if isTypedef:
                codeFile.write("    %s st;\n" % structName)
            else:
                codeFile.write("    struct %s st;\n" % structName)
            codeFile.write("\n")

            if isTypedef:
                codeFile.write("    printf(\"%s 0x%%x {\\n\", sizeof(%s));\n" % (structName, structName))
            else:
                codeFile.write("    printf(\"%s 0x%%x {\\n\", sizeof(struct %s));\n" % (structName, structName))

            # struct members
            for m in structNode:
                if isTypedef:
                    codeFile.write("    printf(\"  0x%%x 0x%%x %s\\n\", offsetof(%s, %s), sizeof(%s));\n" % (m.name, structName, m.name, "st." + m.name))
                else:
                    codeFile.write("    printf(\"  0x%%x 0x%%x %s\\n\", offsetof(struct %s, %s), sizeof(%s));\n" % (m.name, structName, m.name, "st." + m.name))

            codeFile.write("    printf(\"}\\n\\n\");\n")
            codeFile.write("  }\n")
            codeFile.write("\n")

    codeFile.write("    return 0;\n")
    codeFile.write("}\n")

    codeFile.close()
    if debugLevel > 0:
        output("%s :\n" % codeFile.name)
        f = open(codeFile.name)
        data = f.read()
        f.close()
        output(data)
        output("\n")

    binFileName = codeFile.name + ".bin"
    os.system("gcc -Wall -m32 %s -o %s" % (codeFile.name, binFileName))
    os.system(binFileName)

    os.unlink(codeFile.name)
    os.unlink(binFileName)

# structNames: [ name1:str, name2:str, ... ]
# arrayConstants: dotname:str -> [ level1:str, level2:str, ... ]

def print_struct (ast, printAll=False, structNames=[], arrayConstants={}, debugLevel=0):

    for node in ast.ext:

        # typedef struct [name] { ... } tname;
        # struct name { ... };

        if (type(node) == c_ast.Typedef  and  type(node.type) == c_ast.TypeDecl  and  type(node.type.type) == c_ast.Struct)  or  (type(node) == c_ast.Decl  and  type(node.type) == c_ast.Struct):

            if type(node) == c_ast.Typedef  and  type(node.type) == c_ast.TypeDecl  and  type(node.type.type) == c_ast.Struct:  # typedef ...
                structNode = node.type.type
                structName = node.name
            else:  # struct ...
                structNode = node.type
                structName = structNode.name

            if not printAll  and  structName not in structNames:
                continue

            if structName in fakeStructs:
                continue

            if debugLevel > 0:
                if debugLevel > 1:
                    output("%s : \n" % node.name)
                    output("%s\n\n" % node)
                output("%s (members) : \n" % structName)
                output("%s\n" % structNode.decls)
                output("\n")

            output("%s {\n" % structName)

            # struct members
            for m in structNode:
                mType = type(m.type)

                # straight declaration, ex: int count
                if mType == c_ast.TypeDecl:
                    if type(m.type.type) == c_ast.IdentifierType:
                        output("    %s %s\n" % (convert_identifier_type(m.type.type), m.name))
                    else:
                        error_exit("not IdentifierType for %s: %s" % (m.name, type(m.type.type)))
                # pointer (straight declaration or function), ex: float *range, int (*func)(int a, int b)
                elif mType == c_ast.PtrDecl:
                    if type(m.type.type) == c_ast.TypeDecl:
                        if type(m.type.type.type) == c_ast.IdentifierType:
                            output("    *%s %s\n" % (convert_identifier_type(m.type.type.type), m.name))
                        elif type(m.type.type.type) == c_ast.Struct:
                            # check if this is pointer to self
                            if m.type.type.type.name == structName:
                                output("    *%s %s\n" % (node.name, m.name))
                            else:
                                output("    *%s %s\n" % (m.type.type.type.name, m.name))
                        else:
                            error_exit("not IdentifierType for pointer %s: %s" % (m.name, type(m.type.type.type)))
                    elif type(m.type.type) == c_ast.FuncDecl:
                        # just a straight pointer in qvmdis
                        #FIXME what would 'int (*func)(int a, int b)[100]' be considered as?
                        output("    *void %s\n" % m.name)
                    else:
                        error_exit("not TypeDecl for pointer %s: %s" % (m.name, type(m.type.type)))
                # arrays, ex: char word[256]...  or  char *strings[256]...
                elif mType == c_ast.ArrayDecl:
                    arrayLengths = []

                    if type(m.type.dim) == c_ast.Constant:
                        arrayLengths.append(m.type.dim.value)
                    elif type(m.type.dim) == type(None):
                        # ex:  char unk[]
                        error_exit("flexible array member not supported: %s" % m.name)
                    elif type(m.type.dim) == c_ast.BinaryOp:
                        arrayLengths.append(parse_binaryop(m.type.dim))
                    elif type(m.type.dim) == c_ast.ID:
                        # one example is Enum as array length
                        #FIXME ID used with math expression: arr[MAX_VAL + 2]
                        arrayLengths.append(m.type.dim.name)
                    else:
                        error_exit("unknown array dim type for %s: %s" % (m.name, type(m.type.dim)))
                    subType = m.type.type

                    while type(subType) == c_ast.ArrayDecl:
                        if type(subType.dim) == c_ast.Constant:
                            #FIXME check dim.type == 'int' ?, ex: int x[2.2]
                            arrayLengths.append(subType.dim.value)
                        elif type(subType.dim) == type(None):
                            # ex:  char[200[]
                            error_exit("flexible sub array member not supported: %s" % m.name)
                        elif type(subType.dim) == c_ast.BinaryOp:
                            arrayLengths.append(parse_binaryop(subType.dim))
                        elif type(subType.dim) == c_ast.ID:
                            # one example is Enum as array length
                            arrayLengths.append(subType.dim.name)
                        else:
                            error_exit("unknown sub array dim type for %s: %s" % (m.name, type(subType.dim)))
                        subType = subType.type

                    if type(subType) == c_ast.TypeDecl  or  type(subType) == c_ast.PtrDecl:
                        if type(subType) == c_ast.PtrDecl:
                            isPointer = True
                            subType = subType.type
                        else:
                            isPointer = False

                        if type(subType.type) == c_ast.IdentifierType:
                            arrayTypeName = convert_identifier_type(subType.type)
                        elif isPointer  and  type(subType) == c_ast.FuncDecl:
                            # ex:  int (*func[36])(int a, int b)
                            error_exit("array of function pointers not supported: %s" % m.name)
                        else:
                            error_exit("unknown array typedecl identifier for %s: %s" % (m.name, type(subType.type)))

                        if isPointer:
                            output("    *%s" % arrayTypeName)
                        else:
                            output("    %s" % arrayTypeName)

                        dotName = node.name + "." + m.name
                        if dotName in arrayConstants:
                            ac = arrayConstants[dotName]
                            for a in ac:
                                output("[%s]" % a)
                        else:
                            for a in arrayLengths:
                                output("[%s]" % a)
                        output(" %s\n" % m.name)
                    else:
                        error_exit("unknown array type for %s: %s" % (m.name, type(m.type.type)))
                else:
                    error_exit("unhandled type for %s: %s\n" % (m.name, mType))
            output("}\n\n")

if __name__ == "__main__":
    debugLevel = 0
    printAll = False
    useOffset = False

    args = []
    args.append(sys.argv[0])
    checkDashOptions = True
    for a in sys.argv[1:]:
        if checkDashOptions:
            if a == "--":
                # all done, pass the rest as is
                checkDashOptions = False
            elif a[0] != '-':
                args.append(a)
                checkDashOptions = False
            elif a == "--debug":
                debugLevel = 1
            elif a == "--debug-node":
                debugLevel = 2
            elif a == "--print-all":
                printAll = True
            elif a == "--offset":
                useOffset = True
            else:
                sys.stderr.write("unknown option: %s\n" % a)
                sys.exit(1)
        else:
            args.append(a)

    # c file required
    if len(args) < 2:
        error_msg("missing c file name")
        usage()

    cFileName = args[1]

    if not printAll  and  len(args) < 3:
        error_msg("missing structure name")
        usage()

    if len(args) > 2:
        structNames = [args[2]]
    else:
        structNames = []

    arrayConstants = {}
    # testing
    #arrayConstants["pc_token_t.string"] = ["MAX_TOKENLENGTH"]

    #ast = parse_file(filename=cFileName)
    #ast = parse_file(filename=cFileName, use_cpp=True, cpp_path='cpp', cpp_args=r'-Iutils/fake_libc_include')
    ast = parse_file(filename=cFileName, use_cpp=True, cpp_path='gcc', cpp_args=['-nostdinc', '-m32', '-I', '/usr/share/python-pycparser/fake_libc_include', '-S', '-E'])
    #ast.show()

    if useOffset:
        print_struct_offset(ast, cFileName=cFileName, structNames=structNames, arrayConstants=arrayConstants, printAll=printAll, debugLevel=debugLevel)
    else:
        print_struct(ast, structNames=structNames, arrayConstants=arrayConstants, printAll=printAll, debugLevel=debugLevel)
