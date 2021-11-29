ASS, MAT, LOG, INT, STR, BOL, FLO, LST, DCT, PAR, DOT, SEP, SYM, SLF, OBJ, NUL, KWD, EQU, FUN, REF, CON = "ASS", "MAT", "LOG", "INT", "STR", "BOL", "FLO", "LST", "DCT", "PAR", "DOT", "SEP", "SYM", "SLF", "OBJ", "NUL", "KWD", "EQU", "FUN", "REF", "CON"

class Token ():
    def __init__ (self, type, value):
        self.type = type
        self.value = value
    def equal (self, type, value):
        return (self.type == type and self.value == value)
    def __repr__ (self):
        return f"({self.type}, \"{self.value}\")"

class Namespace ():
    def __init__ (self, value):
        self.value = value
        self.audit = False
    def keys (self):
        return self.value.keys()
    def __getitem__ (self, key):
        if self.audit:
            print(key, self.value[key], "NAMESPACE GET")
        return self.value[key]
    def __setitem__ (self, key, value):
        self.value[key] = value
        if self.audit:
            print(key, value, "NAMESPACE SET")

class NamespaceList ():
    def __init__ (self, consts):
        self.scopes = [Namespace(consts), Namespace({})]
        self.scopes[1].audit = True
    def __len__ (self):
        return len(self.scopes)
    def __getitem__ (self, ind):
        return self.scopes[ind]
    def __setitem__ (self, ind, value):
        self.scopes[ind] = value

