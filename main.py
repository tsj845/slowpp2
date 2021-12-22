# imports regex module
import re
# imports sys for error handling
import sys

# token types
ASS, MAT, LOG, INT, STR, BOL, FLO, LST, DCT, PAR, DOT, SEP, SYM, SLF, OBJ, NUL, KWD, EQU, FUN, REF, CON, ERR, ELI = "ASS", "MAT", "LOG", "INT", "STR", "BOL", "FLO", "LST", "DCT", "PAR", "DOT", "SEP", "SYM", "SLF", "OBJ", "NUL", "KWD", "EQU", "FUN", "REF", "CON", "ERR", "ELI"

# stores token data
class Token ():
    # initializes the token
    def __init__ (self, type : str, value):
        """
        Token (type : str, value : any) -> Token

        tokens can have any type and any value

        properties:
            type : token type

            value : token value

        standard types are:
            ASS : assignment token
            MAT : mathmatical operator token
            LOG : logical operator token
            INT : integer token
            STR : string token
            BOL : boolean token
            FLO : floating point token
            LST : list token
            DCT : dict token
            PAR : parentheses token
            DOT : dot token
            SEP : list seperator token
            SYM : symbol token
            SLF : self token
            OBJ : object token
            NUL : null token
            KWD : keyword token
            EQU : equality token
            FUN : function token
            REF : reference token
            CON : config token
            ERR : error token
        
        methods:
            equal (type : str, value : str) -> bool
            deprecated use built in == operator instead

            dump () -> str
            dumps the token's type and value
        """
        # token type
        self.type = type
        # token value
        self.value = value
    # tests token equality
    def equal (self, type : str, value) -> bool:
        return (self.type == type and self.value == value)
    # dumps value
    def _dumpval (self) -> str:
        # converts value to string and replaces ANSI escape sequence introducer with an escaped version
        return '"' + str(self.value).replace("\n", "\\n").replace("\x1b", "\\x1b") + '"'
    # dumps token properties
    def dump (self) -> str:
        return f"({self.type}, {self._dumpval()})"
    # string representation of token
    def __repr__ (self) -> str:
        return f"({self.type}, {self._dumpval()})"
    # token equality
    def __eq__ (self, comp) -> bool:
        # tests that the comparison is between tokens
        if (isinstance(comp, Token)):
            # returns equality
            return comp.type == self.type and comp.value == self.value
        # returns false if comparison is not between tokens
        return False

# a variable scope
class Namespace ():
    # initializes the variable scope
    def __init__ (self, value : dict, parent):
        """
        Namespace (value : dict, parent : NamespaceList) -> Namespace

        properties:
            parent : the namepaces parent NamespaceList

            value : the variable map

            audit : flag, tells the Namespace whether to audit variable gets/sets

            zavls : stores which audit states will audit any variable if no variables are expicitly set for auditing

            auditstate : the auditing policy

        auditstate can be one of the following values:
            0 : all variables are audited if not given any variables to audit
            1 : audits only variables in self.parent.auditvars
            2 : audits only variables not in self.parent.auditvars
        """
        # the parent namespace list
        self.parent = parent
        # the variable map
        self.value = value
        # if all variables should be audited if no variables are explicitly audited
        self.zavls = (0,)
        # the current audit policy
        self.auditstate = 0
    # the variable scope keys
    def keys (self):
        return self.value.keys()
    # string representation of the variable scope
    def __repr__ (self) -> str:
        return str(self.value)
    # gets an item
    def __getitem__ (self, key : str) -> Token:
        # checks if the get should be audited
        if (self.parent.audit and not self.parent.auditing and ((len(self.parent.auditvars) == 0 and self.auditstate in self.zavls) or (key in self.parent.auditvars and self.auditstate != 2) or (self.auditstate == 2 and key not in self.parent.auditvars))):
            # audits the get
            print(key, self.value[key], "NAMESPACE GET")
        # returns the value
        return self.value[key]
    # sets an item
    def __setitem__ (self, key : str, value : Token) -> None:
        # sets the value
        self.value[key] = value
        # checks if the set should be audited
        if (self.parent.audit and not self.parent.auditing and ((len(self.parent.auditvars) == 0 and self.auditstate in self.zavls) or (key in self.parent.auditvars and self.auditstate != 2) or (self.auditstate == 2 and key not in self.parent.auditvars))):
            # audits the set
            print(key, value, "NAMESPACE SET")

