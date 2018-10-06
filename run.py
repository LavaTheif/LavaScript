import prepare
import inspect
import re

imports = {}
system = None
natives = None
workingDir = "."

def getSystemClass():
    global natives
    natives = Natives()
    system = Env(None, "LavaScript.utils.System")
    ##Init natives
    system.setFunc("log",["native",natives.print])
    system.setFunc("toString",["native",natives.toString])
    system.setFunc("getString",["native",natives.getString])
    system.setFunc("getInteger",["native",natives.getInteger])
    system.setFunc("getDouble",["native",natives.getDouble])
    system.setFunc("getBoolean",["native",natives.getBoolean])
    return system

class Env():
    def __init__(self, parent, name="Main"):
        self.parent = parent
        self.vars = {}
        self.functions = {}
        self.imports = {}##{Name:classID}
        self.id = name
        
        if(parent==None):
            global system
            self.imports["System"] = "LavaTheif.utils.System"
            imports["LavaTheif.utils.System"] = system
            self.setFunc("toString",["native",natives.toString])

    ##Depreciated##
    #def get(self, name):
    #    return self.getVar(name)
    def importNew(self, classID):
        if(self.parent!=None):
            raise Exception("Imports can not be imported inside a block")
        if(not classID in imports.keys()):#File already imported
            code = open(workingDir+"/"+classID+".lava").read()
            x = prepare.Tokenize(code)
            treeData = x.start()
            imports[classID] = treeData            
        self.imports[classID.split("/")[-1]] = classID

    
    def instantize(self, name):
        if(name in self.imports):
            classID = self.imports[name]
            instance = Env(None, classID)
            treeData = imports[classID]
            if(isinstance(treeData, Env)):
                return treeData
            evalList(treeData, instance)
            return instance
        elif(self.parent != None):
            return self.parent.instantize(name)
        else:
            return None

    def getVar(self, name):
        if(name in self.vars):
            return self.vars[name]
        elif(self.parent != None):
            return self.parent.getVar(name)
        else:
            return None

    def getFunc(self, name):
        if(name in self.functions):
            return self.functions[name]
        elif(self.parent != None):
            return self.parent.getFunc(name)
        else:
            raise Exception("Function '"+name+"' not found.")


    def getVarWithParent(self, name):
        if(name in self.vars):
            return self
        elif(self.parent != None):
            return self.parent.getVarWithParent(name)
        else:
            return None

    def setVar(self, name, value, glob=False):
        if(name in self.vars):
            #Already defined in the env
            self.vars[name]=value
        elif(self.parent != None):
            #Check if defined in parents
            p = self.parent.getVarWithParent(name)
            if(p!=None):
                #Defined in parent, so set it there
                p.setVar(name, value)
            else:
                #Not defined in a parent, define it local
                self.vars[name]=value
        else:
            #Doesn't have a parent
            self.vars[name]=value 

    def setFunc(self, name, content):
        if(self.parent == None):
            self.functions[name]=content
        else:
            raise Exception("Cannot create function inside function") 


##Native Functions
class Natives:
    def print(self, env, *args):
        string = ""
        for arg in args:
            if(isinstance(arg, tuple)):
                string+=str(eval_exp(arg, env)[1])
            elif(isinstance(arg, Env)):
                string+= str(callFunction(("Function",[("name",("Token","toString")), ("args",[])]), arg)[1])#1011 = name 111=args
            else:
                string += str(arg)
            string += " "
        print(string[0:-1])

    def toString(self, env):
        return ("String","Class Object of Class "+env.id.replace("/","."))
    
    def getString(self, env, message):
        self.print(message)
        return input(str(message[1]).strip() + " >> ")

    def getInteger(self, env, message):
        try:
            return int(self.getString(env,message))
        except Exception:
            return self.getInteger(env, message)
                
    def getDouble(self, env, message):
        try:
            return float(self.getString(env,message))
        except Exception:
            return self.getDouble(env, message)
                
    def getBoolean(self, env, message):
        message = ("Boolean",str(message[1]).strip()+" [y/n]")
        return self.getString(env,  message).lower()=="y"
##END##

