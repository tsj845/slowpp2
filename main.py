ASS, MAT, LOG, INT, STR, BOL, FLO, LST, DCT, PAR, DOT, SEP, SYM, SLF, OBJ, NUL = "ASS", "MAT", "LOG", "INT", "STR", "BOL", "FLO", "LST", "DCT", "PAR", "DOT", "SEP", "SYM", "SLF", "OBJ", "NUL"

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
            ("split", ("self", SLF, "sep", STR, "maxsep=-1", INT), LST) : "python {return self.value.split(sep, maxsep)}",
            ("rsplit", ("self", SLF, "sep", STR, "maxsep=-1", INT), LST) : "python {return self.value.rsplit(sep, maxsep)}",
            ("indexOf", ("self", SLF, "item", STR), INT) : "python {try:\n\treturn self.value.index(item)\nexcept:\n\treturn -1}",
            ("slice", ("self", SLF, "start=0", INT, "end=-1", INT), STR) : "python {return self.value[start:end]}"
        })
    def __repr__ (self):
        return f"String(\"{self.value}\")"

class Int (Type):
    def __init__ (self, value : int):
        super().__init__("int", value)
        self.methods.update({
            ("toString", ("self", SLF), STR) : "python {return str(self.value)}"
        })

class Float (Type):
    def __init__ (self, value : float):
        super().__init__("float", value)
        self.methods.update({
            ("toString", ("self", SLF), STR) : "python {return str(self.value)}"
        })

class Bool (Type):
    def __init__ (self, value : bool):
        super().__init__("bool", value)

class List (Type):
    def __init__ (self, value : list):
        super().__init__("list", value)
        self.methods.update({
            ("join", ("self", SLF, "j=','", STR), STR) : "python {v=self.value.copy()\nfor i in range(len(v)):\n\tif type(v[i])!=str:\n\t\tv[i]=str(v[i])\nreturn j.join(v)}",
            ("slice", ("self", SLF, "start=0", INT, "end=-1", INT), LST, OBJ) : "python {return self.value[start:end]}",
            ("pop", ("self", SLF, "item=-1", INT), OBJ) : "python {return self.value.pop(item)}",
            ("push", ("self", SLF, "...items", LST, OBJ), NUL) : "python {for item in items:\n\tself.value.push(item)}"
        })

class Dict (Type):
    def __init__ (self, value : dict):
        super().__init__("dict", value)
        self.methods.update({
            ("keys", ("self", SLF), LST, OBJ) : "python {return list(self.value.keys())}",
            ("values", ("self", SLF), LST, OBJ) : "python {return list(self.value.values())}",
            ("entries", ("self", SLF), LST, LST, OBJ) : "python {entries=list(self.value.entries())\nl=[]\nfor entry in entries:\n\tl.append(list(entry))\nreturn l}",
            ("pop", ("self", SLF, "item", OBJ), OBJ) : "python {return self.value.pop(item)}"
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
    def equal (type, value):
        return (self.type == type and self.value == value)
    def __repr__ (self):
        return f"({self.type}, \"{self.value}\")"

class Interpreter ():
    def __init__ (self, filename="code"):
        self.lines = []
        self.keywords = ("func", "if", "elif", "else", "for", "while", "in", "break", "continue", "python")
        self._getData(filename)
        self.run()
    def _getData (self, filename : str):
        f = open(filename+("" if filename.endswith(".spp") else ".spp"))
        data = f.read()
        f.close()
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
                    line = "\n" + data.pop(i+1)
                    data[i] = line
                isstr = not isstr
            elif isstr:
                line += "\n" + data.pop(i+1)
                data[i] = line
        for i in range(len(data)):
            data[i] = data[i].replace("\\n", "\n")
        self.lines = data
    def tokenize (self, line : str) -> list:
        tokens = []
        i = 0
        while i < len(line):
            char = line[i]
            if i < len(line)-1 and line[i:i+1] == "//":
                break
            if char in "+-*/%":
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
                    raise Exception("unclosed string")
                tokens.append(Token(STR, line[i+1:ci]))
                i = ci
            else:
                found = False
                for keyword in self.keywords:
                    if len(line)-i < len(keyword):
                        test = line[i:i+len(keyword)]
                        if test == keyword:
                            tokens.append(Token(KWD, test))
                            found = True
                            i += len(test)
                            break
                if found:
                    continue
            i += 1
        return tokens
    def pythonFunc (self, tokens):
        return Token(NUL, None)
    def doPython (self, data):
        f = None
        code = "\t"+data["code"]
        code = code.replace("\n", "\n\t")
        code = "def private ():\n"+code+"\nf=private"
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
            tokens = self.tokenize(line)
        tind = 0
        while tind < len(tokens):
            token = tokens[i]
            if token.type == KWD:
                if token.value == "python":
                    if tokens[i+1].type == "python":
                        self.tokens[i] = self.doPython(tokens[i+1].value)
                    else:
                        self.tokens[i] = self.pythonFunc(tokens[i:])
                    self.tokens.pop(i+1)
            tind += 1
                        
    def run (self):
        exline = 0
        while True:
            if exline >= len(self.lines):
                break
            # code goes here
            exline += 1

inter = Interpreter()

print(inter.tokenize(inter.lines[0]))

l = List([String("go"), String("back"), Int(10), String("lines"), String("if"), String("is_error"), String("is"), Bool("True")])
print(l)