# stores namespaces
class NamespaceList ():
    # initializes the list
    def __init__ (self, consts : dict):
        """
        NamespaceList (consts : dict) -> NamespaceList

        stores Namespace objects

        properties:
            auditing - wheter an audit event is occuring, suppresses child variable scope auditing

            scopes - list of child variable scopes

            auditvars - list of variables that should be audited

        methods:
            audit_state (index : int, value : int) -> None
            sets the audit policy for a variable scope

            add_audit (vname : str) -> None
            adds vname to list of variables to audit

            remove_audit (vname : str) -> None
            removes vname from list of variables to audit

            new_scope () -> None
            adds a new variable scope

            remove_scope () -> None
            removes the lowest level scope (can't remove global or constant scopes)
        """
        # whether an audit is occuring
        self.auditing = False
        # if child scopes should audit variable changes
        self.audit = False
        # variable scopes
        self.scopes = [Namespace(consts, self), Namespace({}, self)]
        # variables that should be audited
        self.auditvars = []
    # sets audit policy for a scope
    def audit_state (self, index : int, value : int) -> None:
        # checks that index is valid
        if (index >= 0 and index < len(self.scopes)):
            # sets audit policy
            self.scopes[index].auditstate = value
    # adds a variable to audit
    def add_audit (self, vname : str) -> None:
        # checks that the variable name isn't already in self.auditvars
        if (vname not in self.auditvars):
            # adds the name to self.auditvars
            self.auditvars.append(vname)
    # removes a variable from auditing
    def remove_audit (self, vname : str) -> None:
        # checks that the name is in self.auditvars
        if (vname in self.auditvars):
            # removes the name from self.auditvars
            self.auditvars.pop(self.auditvars.index(vname))
    # adds a scope
    def new_scope (self) -> None:
        self.scopes.append(Namespace({}, self))
    # removes a scope
    def remove_scope (self) -> None:
        if (len(self.scopes) > 2):
            self.scopes.pop()
    # returns string representation of the list
    def __repr__ (self) -> str:
        # gets the string representation of all scopes and formats them nicely
        return "[\n"+",\n".join([str(self.scopes[i]) for i in range(len(self.scopes))])+"\n]"
    # gets length of list
    def __len__ (self) -> int:
        return len(self.scopes)
    # gets scope
    def __getitem__ (self, ind : int) -> Namespace:
        return self.scopes[ind]
    # sets scope
    def __setitem__ (self, ind : int, value : Namespace) -> None:
        self.scopes[ind] = value

# system color palette
class InterPalette ():
    # inializes the palette
    def __init__ (self):
        """
        InterPalette () -> InterPalette

        the palette is used to store what colors the system should use when displaying certain types of outputs

        properties:
            [system colors] : the colors for different type of system output

            validcolornames : tuple of valid system colors
        
        methods:
            has (attr : str) -> bool
            returns true if the attr is in self.validcolornames
        """
        # when program resets to default color
        self.reset = "\x1b[39m"
        # color for auditing header
        self.audithead = "\x1b[38;2;200;100;0m"
        # color for auditing output
        self.audit = "\x1b[38;2;200;100;0m"
        # color for error output
        self.error = "\x1b[38;2;255;0;0m"
        # color for warning output
        self.warning = "\x1b[38;2;255;255;0m"
        # color for normal output
        self.output = "\x1b[38;2;0;100;200m"
        # valid color names
        self.validcolornames = ("reset", "audithead", "audit", "error", "warning", "output")
    # checks if the given name is a valid color name
    def has (self, attr : str) -> bool:
        return (attr in self.validcolornames)
    # sets a color
    def __setitem__ (self, key, value):
        if (key == "reset"):
            self.reset = value
        elif (key == "audithead"):
            self.audithead = value
        elif (key == "audit"):
            self.audit = value
        elif (key == "error"):
            self.error = value
        elif (key == "warning"):
            self.warning = value
        elif (key == "output"):
            self.output = value

# regex for checking if a string is a valid ANSI color code
ansire = re.compile("(\\\\x1b\[\d{2,2};\d{1,1};\d{1,3};\d{1,3};\d{1,3}m)|(\\\\x1b\[\d{2,2}m)")