class StartRunning():
    def start(self, treeList, workDir = "."):
        global system
        global workingDir
        if(system == None):
            system = getSystemClass()

        workingDir = workDir
        
        self.env = Env(None)
        evalList(treeList, self.env)

        self.allowUserInputs()

    def allowUserInputs(self):
        while(True):
            code = getCode()
            if(code == "quit()"):
                break
            try:
                x = prepare.Tokenize(code)
                treeData = x.start()
                output = evalList(treeData, self.env)
                if(output != None and output != ""):
                    if(not isinstance(output, bool)):
                        natives.print(self.env,">> ",output)
            except Exception as e:
                if(e=="list index out of range" or e=="string index out of range"):
                    print("Did you miss a semi colon?")
                else:
                    print(e)
                
def getCode(code = "", i=0):
    code += input("code >> "+("    "*i))
    i=0
    for char in code:
        if(char=='}'):
            i-=1
        elif(char=='{'):
            i+=1

    if(i==0):
        return code
    else:
        return getCode(code+"\n", i)

def eval_exp(exp, env):
    typ = exp[0]
    ##Integer, Double, String, Assignment, Operation, Token, Function
    ##TODO remove python int str etc
    if(typ == "Integer"):
        return ("Integer", int(exp[1]))
    
    elif(typ == "Boolean"):
        if(isinstance(exp[1], str)):
            return ("Boolean", exp[1].lower()=="true")
        return ("Boolean", exp[1])
    
    elif(typ == "Double"):
        return ("Double", float(exp[1]))
    
    elif(typ == "String"):
        return ("String", str(exp[1]))#should already be string

    elif(typ == "Comparator"):###TODO: DOESNT WORK WITH INSTANCES
        return compare(exp, env)

    elif(typ == "Negate"):
        return ("Boolean",not eval_exp(exp[1], env))
        
    elif(typ == "."):
        left = eval_exp(exp[1][0][1], env)
        return eval_exp(exp[1][1][1], left)
        
    elif(typ == "Token"):
        name = exp[1]
        val = env.getVar(name)
        if(val == None):
            val = env.instantize(name)
        
        if(val == None):
            raise Exception("Variable "+name+" does not exist")
        else:
            return val
        
    elif(typ == "Assignment"):
        name = exp[1][0][1][1]
        val = eval_exp(exp[1][1][1], env)
        env.setVar(name, val)
        
    elif(typ == "Keyword"):
        if(exp[1][0]=="new"):
            return env.instantize(exp[1][1][1])
        
    elif(typ == "Operation"):###TODO: DOESNT WORK WITH INSTANCES
        return exec_operation(exp, env)#returns ("Value", result)
    elif(typ=="Function"):
        return callFunction(exp, env)
        #if(len(exp[1])==3):
        #elif(len(exp[1])==2):
        #else:
        #    raise Exception("Function Error")
    else:
        pass

keyWordData=""
pause = False
envCall = None
def evalList(body, env, function=None):
    i=0
    out = ""
    global keyWordData
    global envCall
    global pause
    store = None
    while i < len(body):
        envCall = env
        #print(function)
        #print(pause)
        if(not(function == None) and not(store == None)):
            #print(">>> "+str(store))
            if(not pause):
                if(function == env):
                    pause = True
                return store
            #else:
            #    pause = False

        line = body[i]#for each line
        if(line[0]=="Keyword"):
            i+=1
            name = line[1][0]

            if(name == "if"):
                ifStmnt = Env(env, env.id)
                keyWordData = eval_exp(line[1][1][1][0], ifStmnt)[1]
                if(keyWordData):
                    store = evalList(line[1][2][1], ifStmnt, function)
                    
            elif(name == "while"):
                whileLoop = Env(env, env.id)
                boolean = eval_exp(line[1][1][1][0], whileLoop)
                while(boolean[1]):
                    boolean = eval_exp(line[1][1][1][0], whileLoop)
                    store = evalList(line[1][2][1], whileLoop, function)
                    
            elif(name == "for"):
                assign = line[1][1][1][0]
                boolean = line[1][1][1][1]
                incrementer = line[1][1][1][2]
                forLoop = Env(env, env.id)
                eval_exp(assign, forLoop)
                while(eval_exp(boolean, forLoop)[1]):
                    store = evalList(line[1][2][1], forLoop, function)
                    eval_exp(incrementer, forLoop)
                    
            elif(name == "else"):
                if(not keyWordData):
                    ifStmnt = Env(env, env.id)
                    code = line[1][1][1]
                    if(isinstance(code[0], list)):
                        code = code[0]
                    store = evalList(code, ifStmnt, function)
                    
            elif(name == "return"):
                pause = False
                if(line[1][1]==None):
                    return ""#TODO change
                return eval_exp(line[1][1], env)
            elif(name == "func"):
                createFunction(line[1][1], env)
            elif(name == "import"):
                classID = getClassID(line[1][1])
                env.importNew(classID)
                
            continue #Already executed code
        try:#Try and run code, if it fails, print error
            store = eval_exp(line, env)
        except Exception as e:
            if(e=="string index out of range" or e=="list index out of range"):
                print("Did you miss a semi colon?")
            else:
                print(e)
        i+=1
    return store

