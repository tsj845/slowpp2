import re
import sys

ASS, MAT, LOG, INT, STR, BOL, FLO, LST, DCT, PAR, DOT, SEP, SYM, SLF, OBJ, NUL, KWD, EQU, FUN, REF, CON = "ASS", "MAT", "LOG", "INT", "STR", "BOL", "FLO", "LST", "DCT", "PAR", "DOT", "SEP", "SYM", "SLF", "OBJ", "NUL", "KWD", "EQU", "FUN", "REF", "CON"

class Token ():
    def __init__ (self, type, value):
        self.type = type
        self.value = value
    def equal (self, type, value):
        return (self.type == type and self.value == value)
    def __repr__ (self):
        return f"({self.type}, \"{self.value}\")"
    def __eq__ (self, comp):
        if (isinstance(comp, Token)):
            return comp.type == self.type and comp.value == self.value
        return False

class Namespace ():
    def __init__ (self, value, parent):
        self.parent = parent
        self.value = value
        self.audit = False
        self.zavls = (0,)
        self.auditstate = 0
    def keys (self):
        return self.value.keys()
    def __getitem__ (self, key):
        if (self.audit and not self.parent.auditing and ((len(self.parent.auditvars) == 0 and self.auditstate in self.zavls) or key in self.parent.auditvars)):
            print(key, self.value[key], "NAMESPACE GET")
        return self.value[key]
    def __setitem__ (self, key, value):
        self.value[key] = value
        if (self.audit and not self.parent.auditing and ((len(self.parent.auditvars) == 0 and self.auditstate in self.zavls) or key in self.parent.auditvars)):
            print(key, value, "NAMESPACE SET")

class NamespaceList ():
    def __init__ (self, consts):
        self.auditing = False
        self.scopes = [Namespace(consts, self), Namespace({}, self)]
        self.scopes[1].audit = True
        self.auditvars = []
    def audit_state (self, index, value):
        if (index >= 0 and index < len(self.scopes)):
            self.scopes[index].auditstate = value
    def add_audit (self, vname):
        if (vname not in self.auditvars):
            self.auditvars.append(vname)
    def remove_audit (self, vname):
        if (vname in self.auditvars):
            self.auditvars.pop(self.auditvars.index(vname))
    def __len__ (self):
        return len(self.scopes)
    def __getitem__ (self, ind):
        return self.scopes[ind]
    def __setitem__ (self, ind, value):
        self.scopes[ind] = value

class InterPalette ():
    def __init__ (self):
        self.reset = "\x1b[39m"
        self.audit = "\x1b[38;2;200;100;0m"
        self.error = "\x1b[38;2;255;0;0m"
        self.warning = "\x1b[38;2;255;255;0m"
        self.output = "\x1b[38;2;0;100;200m"
        self.validcolornames = ("reset", "audit", "error", "warning", "output")
    def has (self, attr):
        return (attr in self.validcolornames)
    def __setitem__ (self, key, value):
        if (key == "reset"):
            self.reset = value
        elif (key == "audit"):
            self.audit = value
        elif (key == "error"):
            self.error = value
        elif (key == "warning"):
            self.warning = value
        elif (key == "output"):
            self.output = value

ansire = re.compile("\\\\x1b\[\d{2,2};\d{1,1};\d{1,3};\d{1,3};\d{1,3}m")