# interprets code
class Interpreter ():
    # initializes the interpreter
    def __init__ (self, filename : str = "code", /, suppress : bool = False):
        """
        Interpreter (filename : str = "code", /, suppress : bool = False) -> Interpreter

        filename - defaults to "code", specifies the file to read from, if the file extension .spp isn't in the filename it will be added automatically

        suppress - defaults to False, keyword only argument, if set to true suppresses the automatic running of the interpreter

        the interpreter class will take the filename given, read it then will evaluate the code unless automatic running is suppressed
        """
        # maximum error code
        self.mec = 0
        # lines
        self.lines = []
        # language keywords
        self.keywords = ("func", "if", "elif", "else", "for", "while", "in", "break", "continue", "python", "search", "switch", "return", "case", "default", "class", "global", "flag", "audit", "watch", "color", "dump", "existing")
        # system flags
        self.flags = {"vars":False, "tokens":False, "error":False}
        # non modifier token types
        self.nonmod = (REF, NUL, INT, STR, PAR, DCT, LST, BOL, FLO, OBJ, KWD)
        # modifier token types
        self.modtokens = (MAT, LOG, EQU)
        # tokens for debugging
        self.tokens = []
        # sets up builtin functions
        self.builtins = {"true":Token(BOL, True), "false":Token(BOL, False), "void":Token(NUL, None),"print":Token(FUN, (((Token(ELI, "..."), Token(REF, "args")), (Token(REF, "sep"), Token(ASS, "="), Token(STR, " ")), (Token(REF, "end"), Token(ASS, "="), Token(STR, "\n"))), (Token(KWD, "python"), Token("python", "    print(*args, sep=sep, end=end)"))))}
        # sets up variable scopes, top level scope is readonly constants and second scope is the program global scope, all other scopes are local scopes
        self.scopes = NamespaceList(self.builtins)
        # system color palette
        self.colors = InterPalette()
        # gets code
        self._getData(filename)
        # checks that run isn't suppressed
        if (not suppress):
            # runs the interpreter
            self.run()
    # reads code from a file
    def _getData (self, filename : str) -> None:
        # opens the file
        f = open(filename+("" if filename.endswith(".spp") else ".spp"))
        # reads file data
        data = f.read()
        # closes the file
        f.close()
        # sets self.lines to file contents
        self.lines = data
    # breaks lines of code
    def breaklines (self, data : str) -> list:
        # changes \\n to \n
        data = data.replace("\\n", "\n")
        # splits at newliines
        data = data.split("\n")
        # initial length
        inlen = len(data)-1
        # if the current part is in a string
        isstr = False
        for i in range(len(data)):
            # goes from last to first
            i = inlen-i
            # checks that i is less than the length of the data
            if (i >= len(data)):
                break
            # gets line
            line = data[i]
            # if a string is being opened or closed
            if (line.count('"') % 2 != 0):
                # if the current part is a string
                if (isstr):
                    # combines the parts of the line
                    line = line + "\n" + data.pop(i+1)
                    data[i] = line
                # toggles isstr
                isstr = not isstr
            # if current part is a string
            elif (isstr):
                # combines the parts of the line
                line += "\n" + data.pop(i+1)
                data[i] = line
        # returns the lines
        return data
    # tokenizes a string of code
    def tokenize (self, line : str) -> list:
        # token list
        tokens = []
        # index
        i = 0
        while i < len(line):
            # updates self.tokens
            self.tokens = tokens
            # gets current character
            char = line[i]
            # checks for line seperation character
            if (char == "\n" or char == ";"):
                # increments i
                i += 1
                # continues tokenizing
                continue
            # checks for comments
            elif (i < len(line)-1 and line[i:i+2] == "//"):
                # if the end of comment was found
                found = False
                isstr = False
                # gets the end of the comment
                while i < len(line):
                    if (line[i] == '"' and line[i-1] != "\\"):
                        isstr = not isstr
                    if (line[i] == "\n" and not isstr):
                        found = True
                        break
                    i += 1
                # breaks tokenizer loop if the comment lasted until end of code
                if (not found):
                    break
            # checks for mathmatical operation
            elif (char in "+-*/%"):
                # checks if the operation is an assignment
                if (i < len(line)-1 and line[i+1] == "="):
                    # adds assignment token
                    tokens.append(Token(ASS, char+"="))
                    # increases i
                    i += 2
                    # continues tokenizing
                    continue
                # adds mathmatical operator token
                tokens.append(Token(MAT, char))
            # checks for assignment
            elif (char == "="):
                # checks for equality
                if (len(line) > i and line[i:i+2] == "=="):
                    # adds equality token
                    tokens.append(Token(EQU, "=="))
                    # increases i
                    i += 2
                    # continues tokenizing
                    continue
                # adds assignment token
                tokens.append(Token(ASS, char))
            # checks for comparison
            elif (char in "<>"):
                v = char
                if (len(line) > i and line[i+1] == "="):
                    v += "="
                    i += 1
                tokens.append(Token(EQU, v))
            # checks for logical operators
            elif (char in "!&|^"):
                # checks for equality
                if (i < len(line)-1 and line[i+1] == "=" and char not in "&|^"):
                    # adds equality token
                    tokens.append(Token(EQU, char+"="))
                    # increases i
                    i += 2
                    # continues tokenizing
                    continue
                # adds logical operator token
                tokens.append(Token(LOG, char))
            # checks for curly brackets
            elif (char in "{}"):
                # adds dictionary token
                tokens.append(Token(DCT, char))
            # checks for square brackets
            elif (char in "[]"):
                # adds list token
                tokens.append(Token(LST, char))
            # checks for parentheses
            elif (char in "()"):
                # adds parentheses token
                tokens.append(Token(PAR, char))
            # checks for dot syntax
            elif (char == "."):
                # adds dot token
                tokens.append(Token(DOT, char))
            # checks for comma
            elif (char == ","):
                # adds seperator token
                tokens.append(Token(SEP, char))
            # checks for colon
            elif (char in ":"):
                # adds symbol token
                tokens.append(Token(SYM, char))
            # checks for string opening
            elif (char == '"'):
                # if the end of the string was found
                found = False
                # char index
                ci = i+1
                # loops over code
                while ci < len(line):
                    # checks if char is string ending
                    if (line[ci] == '"' and line[ci-1] != "\\"):
                        # breaks out of loop
                        found = True
                        break
                    # increments char index
                    ci += 1
                # if end of string wasn't found
                if (not found):
                    # unclosed string
                    raise Exception(2)
                # adds string token
                tokens.append(Token(STR, '"'+line[i+1:ci]+'"'))
                # increases i
                i = ci
            # checks for number
            elif (char.isdigit()):
                fin = ""
                s = i
                # if number is float
                deciuse = False
                # loops over code
                while line[s].isdigit() and s < len(line):
                    # gets test character
                    c = line[s]
                    # adds it to final
                    fin += c
                    # increments s
                    s += 1
                    # checks that s is a valid index for code
                    if (s >= len(line)):
                        break
                    # checks for a decimal
                    if (line[s] == "."):
                        # if decimal already used
                        if (deciuse):
                            break
                        # if next character is also a decimal
                        if (line[s+1] == "."):
                            break
                        # if next character is start of a name
                        if (line[s+1].isalpha()):
                            break
                        # sets float flag to true
                        deciuse = True
                        # adds decimal
                        fin += "."
                        # increments s
                        s += 1
                # increases i
                i = s-1
                # adds float token if decimal was used else adds integer token
                tokens.append(Token(FLO if deciuse else INT, float(fin) if deciuse else int(fin)))
            else:
                found = False
                # loops over all keywords
                for keyword in self.keywords:
                    # checks that the line isn't longer than the keyword
                    if (len(line)-i >= len(keyword)):
                        # gets where the keyword could be
                        test = line[i:i+len(keyword)]
                        # checks for a match with the keyword
                        if (test == keyword):
                            # tells the tokenizer that a keyword was found
                            found = True
                            # appends keyword token
                            tokens.append(Token(KWD, test))
                            # sets program flags
                            if (keyword == "flag"):
                                # gets keyword arguments
                                sec = line[i:(i+line[i:].index("\n")) if "\n" in line[i:] else i+len(line[i:])].split(" ")
                                # appends config token
                                tokens.append(Token(CON, (sec[1], sec[2][:-1 if sec[2][-1] == "\n" else len(sec[2])])))
                                # increases i
                                i += len(" ".join(sec))
                                break
                            # sets system colors
                            if (keyword == "color"):
                                # gets rest of code
                                rest = line[i + len(keyword) + 1:]
                                # gets code to end of line
                                v = line[i + len(keyword) + 1:(rest.index("\n")+i+len(keyword)+1) if "\n" in rest else len(line)]
                                # increases i
                                i += len(v) + len(keyword) + 1
                                # splits v by spaces
                                v = v.split(" ")
                                # gets the first two items of v
                                v = v[:min(2, len(v))]
                                # checks that v has two items
                                if (len(v) < 2):
                                    break
                                # checks that the property exists
                                if (self.colors.has(v[0])):
                                    # checks if the color given is ANSI
                                    if (ansire.fullmatch(v[1])):
                                        # adds color tokens
                                        tokens.append(Token("color", v[0]))
                                        tokens.append(Token("color", v[1].replace("\\x1b", "\x1b")))
                                    else:
                                        # tries to convert from common colors to ANSI
                                        commoncolors = {"lime":"\x1b[38;2;0;255;0m","green":"\x1b[38;2;0;200;0m","orange":"\x1b[38;2;200;100;0m","yellow":"\x1b[38;2;255;255;0m","red":"\x1b[38;2;255;0;0m"}
                                        if (v[1] not in commoncolors.keys()):
                                            break
                                        # adds color tokens
                                        tokens.append(Token("color", v[0]))
                                        tokens.append(Token("color", commoncolors[v[1]]))
                                break
                            # variable auditing
                            if (keyword == "audit"):
                                # checks if an argument was given
                                if (len(line) > i + len(keyword) and line[i + len(keyword)] == " "):
                                    # gets rest of the code
                                    rest = line[i + len(keyword) + 1:]
                                    v = line[i + len(keyword) + 1:(rest.index("\n")+i+len(keyword)+1) if "\n" in rest else len(line)]
                                    # adds audit token
                                    tokens.append(Token("audit", v))
                                    # increases i
                                    i += len(v) + 1
                                i += len(keyword)
                                break
                            # dumps data
                            if (keyword == "dump"):
                                # checks that an argument is present
                                if (len(line) > i + len(keyword) and line[i + len(keyword)] == " "):
                                    # gets the rest of the code
                                    rest = line[i + len(keyword) + 1:]
                                    v = line[i + len(keyword) + 1:(rest.index("\n")+i+len(keyword)+1) if "\n" in rest else len(line)]
                                    # checks that v is a valid object to dump
                                    if (v in ("global", "local", "constant", "tokens", "space")):
                                        # adds dump token
                                        tokens.append(Token("dump", v))
                                    else:
                                        print(f"{self.colors.output}{v}{self.colors.reset}", len(v))
                                    # increases i
                                    i += len(v) + 1
                                i += len(keyword)
                                break
                            # checks whether a variable exists
                            if (keyword == "existing"):
                                # checks that there is an argument
                                if (len(line) > i + len(keyword) and line[i + len(keyword)] == " "):
                                    # get the rest of the code
                                    rest = line[i + len(keyword) + 1:]
                                    v = line[i + len(keyword) + 1:(rest.index("\n")+i+len(keyword)+1) if "\n" in rest else len(line)]
                                    # adds the existing token
                                    tokens.append(Token("existing", v))
                                    # increases i
                                    i += len(v) + 1
                                i += len(keyword)
                                break
                            # watches for variable changes
                            if (keyword == "watch"):
                                # gets the rest of the code
                                rest = line[i + len(keyword) + 1:]
                                # checks that there is code after the watch statement
                                if ("\n" not in rest):
                                    raise Exception(3)
                                # gets variable name
                                end = rest.index("\n")+i+len(keyword)+1
                                v = line[i + len(keyword) + 1:end]
                                # increses i
                                i = end
                                # adds audit
                                self.scopes.add_audit(v)
                                break
                            # executes python code
                            if (keyword == "python"):
                                # checks that there is a code block after the python keyword
                                if (line[i + len(keyword)] == "{" or line[i + len(keyword):i + len(keyword) + 2] == " {"):
                                    # gets the python code
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
                                    # adds the python token
                                    tokens.append(Token("python", t2))
                                    # increases i
                                    i = tstart + i2 + 3
                                break
                            # increases i
                            i += len(keyword)
                            break
                # continues tokenizing
                if (found):
                    continue
                # gets to end of alphanumeric characters
                ti = i
                while ti < len(line):
                    if (not line[ti].isalnum() and not line[ti] == "_"):
                        break
                    ti += 1
                # if len wasn't zero
                if (ti != i):
                    # adds reference token
                    tokens.append(Token(REF, line[i:ti]))
                # increments ti if ti didn't change
                if (ti == i):
                    ti += 1
                # increases i
                i = ti
                # continues tokenizing
                continue
            # increments i
            i += 1
        # updates self.tokens
        self.tokens = tokens
        # returns tokens
        return tokens
    # runs python function
    def pythonFunc (self, tokens : list) -> Token:
        return Token(NUL, None)
    # runs python blocks
    def doPython (self, data : dict) -> Token:
        # gets code
        code = data["code"]
        code = self.breaklines(code)
        # removes all leading indentation
        for i in range(len(code)):
            code[i] = code[i].removeprefix("\t")
        # adds indentation
        code[0] = "\t"+code[0]
        code = "\n\t".join(code)
        # wraps code in a function
        code = "def private ():\n"+code+"\nglobal f\nf = private"
        # checks if data was given globals
        if ("globals" in data):
            # executes code with globals and locals if provided
            exec(code, data["globals"], data["locals"] if "locals" in data else data["globals"])
        else:
            # executes code without globals
            exec(code)
        # runs the code
        result = f()
        # if result is string adds quotes to it
        if (type(result) == str):
            result = '"' + result + '"'
        # returns result
        return Token(NUL, None)
    # unpacks a reference token
    def deref (self, token : Token, /, check : bool = False):
        # flag for if deref is being used to check whether a variable exists
        if (check):
            # looks through all scopes
            for i in range(len(self.scopes)):
                scope = self.scopes[i]
                if (token in scope.keys()):
                    return True
            return False
        # looks through all scopes
        for i in range(len(self.scopes)):
            # gets scopes from last to first
            scope = self.scopes[-1-i]
            # checks if the variable is in the scope
            if (token.value in scope.keys()):
                # returns the variable's value
                return scope[token.value]
        print(token, "INV DEREF")
        # undefined variable name
        raise Exception(3)
    # gets resulting token type
    def _getttype (self, value) -> str:
        r = ERR
        t = type(value)
        if (t == str):
            r = STR
        elif (t == int):
            r = INT
        elif (t == float):
            r = FLO
        elif (t == bool):
            r = BOL
        elif (t == None):
            r = NUL
        elif (t == list):
            r = LST
        elif (t == dict):
            r = DCT
        return r
    # does a mathmatical operation
    def domod (self, base : Token, op : Token, mod : Token) -> Token:
        # derefs the base and mod token if necessary
        if (mod.type == REF):
            mod = self.deref(mod)
        if (base.type == REF):
            base = self.deref(base)
        # stores if the base or mod tokens are strings
        isstr = False
        modstr = False
        # unpacks string values if necessary
        if (base.type == STR):
            isstr = True
            base.value = base.value[1:-1]
        if (mod.type == STR):
            modstr = True
            mod.value = mod.value[1:-1]
        # gets the operation
        op = op.value
        # operation result
        result = None
        # addition / concatination
        if (op == "+"):
            result = base.value + mod.value
        # subtraction
        elif (op == "-"):
            result = base.value - mod.value
        # multiplication
        elif (op == "*"):
            result = base.value * mod.value
        # division
        elif (op == "/"):
            # checks for divide by zero
            if (mod.value == 0):
                raise Exception(6)
            result = base.value / mod.value
        # modulo (remainder)
        elif (op == "%"):
            result = base.value % mod.value
        # repacks strings if necessary
        if (isstr):
            result = '"' + result + '"'
            base.value = '"' + base.value + '"'
        if (modstr):
            mod.value = '"' + mod.value + '"'
        # returns result
        return Token(self._getttype(result), result)
    # collapses expressions
    def _collapseexp (self, tokens : list, start : int) -> list:
        print(tokens, start, tokens[start])
        tind = start
        while tind < len(tokens):
            token = tokens[tind]
            print(token)
            if (token.type == REF and self.deref(token).type == FUN):
                token = self.deref(token)
                tokens[tind] = token
                tokens, placeholder = self.runfunc(tokens, tind)
                if (tokens[tind+1].type == REF):
                    break
            elif (token.type == LOG):
                if (token.value == "!"):
                    pass
            elif (token.type == EQU):
                if (tokens[tind-1].type == REF):
                    tokens[tind-1] = self.deref(tokens[tind-1])
                if (tokens[tind+1].type == REF):
                    tokens[tind+1] = self.deref(tokens[tind+1])
                if (token.value == "=="):
                    res = tokens[tind-1] == tokens[tind+1]
                elif (token.value == ">="):
                    res = tokens[tind-1].value >= tokens[tind+1].value
                elif (token.value == "<="):
                    res = tokens[tind-1].value <= tokens[tind+1].value
                elif (token.value == "!="):
                    res = tokens[tind-1] != tokens[tind+1]
                elif (token.value == ">"):
                    res = tokens[tind-1].value > tokens[tind+1].value
                elif (token.value == "<"):
                    res = tokens[tind-1].value < tokens[tind+1].value
                tokens[tind-1] = Token(BOL, res)
                print(tokens)
            tind += 1
        return tokens
    # gets the result of a mathmatical expression
    def getexp (self, tokens : list, start : int):
        tokens = self._collapseexp(tokens, start+2)
        # starting index
        i = start+2
        # result
        result = tokens[start+1]
        # unpacks reference if necessary
        if (result.type == REF):
            result = self.deref(result)
        # loops through tokens
        while i < len(tokens):
            # gets token
            token = tokens[i]
            ret = None
            # if token type isn't a modifier exit loop
            if (token.type not in self.modtokens):
                break
            # get value
            if (token.type == MAT):
                ret = self.domod(result, token, tokens[i+1])
            # something went wrong, break out of loop
            if (ret == None):
                break
            # set result
            result = ret
            # increase i
            i += 2
        # decrement i
        i -= 1
        # returns result and new index
        return result, i
    # gets the tokens that are part of a function
    def getfunc (self, tokens : list, start : int):
        # index
        i = start+3
        # bracket depth
        depth = 1
        # args
        args = []
        # building args
        build = []
        # body
        ftoks = []
        # loops through tokens to find args
        while i < len(tokens):
            token = tokens[i]
            # if depth changes
            if (token.type == PAR):
                # changes parenthesis depth
                if (token.value == "("):
                    depth += 1
                else:
                    depth -= 1
                # final closing parenthesis
                if (depth == 0):
                    args.append(tuple(build))
                    break
            # new argument
            elif (token.type == SEP):
                # append argument
                args.append(tuple(build))
                # result build
                build = []
            else:
                # add token to build
                build.append(token)
            # increment i
            i += 1
        # reset depth
        depth = 1
        # increase i
        i += 2
        # loop through tokens to find function body
        while i < len(tokens):
            # gets token
            token = tokens[i]
            # if depth changes
            if (token.type == DCT):
                # change depth
                if (token.value == "{"):
                    depth += 1
                else:
                    depth -= 1
                # final closing bracket
                if (depth == 0):
                    break
            else:
                # add token to function body tokens
                ftoks.append(token)
            # increment i
            i += 1
        # generate result
        result = Token(FUN, (tuple(args), tuple(ftoks)))
        # return result and new index
        return result, i
    def _writevars (self, func : Token, args : list) -> None:
        fargs = func.value[0]
        for i in range(len(fargs)):
            if (len(args) <= i):
                if (Token(ASS, "=") in fargs[i]):
                    arg = fargs[i][fargs[i].index(Token(ASS, "="))+1:]
                else:
                    # missing argument
                    raise Exception(9)
            else:
                arg = args[i]
            if (len(arg) == 0):
                # empty argument
                raise Exception(8)
            self.scopes[-1][fargs[i][0].value] = self.evaltokens(list(arg))[0]
    def runfunc (self, tokens : list, tind : int):
        ftok = tokens[tind]
        tind += 2
        depth = 1
        args = []
        build = []
        while tind < len(tokens):
            token = tokens[tind]
            build.append(token)
            if (token.type == PAR):
                if (token.value == "("):
                    depth += 1
                else:
                    depth -= 1
                if (depth == 0):
                    tokens.pop(tind)
                    build.pop()
                    if (len(build) > 0):
                        args.append(build)
                    break
            elif (token.type == SEP):
                build.pop()
                args.append(build)
                build = []
            tokens.pop(tind)
        tokens.pop(tind-1)
        self.scopes.new_scope()
        self._writevars(ftok, args)
        ret = self.evaltokens(list(ftok.value[1]))[0]
        if (ret.type == REF):
            ret = self.deref(ret)
        tokens[tind-2] = ret
        self.scopes.remove_scope()
        return tokens, tind
    # prints an error message
    def _perr (self, type : str, value : str) -> None:
        print(f"{self.colors.error}{type}: {value}{self.colors.reset}")
    # handles error codes
    def err (self, code : int) -> None:
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
        elif (code == 7):
            self._perr("AuditVarError", "tried to audit undefined variable")
        elif (code == 8):
            self._perr("EmptyFuncArgError", "function argument had no value")
        elif (code == 9):
            self._perr("MissingFuncArgError", "missing required function argument")
    # evaluates tokens
    def evaltokens (self, tokens) -> None:
        # converts from strings to tokens if necessary
        if (type(tokens) == str):
            tokens = self.tokenize(tokens)
        # token index
        tind = 0
        # loops through tokens
        while tind < len(tokens):
            # print(tind)
            # gets token
            token = tokens[tind]
            # error token
            if (token.type == ERR):
                raise Exception(token.value)
            # keyword tokens
            elif (token.type == KWD):
                # python
                if (token.value == "python"):
                    # next token is python code
                    if (tokens[tind+1].type == "python"):
                        # evaluates python code
                        tokens[tind] = self.doPython({"code":tokens[tind+1].value})
                    else:
                        # runs python function
                        tokens[tind] = self.pythonFunc(tokens[tind:])
                    # pops the next token
                    tokens.pop(tind+1)
                # function
                elif (token.value == "func"):
                    # gets function name
                    name = tokens[tind+1].value
                    # checks name isn't same as a constant variable
                    if (name in self.scopes[0].keys()):
                        # assignment to constant
                        raise Exception(1)
                    # puts function into lowest namespace
                    self.scopes[-1][name], tind = self.getfunc(tokens, tind)
                    # continues evaluating tokens
                    continue
                # audit
                elif (token.value == "audit"):
                    # prints audit message
                    print(f"{self.colors.audithead}AUDIT:{self.colors.audit}")
                    # checks if the next token has type audit
                    if (len(tokens) > tind+1 and tokens[tind+1].type == "audit"):
                        # checks that the argument is a valid variable name
                        if (not self.deref(tokens[tind+1].value, check=True)):
                            raise Exception(7)
                        # audits the variable
                        self._printvar(tokens[tind+1].value)
                        # increments tind
                        tind += 1
                    else:
                        # audits the NamespaceList
                        self._printvars()
                    print(self.colors.reset, end="")
                # system color
                elif (token.value == "color"):
                    # changes system color
                    self.colors[tokens[tind+1].value] = tokens[tind+2].value
                    # increases tind
                    tind += 2
                # dump
                elif (token.value == "dump"):
                    # performs a dump
                    self._dump(tokens[tind+1].value, tokens)
                    # increments tind
                    tind += 1
                # existing
                elif (token.value == "existing"):
                    # checks that the given variable name exists
                    self._exists(tokens[tind+1].value)
                    # increments tind
                    tind += 1
                # return
                elif (token.value == "return"):
                    return tokens[tind+1:]
            # config token
            elif (token.type == CON):
                if (token.value[0] in self.flags.keys()):
                    # sets system flag
                    self.flags[token.value[0]] = {"on":True, "off":False, "switch":not self.flags[token.value[0]]}[token.value[1]]
                else:
                    v = token.value[0]
                    if (v == "audit"):
                        self.scopes.audit = {"on":True, "off":False, "switch":not self.scopes.audit}[token.value[1]]
            # assignment token
            elif (token.type == ASS):
                # checks assignment type
                if (token.value == "="):
                    # checks that assignment is not being done to a constant variable
                    if (self.tokens[tind-1].value in self.scopes[0].keys()):
                        # assignment to constant
                        raise Exception(1)
                    # sets variable and tind
                    self.scopes[-1][self.tokens[tind-1].value], tind = self.getexp(tokens, tind)
                else:
                    # expands assignment operator
                    tokens.insert(tind+1, Token(MAT, token.value[0]))
                    tokens.insert(tind+1, Token(REF, tokens[tind-1].value))
                    tokens[tind] = Token(ASS, "=")
                    # continues evaluation
                    continue
            # mathmatical operator
            elif (token.type == MAT):
                ret, ni = self.getexp(tokens, tind-2)
                for i in range((ni-tind)+1):
                    tokens.pop(tind)
                tokens[tind-1] = ret
                continue
            # function token
            elif (token.type == FUN):
                tokens, placeholder = self.runfunc(tokens, tind)
            # reference token
            elif (token.type == REF and (len(tokens)-1 == tind or tokens[tind+1].type != ASS)):
                tokens[tind] = self.deref(token)
                continue
            # increments tind
            tind += 1
        return tokens
    # checks if a variable exists
    def _exists (self, name : str) -> None:
        # does the check
        x = self.deref(name, check=True)
        # formats message
        x = {True:"exists", False:"does not exist"}[x]
        # prints message
        print(f"{self.colors.output}variable \"{name}\" {x}{self.colors.reset}")
    # dumps program tokens
    def _dumptokens (self, tokens : list) -> None:
        # start dump
        print(f"{self.colors.output}dumping tokens{self.colors.reset}")
        # loop over tokens
        for token in tokens:
            # print formatted token
            print(token.dump())
        # end dump
        print(f"{self.colors.output}end dump{self.colors.reset}")
    # dumps the NamespaceList
    def _dumpspace (self) -> None:
        # start dump
        print(f"{self.colors.output}dumping namespaces:{self.colors.reset}")
        # print NamespaceList
        print(self.scopes)
        # end dump
        print(f"{self.colors.output}end dump{self.colors.reset}")
    # does a dump
    def _dump (self, scope : str, tokens : list = None) -> None:
        # if tokens are being dumped
        if (scope == "tokens"):
            self._dumptokens(tokens)
            return
        # if NamespaceList is being dumped
        if (scope == "space"):
            self._dumpspace()
            return
        # sets auditing to true
        self.scopes.auditing = True
        # gets scope index
        index = 1 if scope == "global" else len(self.scopes) - 1 if scope == "local" else 0
        # prints which scope is being dumped
        print(f"{self.colors.output}dumping {scope} scope:{self.colors.reset}")
        # gets scope
        scope = self.scopes[index]
        # loops over scope keys
        for key in scope.keys():
            # prints key value pairs
            print(f"{key} : {scope[key]}")
        # end dump
        print(f"{self.colors.output}end dump{self.colors.reset}")
        # sets auditing to false
        self.scopes.auditing = False
    # prints values of a variable name from all scopes
    def _printvar (self, vname : str) -> None:
        # sets auditing to true
        self.scopes.auditing = True
        # loops over all scopes
        for i in range(len(self.scopes)):
            # gets scope
            scope = self.scopes[i]
            # checks that the variable is in the scope
            if (vname in scope.keys()):
                # prints variable scope
                print(self.colors.audithead, "globa scope:" if i == 1 else f"local scope ({i-2}):" if i > 1 else "constant scope:", self.colors.audit, end=" ")
                # prints variable
                print(f"{vname} = {scope[vname]}")
        # sets auditing to false
        self.scopes.auditing = False
    # prints all variables
    def _printvars (self) -> None:
        # sets auditing to true
        self.scopes.auditing = True
        # loops over all scopes
        for i in range(len(self.scopes)):
            # gets scope
            scope = self.scopes[i]
            # prints what scope it is
            print(self.colors.audithead, "global scope:" if i == 1 else f"local scope ({i-2}):" if i > 1 else "constant scope:", self.colors.audit)
            # loops over scope keys
            for key in scope.keys():
                # prints formatted variable mapping
                print(f"\t{key} : {scope[key]}")
        # sets auditing to false
        self.scopes.auditing = False
    # runs the interpreter
    def run (self) -> None:
        # sets maximum error code
        self.mec = 9
        # error info
        errinfo = None
        try:
            # runs program
            self.evaltokens(self.lines)
        except Exception:
            # gets exception info
            info = sys.exc_info()
            # checks that exception argument is a valid error code
            if (type(info[1].args[0]) == int and info[1].args[0] >= 0 and info[1].args[0] <= self.mec and info[0] == Exception and not self.flags["error"]):
                # sets error info
                errinfo = info[1].args[0]
            else:
                # re-raises error
                raise info[1]
        # checks if the vars flag is set
        if (self.flags["vars"]):
            # prints all variables
            self._printvars()
        # checks if the tokens flag is set
        if (self.flags["tokens"]):
            # prints all tokens
            self._dumptokens()
        # checks if there was an error
        if (errinfo != None):
            # displays error message
            self.err(errinfo)

# instansiates the interpreter
inter = Interpreter(suppress=True)

inter.run()