def getClassID(tup, classID=""):
    if(tup[1][0]=="Token"):
        classID+=tup[1][1]
        return classID
    elif(tup[0]=="Token"):
        classID+=tup[1]
        return classID
    elif(tup[0]=="."):
        classID+=tup[1][0][1][1]+"/"
        return getClassID(tup[1][1][1],classID)
    #elif(tup[0]=="Symbol" and tup[1]==";"):
    #    break
    else:
        raise Exception("Invalid symbol in imports: "+str(tup[0]))

def createFunction(exp, env):
    name = exp[1][0][1][1]
    args = []
    for t,n in exp[1][1][1]:
        args.append(n)
    fn = ["func",args,exp[1][2][1]]
    env.setFunc(name, fn)

def callFunction(exp, env):
    global envCall
    args = list((eval_exp(a, envCall) for a in exp[1][1][1]))#Args are from the main section
    name = exp[1][0][1][1]
    fn = env.getFunc(name)
    if(fn[0]=="func"):#builtins
        params = fn[1]
        if(len(params)!=len(args)):
            raise Exception(name+"() expected "+str(len(params))+" parameters, but got "+str(len(args))+".")
        body = fn[2]
        funcEnv = Env(env, env.id)
        for p, a in zip(params, args):
            funcEnv.setVar(p, a)
        return evalList(body, funcEnv, funcEnv) ##return values
    elif(fn[0]=="native"):
        a=formatValue(fn[1](env, *args))
        return a
        ##TODO change error msg if too many args
        #if(len(insepct.getargspec(fn)!=len(args)):
        #    raise Exception("Invalid arguments.  Expected "+str(len(params))+" got "+str(len(args))+".")
    
def compare(exp, env):
    typ = exp[1][0][1]

    left = exp[1][1][1]
    right = exp[1][2][1]

    left = eval_exp(left, env)
    right = eval_exp(right, env)
    
    if(typ=='=='):
        return ("Boolean",left[1]==right[1])
    elif(typ=='>='):
        return ("Boolean",left[1]>=right[1])
    elif(typ=='<='):
        return ("Boolean",left[1]<=right[1])
    elif(typ=='!='):
        return ("Boolean",left[1]!=right[1])
    elif(typ=='>'):
        return ("Boolean",left[1]>right[1])
    elif(typ=='<'):
        return ("Boolean",left[1]<right[1])

    elif(typ=='&&'):#and
        return ("Boolean",left[1] and right[1])
    elif(typ=='||'):#or
        return ("Boolean",left[1] or right[1])
    elif(typ=='^'):#xor
        return ("Boolean",left[1] ^ right[1])

def exec_operation(exp, env):
    typ = exp[1][0][1]
    left = exp[1][1][1]
    right = exp[1][2][1]
    left = eval_exp(left, env)
    right = eval_exp(right, env)

    ##if token, maybe pull token value?? idk yet
    if(left[0]=="String" or right[0]=="String"):
        if(typ=="+"):
            return ("String",str(left[1])+str(right[1]))
        else:
            ##Maybe add *
            raise Exception("Unable to complete operation '"+typ+"' on type String")
    else:
        retType = "Integer"
        if(left[0]=="Double" or right[0]=="Double"):
            retType = "Double"
        if(typ=="+"):
            return (retType, left[1]+right[1])
        elif(typ=="-"):
            return (retType, left[1]-right[1])
        elif(typ=="/"):
            return (retType, left[1]/right[1])
        elif(typ=="*"):
            return (retType, left[1]*right[1])


def formatValue(value):
    if(isinstance(value, str)):
        return ("String", value)
    elif(isinstance(value, bool)):
        return ("Boolean", value)
    elif(isinstance(value, float)):
        return ("Double", value)
    elif(isinstance(value, int)):
        return ("Integer", value)
    else:
        return value

