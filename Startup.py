import prepare
import run

mode = input("[C] Compile or [E] Execute or [R] Run >> ").upper()
##Compile, packages all files into a .ls file
##Execute, run a .ls file
##Run, runs scripts in .lava files, or allows script to be entered.

def join(arr,sep):
    s = ""
    for i in arr:
        s+=str(i)+str(sep)
    return s[0:-len(sep)]

workingDir = "."

if(mode==""):
    mode = "R"
    
if(mode == "E"):
    pass #run .ls file
elif(mode == "C"):
    pass #Package into .ls file
else:
    file = input("Load from *.lava file? [Y/N] >> ").upper()
    
    if(file == "Y"):
        f = input("File location >> ")
        if(not f.endswith(".lava")):
            f += ".lava"

        workingDir = join(f.replace("\\",".").replace("/",".").split(".")[0:-2],"/")        
        code = open(f).read()
        print("Running " + f)
    else:
        code = run.getCode()

    x = prepare.Tokenize(code)
    treeData = x.start()
    envSetup = run.StartRunning()
    envSetup.start(treeData,workingDir)