class Interpreter ():
    def __init__ (self, filename="code"):
        self.mec = 0
        self.lines = []
        self.keywords = ("func", "if", "elif", "else", "for", "while", "in", "break", "continue", "python", "search", "switch", "return", "case", "default", "class", "global", "flag", "audit", "watch", "color", "dump")
        self.flags = {"vars":False}
        self.nonmod = (REF, NUL, INT, STR, PAR, DCT, LST, BOL, FLO, OBJ, KWD)
        # sets up variable scopes, top level scope is readonly constants and second scope is the program global scope, all other scopes are local scopes
        self._scopes = NamespaceList({"true":Token(BOL, True), "false":Token(BOL, False), "void":Token(NUL, None)})
        self._scopes.audit_state(1, 1)
        self.colors = InterPalette()
        self._getData(filename)
        self.run()
    @property
    def scopes (self):
        return self._scopes
    @scopes.setter
    def vars (self, value):
        self._scopes = value
    def _getData (self, filename : str):
        f = open(filename+("" if filename.endswith(".spp") else ".spp"))
        data = f.read()
        f.close()
        self.lines = data
    def breaklines (self, data):
        data = data.replace("\\n", "\n")
        data = data.split("\n")
        inlen = len(data)-1
        isstr = False
        for i in range(len(data)):
            i = inlen-i
            if (i >= len(data)):
                break
            line = data[i]
            if (line.count('"') % 2 != 0):
                if (isstr):
                    line = line + "\n" + data.pop(i+1)
                    data[i] = line
                isstr = not isstr
            elif (isstr):
                line += "\n" + data.pop(i+1)
                data[i] = line
        return data
    def tokenize (self, line : str) -> list:
        tokens = []
        i = 0
        while i < len(line):
            char = line[i]
            if (char == "\n" or char == ";"):
                i += 1
                continue
            elif (i < len(line)-1 and line[i:i+2] == "//"):
                found = False
                isstr = False
                while i < len(line):
                    if (line[i] == '"' and line[i-1] != "\\"):
                        isstr = not isstr
                    if (line[i] == "\n" and not isstr):
                        found = True
                        break
                    i += 1
                if (not found):
                    break
            elif (char in "+-*/%"):
                if (i < len(line)-1 and line[i+1] == "="):
                    tokens.append(Token(ASS, char+"="))
                    i += 2
                    continue
                tokens.append(Token(MAT, char))
            elif (char == "="):
                if (i < len(line)-1 and line[i:i+1] == "=="):
                    tokens.append(Token(EQU, "=="))
                    i += 2
                    continue
                tokens.append(Token(ASS, char))
            elif (char in "!&|^<>"):
                if (i < len(line)-1 and line[i+1] == "="):
                    tokens.append(Token(EQU, char+"="))
                    i += 2
                    continue
                tokens.append(Token(LOG, char))
            elif (char in "{}"):
                tokens.append(Token(DCT, char))
            elif (char in "[]"):
                tokens.append(Token(LST, char))
            elif (char in "()"):
                tokens.append(Token(PAR, char))
            elif (char == "."):
                tokens.append(Token(DOT, char))
            elif (char == ","):
                tokens.append(Token(SEP, char))
            elif (char in ":"):
                tokens.append(Token(SYM, char))
            elif (char == '"'):
                found = False
                ci = i+1
                while ci < len(line):
                    if (line[ci] == '"' and line[ci-1] != "\\"):
                        found = True
                        break
                    ci += 1
                if (not found):
                    # unclosed string
                    raise Exception(2)
                tokens.append(Token(STR, '"'+line[i+1:ci]+'"'))
                i = ci
            elif (char.isdigit()):
                fin = ""
                s = i
                deciuse = False
                while line[s].isdigit() and s < len(line):
                    c = line[s]
                    fin += c
                    s += 1
                    if (s >= len(line)):
                        break
                    if (line[s] == "."):
                        if (deciuse):
                            break
                        if (line[s+1] == "."):
                            break
                        if (line[s+1].isalpha()):
                            break
                        deciuse = True
                        fin += "."
                        s += 1
                    if (s >= len(line)):
                        break
                i = s
                tokens.append(Token(FLO if deciuse else INT, float(fin) if deciuse else int(fin)))
            else:
                found = False
                for keyword in self.keywords:
                    if (len(line)-i >= len(keyword)):
                        test = line[i:i+len(keyword)]
                        if (test == keyword):
                            found = True
                            tokens.append(Token(KWD, test))
                            if (keyword == "flag"):
                                sec = line[i:(i+line[i:].index("\n")) if "\n" in line[i:] else i+len(line[i:])].split(" ")
                                tokens.append(Token(CON, (sec[1], sec[2][:-1 if sec[2][-1] == "\n" else len(sec[2])])))
                                i += len(" ".join(sec))
                                break
                            if (keyword == "color"):
                                rest = line[i + len(keyword) + 1:]
                                v = line[i + len(keyword) + 1:(rest.index("\n")+i+len(keyword)+1) if "\n" in rest else len(line)]
                                # print("\x1b[38;2;200;100;0mcolor kwd\x1b[39m", v)
                                i += len(v) + len(keyword) + 1
                                v = v.split(" ")
                                v = v[:min(2, len(v))]
                                if (len(v) < 2):
                                    break
                                if (self.colors.has(v[0])):
                                    # print(v[1], ansire.fullmatch(v[1]), ansire.match(v[1]))
                                    if (ansire.fullmatch(v[1])):
                                        tokens.append(Token("color", v[0]))
                                        tokens.append(Token("color", v[1].replace("\\x1b", "\x1b")))
                                    else:
                                        commoncolors = {"lime":"\x1b[38;2;0;255;0m","green":"\x1b[38;2;0;200;0m","orange":"\x1b[38;2;200;100;0m","yellow":"\x1b[38;2;255;255;0m","red":"\x1b[38;2;255;0;0m"}
                                        if (v[1] not in commoncolors.keys()):
                                            break
                                        tokens.append(Token("color", v[0]))
                                        tokens.append(Token("color", commoncolors[v[1]]))
                                break
                            if (keyword == "audit"):
                                if (len(line) > i + len(keyword) and line[i + len(keyword)] == " "):
                                    rest = line[i + len(keyword) + 1:]
                                    v = line[i + len(keyword) + 1:(rest.index("\n")+i+len(keyword)+1) if "\n" in rest else len(line)]
                                    if (self.deref(v, check=True)):
                                        tokens.append(Token("audit", v))
                                    else:
                                        print(f"{self.colors.output}{v}{self.colors.reset}", len(v))
                                    i += len(v) + 1
                                i += len(keyword)
                                break
                            if (keyword == "dump"):
                                if (len(line) > i + len(keyword) and line[i + len(keyword)] == " "):
                                    rest = line[i + len(keyword) + 1:]
                                    v = line[i + len(keyword) + 1:(rest.index("\n")+i+len(keyword)+1) if "\n" in rest else len(line)]
                                    if (v in ("global", "local", "constant")):
                                        tokens.append(Token("dump", v))
                                    else:
                                        print(f"{self.colors.output}{v}{self.colors.reset}", len(v))
                                    i += len(v) + 1
                                i += len(keyword)
                                break
                            if (keyword == "watch"):
                                rest = line[i + len(keyword) + 1:]
                                if ("\n" not in rest):
                                    raise Exception(3)
                                end = rest.index("\n")+i+len(keyword)+1
                                v = line[i + len(keyword) + 1:end]
                                i = end
                                self._scopes.add_audit(v)
                                break
                            if (keyword == "python"):
                                if (line[i + len(keyword)] == "{" or line[i + len(keyword):i + len(keyword) + 2] == " {"):
                                    tstart = i+len(keyword)+(1 if line[i + len(keyword)] != "{" else 0)
                                    test = line[tstart:]
                                    t2 = test[2:]
                                    i2 = 0
                                    depth = 1
                                    while i2 < len(t2):
                                        if (t2[i2] == "{"):
                                            depth += 1
                                        if (t2[i2] == "}"):
                                            depth -= 1
                                        if (depth == 0):
                                            break
                                        i2 += 1
                                    t2 = t2[:i2-1]
                                    tokens.append(Token("python", t2))
                                    i = tstart + i2 + 3
                                break
                            i += len(keyword)
                            break
                if (found):
                    continue
                ti = i
                while ti < len(line):
                    if (not line[ti].isalnum() and not line[ti] == "_"):
                        break
                    ti += 1
                if (ti != i):
                    tokens.append(Token(REF, line[i:ti]))
                self.tokens = tokens
                if (ti == i):
                    ti += 1
                i = ti
                continue
            i += 1
        return tokens
    def pythonFunc (self, tokens):
        return Token(NUL, None)
    def doPython (self, data):
        code = data["code"]
        code = self.breaklines(code)
        for i in range(len(code)):
            code[i] = code[i].removeprefix("\t")
        code[0] = "\t"+code[0]
        code = "\n\t".join(code)
        code = "def private ():\n"+code+"\nglobal f\nf = private"
        if ("globals" in data):
            exec(code, data["globals"], data["locals"] if "locals" in data else data["globals"])
        else:
            exec(code)
        result = f()
        if (type(result) == str):
            result = '"' + result + '"'
        return Token(NUL, None)
    def deref (self, token, /, check=False):
        if (check):
            for i in range(len(self.scopes)):
                scope = self.scopes[-1-i]
                if (token in scope.keys()):
                    return True
                else:
                    print(scope.keys())
            return False
        for i in range(len(self.scopes)):
            scope = self.scopes[-1-i]
            if (token.value in scope.keys()):
                return scope[token.value]
        raise Exception(3)
    def domod (self, base, op, mod):
        if (mod.type == REF):
            mod = self.deref(mod)
        if (base.type == REF):
            base = self.deref(base)
        isstr = False
        modstr = False
        if (base.type == STR):
            isstr = True
            base.value = base.value[1:-1]
        if (mod.type == STR):
            modstr = True
            mod.value = mod.value[1:-1]
        op = op.value
        result = None
        if (op == "+"):
            result = base.value + mod.value
        elif (op == "-"):
            result = base.value - mod.value
        elif (op == "*"):
            result = base.value * mod.value
        elif (op == "/"):
            if (mod.value == 0):
                raise Exception(6)
            result = base.value / mod.value
        elif (op == "%"):
            result = base.value % mod.value
        if (isstr):
            result = '"' + result + '"'
            base.value = '"' + base.value + '"'
        if (modstr):
            mod.value = '"' + mod.value + '"'
        return Token(base.type, result)
    def getexp (self, tokens, start):
        i = start+2
        result = tokens[start+1]
        if (result.type == REF):
            result = self.deref(result)
        while i < len(tokens):
            token = tokens[i]
            if (token.type in self.nonmod):
                break
            ret = self.domod(result, token, tokens[i+1])
            if (ret == None):
                break
            result = ret
            i += 2
        i -= 1
        return result, i
    def getfunc (self, tokens, start):
        i = start+2
        depth = 1
        args = []
        build = []
        ftoks = []
        result = None
        while i < len(tokens):
            token = tokens[i]
            if (token.type == PAR):
                if (token.value == "("):
                    depth += 1
                else:
                    depth -= 1
                if (depth == 0):
                    break
            elif (token.type == SEP):
                args.append(tuple(build))
                build = []
            else:
                build.append(token)
            i += 1
        depth = 1
        i += 1
        while i < len(tokens):
            token = tokens[i]
            if (token.type == DCT):
                if (token.value == "{"):
                    depth += 1
                else:
                    depth -= 1
                if (depth == 0):
                    break
            else:
                ftoks.append(token)
            i += 1
        result = Token(FUN, (tuple(args), tuple(ftoks)))
        return result, i
    def _perr (self, type, value):
        print(f"{self.colors.error}{type}: {value}{self.colors.reset}")
    def err (self, code):
        if (code == 0):
            self._perr("UnkownError", "unkown error occured")
        elif (code == 1):
            self._perr("ConstantAssignmentError", "cannot assign to constant value")
        elif (code == 2):
            self._perr("UnclosedStringError", "unclosed string")
        elif (code == 3):
            self._perr("UndefinedNameError", "variable name not defined")
        elif (code == 4):
            self._perr("WatchError", "watch statement is not followed by more code")
        elif (code == 5):
            self._perr("OperationTypeError", "invalid type(s) for operation")
        elif (code == 6):
            self._perr("ZeroDivisionError", "cannot devide by zero")
    def evaltokens (self, tokens):
        if (type(tokens) == str):
            tokens = self.tokenize(tokens)
        print(self.colors.output, tokens.index(Token(KWD, "color")), self.colors.reset)
        tind = 0
        while tind < len(tokens):
            token = tokens[tind]
            if (token.type == KWD):
                if (token.value == "python"):
                    if (tokens[tind+1].type == "python"):
                        tokens[tind] = self.doPython({"code":tokens[tind+1].value})
                    else:
                        tokens[tind] = self.pythonFunc(tokens[tind:])
                    tokens.pop(tind+1)
                elif (token.value == "func"):
                    name = tokens[tind+1].value
                    if (name in self.scopes[0].keys()):
                        # assignment to constant
                        raise Exception(1)
                    self.scopes[-1][name], tind = self.getfunc(tokens, tind)
                elif (token.value == "audit"):
                    print(tokens[tind:])
                    print(f"{self.colors.audit}AUDIT:{self.colors.reset}")
                    if (len(tokens) > tind+1 and tokens[tind+1].type == "audit"):
                        self._printvar(tokens[tind+1].value)
                        tind += 1
                    else:
                        self._printvars()
                elif (token.value == "color"):
                    # print(f"{self.colors.output}{tokens[tind+1].value}, {tokens[tind+2].value[1:]}{self.colors.reset}")
                    self.colors[tokens[tind+1].value] = tokens[tind+2].value
                    tind += 2
                elif (token.value == "dump"):
                    self._dump(tokens[tind+1].value)
                    tind += 1
            elif (token.type == CON):
                self.flags[token.value[0]] = {"on":True, "off":False, "switch":not self.flags[token.value[0]]}[token.value[1]]
            elif (token.type == ASS):
                if (token.value == "="):
                    if (self.tokens[tind-1].value in self.scopes[0].keys()):
                        # assignment to constant
                        raise Exception(1)
                    self.scopes[-1][self.tokens[tind-1].value], tind = self.getexp(tokens, tind)
                else:
                    tokens.insert(tind+1, Token(MAT, token.value[0]))
                    tokens.insert(tind+1, Token(REF, tokens[tind-1].value))
                    tokens[tind] = Token(ASS, "=")
                    continue
            elif (token.type == FUN):
                pass
                # self.runfun
            tind += 1
    def _dump (self, scope):
        index = 1 if scope == "global" else len(self.scopes) - 1 if scope == "local" else 0
        print(f"{self.colors.output}dumping {scope} scope:{self.colors.reset}")
        scope = self.scopes[index]
        for key in scope.keys():
            print(f"{key} : {scope[key]}")
    def _printvar (self, vname):
        self._scopes.auditing = True
        scopes = self.scopes[1:]
        for i in range(len(scopes)):
            scope = scopes[i]
            if (vname in scope.keys()):
                print("globa scope:" if i == 0 else f"local scope ({i}):", end=" ")
                print(f"{vname} = {scope[vname]}")
        self._scopes.auditing = False
    def _printvars (self):
        self._scopes.auditing = True
        scopes = self.scopes[1:]
        for i in range(len(scopes)):
            scope = scopes[i]
            print("global scope:" if i == 0 else f"local scope ({i}):")
            for key in scope.keys():
                print(f"\t{key} : {scope[key]}")
        self._scopes.auditing = False
    def run (self):
        self.mec = 6
        errinfo = None
        try:
            self.evaltokens(self.lines)
        except Exception:
            info = sys.exc_info()
            print(self.mec)
            if (info[1].args[0] >= 0 and info[1].args[0] <= self.mec and info[0] == Exception):
                errinfo = info[1].args[0]
            else:
                raise info[1]
        if (self.flags["vars"]):
            self._printvars()
        if (errinfo != None):
            self.err(errinfo)

inter = Interpreter()