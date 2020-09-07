import re

class Tokenize:
    
    keyWords = ["if","else","while","for","return","func","import","new"]
    
    def __init__(self, data):
        self.data = data
        self.index = 0
    
    def start(self):
        token = self.tokenize()
        
        x=""
        touples = []
        while(x!=None):
            x = next(token)
            if(x==None):
                break
            touples.append(x)
        t = Tree(touples)
        return t.tree

    def tokenize(self):
        self.line = 1
        while(self.index < len(self.data)):
            '''
            Whitespace: ignore
            "String": string of chars
            number: integer
            decimal: double
            token: string of chars
            token token: else if, String name (maby define key words not as tokens)
            (){},.; :symbols
            // /**/:comment
            /*+-: operation
            '''
            char = self.data[self.index]
            if(char in " \t\n\r"):
                if(char in("\n\r")):
                    self.line+=1
                pass
            elif(char in "(){},.;=<>!&|^"):
                if(char in "=<>!|&^"):
                    nextChar = self.data[self.index+1]
                    if(char+nextChar in ["==","<=",">=","!=","&&","||"]):
                       yield("Comparator",char+nextChar, self.line)
                       self.index+=2
                       continue
                    elif(char in "<>^"):
                       yield("Comparator",char, self.line)
                       self.index+=1
                       continue
                    elif(char == "!"):
                        yield ("Negate","", self.line)
                        self.index+=1
                        continue

                yield ("Symbol",char, self.line)
                if(char == '}'):
                    yield("Symbol",';', self.line)

    
            elif(char in "/*-+%"):
                if(self.data[self.index+1]=='/' or self.data[self.index+1]=="*"):
                    self.skipComment()
                else:
                    nextChar = self.data[self.index+1]
                    if(nextChar in "+-="):
                        yield("Operation",char+nextChar, self.line)
                        self.index+=1
                    else:
                        yield("Operation",char, self.line)
                
            elif(char == '"'):
                string = self.getString('"')
                yield ("String", string, self.line)
            elif(re.match("[0-9]",char)):
                number = self.getRegex("[.0-9]")
                if("." in number):
                    yield ("Double",number, self.line)
                else:
                    yield ("Integer",number, self.line)
                
            elif(re.match("[_a-zA-Z]", char)):
                token = self.getRegex("[_a-zA-Z0-9]")
                if(token  == "true" or token == "false"):
                    yield ("Boolean",token, self.line)
                elif(token in self.keyWords):
                    yield ("Keyword", token, self.line)
                else:
                    yield ("Token", token, self.line)
            else:
                raise Exception("Unknown Token: "+token)
                
            self.index += 1
        yield None

    def skipComment(self):
        self.index += 1
        if(self.data[self.index]=="/"):
            self.getString("\n")
        elif(self.data[self.index]=="*"):
            self.getString("*/")
    
    def getString(self, terminate):
        string = ""
        char = ""
        while(not string.endswith(terminate)):
            self.index+=1
            string += self.data[self.index]
        return string[:-len(terminate)]

    def getRegex(self, regex):
        string = ""
        while(re.match(regex, self.data[self.index])):
            string+=self.data[self.index]
            self.index+=1
        self.index-=1
        return string

class Tree:
    def __init__(self, toupleList):
        self.tree = []
        self.index = 0
        self.toupleList = toupleList
        while(self.index < len(toupleList)):
            t = self.eval(None)
            if(t!=None):#isnt a blank line
                self.tree.append(t)
            self.index+=1

    def eval(self, last):
        if(self.index >= len(self.toupleList)):
            return last
        typ = self.toupleList[self.index][0]
        value = self.toupleList[self.index][1]
        lineNo = self.toupleList[self.index][2]
        self.index+=1
        if(typ == "Token"):
            return self.eval(("Token",value, lineNo))
        elif(typ == "Keyword"):
            if(value in ["return","func","new","import"]):
                return ("Keyword",[value, self.eval(None)], lineNo)
            else:
                if(value == "else"):
                    body = self.eval(None)
                    #print(body)
                    #print(value)
                    return ("Keyword",[value, ("body",[body])], lineNo)
                else:
                    return self.eval(("Keyword",[value], lineNo))

        elif(typ == "Operation"):
            if(value in ["++","--"]):
                return self.eval(("Assignment", [("left",last), ("right",self.eval(("Operation",[("type",value[0]),("left",last),("right",("Integer","1"))])))], lineNo))
            elif("=" in value):
                return self.eval(("Assignment", [("left",last), ("right",self.eval(("Operation",[("type",value[0]),("left",last),("right",self.eval(None))])))], lineNo))
            else:
                return self.eval(("Operation",[("type",value),("left",last),("right",self.eval(None))], lineNo))
        elif(typ == "Comparator"):
            return self.eval(("Comparator",[("type",value),("left",last),("right",self.eval(None))], lineNo))
        elif(typ == "Negate"):
            return ("Negate",self.eval(None), lineNo)
        elif(typ == "Symbol"):
            # ) { }
            if(value==';'):
                self.index -=1
                return last
            elif(value==')'):
                self.index -=1
                return last
            elif(value == '}'):
                self.index -=1
                return last
            elif(value == ','):
                self.index -=1
                return last
            elif(value == '='):
                return self.eval(("Assignment", [("left",last), ("right",self.eval(None))], lineNo))
            elif(value == "("):
                if(last == None):
                    x=("Brackets", [self.eval(None)], lineNo)
                    self.index+=1
                    return self.eval(x)
                elif(last[0]=="Keyword"):
                    last[1].append(("args", Tree(self.getBlock('(',')')).tree))
                    return self.eval(last)
                elif(last[0]=="Token"):
                    return self.eval(("Function", [("name",last),("args", Tree(self.getBlock('(',')')).tree)], lineNo))
                x=("Brackets", [self.eval(None)], lineNo)
                self.index+=1
                return self.eval(x)

            elif(value=="{"):
                if(last == None):
                    return Tree(self.getBlock('{','}')).tree
                elif(last[0]=="Function"):
                    last[1].append(("body", Tree(self.getBlock('{','}')).tree))
                    return last
                elif(last[0]=="Keyword"):
                    last[1].append(("body", Tree(self.getBlock('{','}')).tree))
                    return last
                else:
                    return Tree(self.getBlock('{','}')).tree
                    #return self.eval(("block",("body",Tree(self.getBlock('{','}')).tree)))
            elif(value == "."):
                return (".",[("left",last),("right",self.eval(None))], lineNo)
            else:#
                pass
                #return self.eval(("Symbol", [("type",value),("left",last), ("right",self.eval(None))]))
                ##TODO
        elif(typ=="String"):
                return self.eval(("String",value, lineNo))
        elif(typ=="Integer"):
                return self.eval(("Integer",value, lineNo))
        elif(typ=="Double"):
                return self.eval(("Double",value, lineNo))
        elif(typ=="Boolean"):
                return self.eval(("Boolean",value, lineNo))
        else:
            raise Exception("Unknown Type")
            return None
            ##TODO
    def getBlock(self, _open, terminate):
        ##Terminate **MUST** be a symbol
        argList = []
        touple = self.toupleList[self.index]
        i=1
        while(i>0):
            if(self.index >= len(self.toupleList)):
                raise Exception("EOF")
            touple = self.toupleList[self.index]
            if(touple[0]=="Symbol" and touple[1]==terminate):
                i-=1
            if(touple[0]=="Symbol" and touple[1]==_open):
                i+=1
            argList.append(touple)
            self.index+=1
        #print(argList)
        return argList
