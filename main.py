ASS, MAT, LOG, INT, STR, BOL, FLO, LST, DCT, PAR, DOT, SEP, SYM, SLF, OBJ, NUL, KWD, EQU, FUN, REF, CON = "ASS", "MAT", "LOG", "INT", "STR", "BOL", "FLO", "LST", "DCT", "PAR", "DOT", "SEP", "SYM", "SLF", "OBJ", "NUL", "KWD", "EQU", "FUN", "REF", "CON"

class Object ():
    def __init__ (self, type : str, value):
        self.type = type
        self.value = value

class Class (Object):
    def __init__ (self, methods : dict = None, properties : dict = None):
        super().__init__("class", None)
        self.methods = {} if methods == None else methods
        self.properties = {} if properties == None else properties
    def call (self, method : str) -> list:
        return self.methods[method]
    def fetch (self, property : str):
        return self.properties[property]

class Type (Class):
    def __init__ (self, type, value):
        super().__init__()
        self.type = type
        self.value = value
    def __repr__ (self):
        return f"{self.__class__.__qualname__}({self.value})"

class String (Type):
    def __init__ (self, value : str):
        super().__init__("string", value)
        self.properties["length"] = len(self.value)
        self.methods.update({
            "split" : ("self", "sep", "maxsep=-1", "python {return self.value.split(sep, maxsep)}"),
            "rsplit" : ("self", "sep", "maxsep=-1", "python {return self.value.rsplit(sep, maxsep)}"),
            "indexOf" : ("self", "item", "python {try:\n\treturn self.value.index(item)\nexcept:\n\treturn -1}"),
            "slice" : ("self", "start=0", "end=-1", "python {return self.value[start:end]}")
        })
    def __repr__ (self):
        return f"String(\"{self.value}\")"

class Int (Type):
    def __init__ (self, value : int):
        super().__init__("int", value)
        self.methods.update({
            "toString" : ("self", "python {return str(self.value)}")
        })

class Float (Type):
    def __init__ (self, value : float):
        super().__init__("float", value)
        self.methods.update({
            "toString" : ("self", "python {return str(self.value)}")
        })

class Bool (Type):
    def __init__ (self, value : bool):
        super().__init__("bool", value)

class List (Type):
    def __init__ (self, value : list):
        super().__init__("list", value)
        self.methods.update({
            "join" : ("self", "j=','", "python {v=self.value.copy()\nfor i in range(len(v)):\n\tif type(v[i])!=str:\n\t\tv[i]=str(v[i])\nreturn j.join(v)}"),
            "slice" : ("self", "start=0", "end=-1", "python {return self.value[start:end]}"),
            "pop" : ("self", "item=-1", "python {return self.value.pop(item)}"),
            "push" : ("self", "...items", "python {for item in items:\n\tself.value.push(item)}")
        })

class Dict (Type):
    def __init__ (self, value : dict):
        super().__init__("dict", value)
        self.methods.update({
            "keys" : ("self", "python {return list(self.value.keys())}"),
            "values" : ("self", "python {return list(self.value.values())}"),
            "entries" : ("self", "python {entries=list(self.value.entries())\nl=[]\nfor entry in entries:\n\tl.append(list(entry))\nreturn l}"),
            "pop" : ("self", "item", "python {return self.value.pop(item)}")
        })

class Func (Object):
    def __init__ (self, value : str):
        super().__init__("func", value)
    def call (self):
        return self.value

class Token ():
    def __init__ (self, type, value):
        self.type = type
        self.value = value
    def equal (self, type, value):
        return (self.type == type and self.value == value)
    def __repr__ (self):
        return f"({self.type}, \"{self.value}\")"