class Interpreter ():
    def __init__ (self, filename="code"):
        self.lines = []
        self.keywords = ("func", "if", "elif", "else", "for", "while", "in", "break", "continue", "python", "search", "switch", "return", "case", "default", "class", "global", "flag", "audit")
        self.flags = {"vars":False}
        self.nonmod = (REF, NUL, INT, STR, PAR, DCT, LST, BOL, FLO, OBJ, KWD)
        # sets up variable scopes, top level scope is readonly constants and second scope is the program global scope, all other scopes are local scopes
        self._scopes = NamespaceList({"true":Token(BOL, True), "false":Token(BOL, False), "void":Token(NUL, None)})
        # self._scopes = [{"true":Token(BOL, True), "false":Token(BOL, False), "void":Token(NUL, None)}, {}]
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
            if i >= len(data):
                break
            line = data[i]
            if line.count('"') % 2 != 0:
                if isstr:
                    line = line + "\n" + data.pop(i+1)
                    data[i] = line
                isstr = not isstr
            elif isstr:
                line += "\n" + data.pop(i+1)
                data[i] = line
        return data
    def tokenize (self, line : str) -> list:
        # print("\\n".join(line.split("\n")))
        tokens = []
        i = 0
        while i < len(line):
            char = line[i]
            if char == "\n" or char == ";":
                i += 1
                continue
            elif i < len(line)-1 and line[i:i+2] == "//":
                found = False
                isstr = False
                while i < len(line):
                    if line[i] == '"' and line[i-1] != "\\":
                        isstr = not isstr
                    if line[i] == "\n" and not isstr:
                        found = True
                        break
                    i += 1
                if not found:
                    break
            elif char in "+-*/%":
                if i < len(line)-1 and line[i+1] == "=":
                    tokens.append(Token(ASS, char+"="))
                    i += 2
                    continue
                tokens.append(Token(MAT, char))
            elif char == "=":
                if i < len(line)-1 and line[i:i+1] == "==":
                    tokens.append(Token(EQU, "=="))
                    i += 2
                    continue
                tokens.append(Token(ASS, char))
            elif char in "!&|^<>":
                if i < len(line)-1 and line[i+1] == "=":
                    tokens.append(Token(EQU, char+"="))
                    i += 2
                    continue
                tokens.append(Token(LOG, char))
            elif char in "{}":
                tokens.append(Token(DCT, char))
            elif char in "[]":
                tokens.append(Token(LST, char))
            elif char in "()":
                tokens.append(Token(PAR, char))
            elif char == ".":
                tokens.append(Token(DOT, char))
            elif char == ",":
                tokens.append(Token(SEP, char))
            elif char in ":":
                tokens.append(Token(SYM, char))
            elif char == '"':
                found = False
                ci = i+1
                while ci < len(line):
                    if line[ci] == '"' and line[ci-1] != "\\":
                        found = True
                        break
                    ci += 1
                if not found:
                    # unclosed string
                    self.err(1)
                tokens.append(Token(STR, '"'+line[i+1:ci]+'"'))
                i = ci
            elif char.isdigit():
                fin = ""
                s = i
                deciuse = False
                while line[s].isdigit() and s < len(line):
                    c = line[s]
                    fin += c
                    s += 1
                    if s >= len(line):
                        break
                    if line[s] == ".":
                        if deciuse:
                            break
                        if line[s+1] == ".":
                            break
                        if line[s+1].isalpha():
                            break
                        deciuse = True
                        fin += "."
                        s += 1
                    if s >= len(line):
                        break
                i = s
                tokens.append(Token(FLO if deciuse else INT, float(fin) if deciuse else int(fin)))
            else:
                found = False
                for keyword in self.keywords:
                    if len(line)-i >= len(keyword):
                        test = line[i:i+len(keyword)]
                        if test == keyword:
                            found = True
                            tokens.append(Token(KWD, test))
                            if keyword == "flag":
                                sec = line[i:(i+line[i:].index("\n")) if "\n" in line[i:] else i+len(line[i:])].split(" ")
                                tokens.append(Token(CON, (sec[1], sec[2][:-1 if sec[2][-1] == "\n" else len(sec[2])])))
                                i += len(" ".join(sec))
                                break
                            if keyword == "python":
                                if line[i + len(keyword)] == "{" or line[i + len(keyword):i + len(keyword) + 2] == " {":
                                    tstart = i+len(keyword)+(1 if line[i + len(keyword)] != "{" else 0)
                                    test = line[tstart:]
                                    t2 = test[2:]
                                    i2 = 0
                                    depth = 1
                                    while i2 < len(t2):
                                        if t2[i2] == "{":
                                            depth += 1
                                        if t2[i2] == "}":
                                            depth -= 1
                                        if depth == 0:
                                            break
                                        i2 += 1
                                    t2 = t2[:i2-1]
                                    tokens.append(Token("python", t2))
                                    i = tstart + i2 + 3
                                break
                            i += len(keyword)
                            break
                if found:
                    continue
                ti = i
                while ti < len(line):
                    if not line[ti].isalnum() and not line[ti] == "_":
                        break
                    ti += 1
                if ti != i:
                    tokens.append(Token(REF, line[i:ti]))
                self.tokens = tokens
                if ti == i:
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
        if "globals" in data:
            exec(code, data["globals"], data["locals"] if "locals" in data else data["globals"])
        else:
            exec(code)
        result = f()
        if type(result) == str:
            result = '"' + result + '"'
        return Token(NUL, None)
    def deref (self, token):
        for i in range(len(self.scopes)):
            scope = self.scopes[-1-i]
            if token.value in scope.keys():
                return scope[token.value]
        self.err(2)
    def domod (self, base, op, mod):
        print(mod, "r")
        if mod.type == REF:
            mod = self.deref(mod)
        print(mod, "dr")
        if base.type == REF:
            base = self.deref(base)
        isstr = False
        modstr = False
        if base.type == STR:
            isstr = True
            base.value = base.value[1:-1]
        if mod.type == STR:
            modstr = True
            mod.value = mod.value[1:-1]
        op = op.value
        result = None
        if op == "+":
            print(base.value, "BASE", mod.value, "MOD")
            result = base.value + mod.value
            print(base.value, mod.value, result, "RESULTANT")
        elif op == "-":
            result = base.value - mod.value
        elif op == "*":
            result = base.value * mod.value
        elif op == "/":
            result = base.value / mod.value
        elif op == "%":
            result = base.value % mod.value
        if isstr:
            result = '"' + result + '"'
        if modstr:
            mod.value = '"' + mod.value + '"'
        return Token(base.type, result)
    def getexp (self, tokens, start):
        i = start+2
        result = tokens[start+1]
        if result.type == REF:
            result = self.deref(result)
        while i < len(tokens):
            token = tokens[i]
            if token.type in self.nonmod:
                break
            ret = self.domod(result, token, tokens[i+1])
            if ret == None:
                break
            result = ret
            i += 2
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
            if token.type == PAR:
                if token.value == "(":
                    depth += 1
                else:
                    depth -= 1
                if depth == 0:
                    break
            elif token.type == SEP:
                args.append(tuple(build))
                build = []
            else:
                build.append(token)
            i += 1
        depth = 1
        i += 1
        while i < len(tokens):
            token = tokens[i]
            if token.type == DCT:
                if token.value == "{":
                    depth += 1
                else:
                    depth -= 1
                if depth == 0:
                    break
            else:
                ftoks.append(token)
            i += 1
        result = Token(FUN, (tuple(args), tuple(ftoks)))
        print(result)
        return result, i
    def err (self, code):
        if code == 0:
            raise NameError("cannot assign to constant value")
        elif code == 1:
            raise SyntaxError("unclosed string")
        elif code == 2:
            raise NameError("variable name not defined")
    def evaltokens (self, tokens):
        if type(tokens) == str:
            tokens = self.tokenize(tokens)
        # print(tokens)
        tind = 0
        while tind < len(tokens):
            token = tokens[tind]
            if token.type == KWD:
                if token.value == "python":
                    if tokens[tind+1].type == "python":
                        tokens[tind] = self.doPython({"code":tokens[tind+1].value})
                    else:
                        tokens[tind] = self.pythonFunc(tokens[tind:])
                    tokens.pop(tind+1)
                elif token.value == "func":
                    # print(token)
                    name = tokens[tind+1].value
                    if name in self.scopes[0].keys():
                        # assignment to constant
                        self.err(0)
                    self.scopes[-1][name], tind = self.getfunc(tokens, tind)
                elif token.value == "audit":
                    self._printvars()
            elif token.type == CON:
                self.flags[token.value[0]] = {"on":True, "off":False, "switch":not self.flags[token.value[0]]}[token.value[1]]
            elif token.type == ASS:
                if token.value == "=":
                    if self.tokens[tind-1].value in self.scopes[0].keys():
                        # assignment to constant
                        self.err(0)
                    self.scopes[-1][self.tokens[tind-1].value], tind = self.getexp(tokens, tind)
                else:
                    tokens.insert(tind+1, Token(MAT, token.value[0]))
                    tokens.insert(tind+1, Token(REF, tokens[tind-1].value))
                    tokens[tind] = Token(ASS, "=")
                    print(tokens[tind:])
                    continue
            elif token.type == FUN:
                pass
                # self.runfun
            tind += 1
    def _printvars (self):
        scopes = self.scopes[1:]
        for i in range(len(scopes)):
            scope = scopes[i]
            print("global scope:" if i == 0 else f"local scope ({i}):")
            for key in scope.keys():
                print(f"\t{key} : {scope[key]}")
    def run (self):
        self.evaltokens(self.lines)
        if self.flags["vars"]:
            self._printvars()

inter = Interpreter()