class Interpreter ():
    def __init__ (self, filename="code"):
        self.lines = []
        self.keywords = ("func", "if", "elif", "else", "for", "while", "in", "break", "continue", "python", "search", "switch", "return", "case", "default", "class", "global", "flag")
        self.flags = {"vars":False}
        # sets up variable scopes, top level scope is readonly constants and second scope is the program global scope, all other scopes are local scopes
        self.scopes = [{"true":Token(BOL, True), "false":Token(BOL, False), "void":Token(NUL, None)}, {}]
        self._getData(filename)
        self.run()
    def _getData (self, filename : str):
        f = open(filename+("" if filename.endswith(".spp") else ".spp"))
        data = f.read()
        f.close()
        # data = self.breaklines(data)
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
        # for i in range(len(data)):
        #     data[i] = data[i].replace("\\n", "\n")
        return data
    def tokenize (self, line : str) -> list:
        # print("\\n".join(line.split("\n")))
        # lines = self.breaklines(line)
        # for i in range(len(lines)):
        #     lines[i] = lines[i]+"\n"
        tokens = []
        i = 0
        while i < len(line):
            # if i >= len(lines[0]):
            #     print(lines, "l", end="\n\n")
            #     if len(lines) == 1:
            #         break
            #     lines[0] = lines[0] + lines.pop(1)
            #     print(lines, "l2", end="\n\n")
            # else:
            #     print(i)
            char = line[i]
            if i < len(line)-1 and line[i:i+2] == "//":
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
                # i += len(lines[0])-i
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
                # print(line[i:])
                if not found:
                    raise Exception("unclosed string")
                tokens.append(Token(STR, line[i+1:ci]))
                i = ci
            elif char.isdigit():
                fin = ""
                s = i
                deciuse = False
                while line[s].isdigit():
                    c = line[s]
                    fin += c
                    s += 1
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
                i = s
                tokens.append(Token(FLO if deciuse else INT, Float(float(fin)) if deciuse else Int(int(fin))))
            else:
                found = False
                for keyword in self.keywords:
                    # print("\\t".join("\\n".join(line[i:].split("\n")).split("\t")), lines, sep="\n\n")
                    # print(i, line[i], len(line)-i, len(line), keyword, len(keyword))
                    if len(line)-i >= len(keyword):
                        test = line[i:i+len(keyword)]
                        # print(test)
                        if test == keyword:
                            # print(test)
                            found = True
                            tokens.append(Token(KWD, test))
                            if keyword == "flag":
                                sec = line[i:line[i:].index("\n") if "\n" in line[i:] else len(line[i:])].split(" ")
                                tokens.append(Token(CON, (sec[1], sec[2][:-1 if sec[2][-1] == "\n" else len(sec[2])])))
                            if keyword == "python":
                                # print(line[i+len(keyword)], line[i+len(keyword):i+len(keyword)+2], i, len(keyword), i+len(keyword), line)
                                if line[i + len(keyword)] == "{" or line[i + len(keyword):i + len(keyword) + 2] == " {":
                                    test = line[i+len(keyword)+(1 if line[i + len(keyword)] != "{" else 0):]
                                    # print(test, "test")
                                    t2 = test[1:]
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
                                    # print(t2, i2)
                                    t2 = t2[:i2]
                                    # print(t2, "t2", sep="\n")
                                    tokens.append(Token("python", t2))
                                    i += i2
                                # i += len(t2)
                                print(line)
                                # print(i, line[i:], "X")
                                break
                            i += len(keyword)
                            # print(i)
                            # i += 1
                            break
                # return []
                if found:
                    continue
                ti = i
                while ti < len(line):
                    if not line[ti].isalnum():
                        break
                    ti += 1
                tokens.append(Token(REF, line[i:ti]))
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
        # print(code)
        if "globals" in data:
            exec(code, data["globals"], data["locals"] if "locals" in data else data["globals"])
        else:
            exec(code)
        result = f()
        if type(result) == str:
            result = '"' + result + '"'
        return Token(NUL, None)
    def evaltokens (self, tokens):
        if type(tokens) == str:
            tokens = self.tokenize(tokens)
        print(tokens)
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
            elif token.type == CON:
                print(token)
                self.flags[token.value[0]] = {"on":True, "off":False, "switch":not self.flags[token.value[0]]}[token.value[1]]
            tind += 1
    def _printvars (self):
        scopes = self.scopes[1:]
        for i in range(len(scopes)-1):
            scope = scopes[i]
            print("global scope:" if i == 0 else f"local scope ({i}):")
            for key in scope.keys():
                print(f"\t{key} : {scope[i][key]}")
    def run (self):
        exline = 0
        # print(self.lines)
        self.evaltokens(self.lines)
        print(self.flags)
        if self.flags["vars"]:
            self._printvars()
        # while True:
        #     if exline >= len(self.lines):
        #         break
        #     # code goes here
        #     print(exline)
        #     self.evaltokens(self.lines[exline])
        #     exline += 1

inter = Interpreter()

# print(inter.tokenize(inter.lines[3]))

# l = List([String("go"), String("back"), Int(10), String("lines"), String("if"), String("is_error"), String("is"), Bool("True")])
# print(l)

# print(inter.breaklines('h\n"g\\ng"\nh'))