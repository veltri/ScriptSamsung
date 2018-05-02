#!/usr/bin/env python3

import sys
import os
import time
from os import listdir
from os.path import isfile, join, getsize
from optparse import OptionParser
import subprocess
from sys import stdout, stderr

__basePath = os.path.dirname(sys.argv[0])
__execFolder = "solvers"
__tmpFolder = "tmp"
__tboxFolder = "tbox"
__aboxFolder = "abox"
__resultFilename = "results.txt"
__relevPredsFilename = "relevPreds.txt"
__dlv = "dlv"
__dlvSK = "dlv"
__dlvEx = "dlvEx"
__owl2dpm = "owl2dpm.jar"
__tstore2facts = "tstore2facts.jar"
__skolemizeScript = "skolemize.py"
__dlvRelevPreds = "dlvRelevPreds"

def errorMessage(msg):
    sys.stderr.write("Error: "+msg.__str__()+"\n")
    sys.exit()

def manageOptions():
    usage = "usage: %prog [options] [filenames] (if no options are given it behaves like DLV)"
    parser = OptionParser(usage=usage)
    parser.add_option("--mode",action="store",type="string",dest="mode",
                      help="set execution mode (a value from {'obqa','clear-workspace','asp','load-results'}")
    parser.add_option("--import",action="store",type="string",dest="inputFormalism",
                      help="specify an input formalism between 'owl' (OWL2) and 'dpm' (Datalog+/-)")
    parser.add_option("--run",action="store",type="string",dest="run",
                      help="""choose a strategy (a value from {'pchase','datarewclip','skdlv'} and evaluate the 
                      input query after converting the input knowledge base, if needed (valid only in 'obqa' mode)""")
    parser.add_option("--tbox",action="store",type="string",dest="tbox",
                      help="set the tbox folder name (a valid path to be given)")
    parser.add_option("--abox",action="store",type="string",dest="abox",
                      help="set the abox folder name (a valid path to be given)")
    parser.add_option("--kb",action="store",type="string",dest="kb",
                      help="set the kb folder name (a valid path to be given)")
    parser.add_option("--query",action="store",type="string",dest="query",
                      help="set the query file name (a valid path to be given)")
    parser.add_option("--cautious",action="store_true",default=False,dest="cautious",
                      help="run DLV under the cautious assumption (valid only in 'asp' mode)")
    parser.add_option("--brave",action="store_true",default=False,dest="brave",
                      help="run DLV under the brave assumption (valid only in 'asp' mode)")
    return parser.parse_args()

def getBenchFolder(benchFolder):
    folderPath = os.path.abspath(benchFolder)
    localFolderName = os.path.abspath(os.path.join(folderPath, os.pardir)).__str__().replace("/","_")
    localFolderPath = os.path.join(__basePath,__tmpFolder,localFolderName)
    return localFolderPath

def manageBenchFolders(inputFolderName,outputFolderName):
    localFolderPath = getBenchFolder(inputFolderName)
    if os.path.exists(os.path.join(localFolderPath,outputFolderName)):
        subprocess.call(["rm","-r",os.path.join(localFolderPath,outputFolderName)])
    if not os.path.exists(os.path.join(__basePath,__tmpFolder)):
        subprocess.call(["mkdir",os.path.join(__basePath,__tmpFolder)])
    if not os.path.exists(localFolderPath):
        subprocess.call(["mkdir",localFolderPath])
    subprocess.call(["mkdir",os.path.join(localFolderPath,outputFolderName)])
    return os.path.join(localFolderPath,outputFolderName)

def processTBox(inputFolder,formalism):
    if not os.path.isdir(inputFolder):
        errorMessage(inputFolder.__str__()+" is not a valid folder")
    outputFolder = manageBenchFolders(inputFolder,__tboxFolder)
    inputPath = os.path.abspath(inputFolder)    
    execPath = os.path.join(__execFolder,__owl2dpm)
    for file in os.listdir(inputPath):
        srcFile = os.path.join(inputPath,file)
        trgFile = os.path.join(outputFolder,file.__str__().replace(".owl","_owl")+".rul")
        subprocess.call(["java","-jar",execPath,srcFile,trgFile])
    return outputFolder

def processABox(inputFolder,formalism):
    if not os.path.isdir(inputFolder):
        errorMessage(inputFolder.__str__()+" is not a valid folder")
    outputFolder = manageBenchFolders(inputFolder,__aboxFolder) 
    inputPath = os.path.abspath(inputFolder)
    execPath = os.path.join(__execFolder,__tstore2facts)
    subprocess.call(["java","-Xmx8192m","-DentityExpansionLimit=100000000","-jar",execPath,inputPath,outputFolder])
    return outputFolder

def checkRunningFolder(inputFolder,outputFolder):
    localFolderPath = getBenchFolder(inputFolder)
    if os.path.exists(os.path.join(localFolderPath,outputFolder)):
        return os.path.join(localFolderPath,outputFolder)
    if not os.path.exists(os.path.join(__basePath,__tmpFolder)):
        subprocess.call(["mkdir",os.path.join(__basePath,__tmpFolder)])
    if not os.path.exists(localFolderPath):
        subprocess.call(["mkdir",localFolderPath])
    subprocess.call(["mkdir",os.path.join(localFolderPath,outputFolder)])
    for file in os.listdir(inputFolder):
        subprocess.call(["cp",os.path.join(inputFolder,file),os.path.join(localFolderPath,outputFolder,file)])
    return os.path.join(localFolderPath,outputFolder)

def obqa(approach,rulFolder,dataFolder,queryFile):
    if approach == "pchase":
        execPath = os.path.join(__execFolder,__dlvEx)
        rulFiles = [os.path.join(rulFolder,fpath) for fpath in os.listdir(rulFolder)]
        dataFiles = [os.path.join(dataFolder,fpath) for fpath in os.listdir(dataFolder)]
        inputDLVEx = [execPath]+rulFiles+dataFiles+[queryFile]+["-cautious","-silent","-nofinitecheck","-ODMS+"]
        with open(os.path.join(__basePath,__resultFilename),'w+') as resultFile:
            subprocess.call(inputDLVEx,stdout=resultFile)
    elif approach == "skdlv":
        rulFiles = [os.path.join(rulFolder,fpath) for fpath in os.listdir(rulFolder)]
        #skolemize the input ontology
        skPath = os.path.join(__execFolder,__skolemizeScript)
        skRulFiles = []
        for file in rulFiles:
            skFile = file.__str__()+"__sk__"
            subprocess.call([skPath,file,skFile])
            skRulFiles.append(skFile)
        #compute relevant predicates
        dlvRelevPredsPath = os.path.join(__execFolder,__dlvRelevPreds)
        with open(os.path.join(__basePath,__tmpFolder,__relevPredsFilename),'w+') as relevPredsFile:
            subprocess.call([dlvRelevPredsPath]+rulFiles+[queryFile]+["-cautious","-silent","-nofinitecheck"],stderr=relevPredsFile)
        with open(os.path.join(__basePath,__tmpFolder,__relevPredsFilename)) as relevPredsFile:
            relevPredsList = [line.strip("\n") for line in relevPredsFile]
            #filter out any data file not relevant for the query at hand
            dataFiles = [os.path.join(dataFolder,fpath) for fpath in os.listdir(dataFolder) if fpath[:-5] in relevPredsList]
            #skolemize the input query: TODO!!!
            dlvSKPath = os.path.join(__execFolder,__dlvSK)
            inputDLVSK = [dlvSKPath]+skRulFiles+dataFiles+[queryFile]+["-cautious","-silent","-nofinitecheck","-ODMS+"]
            with open(os.path.join(__basePath,__resultFilename),'w+') as resultFile:
                subprocess.call(inputDLVSK,stdout=resultFile)
        #delete temporary files
        subprocess.call(["rm",os.path.join(__basePath,__tmpFolder,__relevPredsFilename)])
        for skFile in skRulFiles:
            subprocess.call(["rm",skFile])
    else:
        errorMessage("Approach not supported yet")
    

if __name__ == '__main__':    
    (option,args) = manageOptions()
    optionList = [o for o in sys.argv[1:] if o.__str__().startswith("-")]
    
    if len(optionList) == 0: #no options, hence run DLV
        print("Running... ",end='')
        runningStart = time.time()
        execPath = os.path.join(__basePath,__execFolder,__dlv)
        params = [execPath] + ['-silent'] + sys.argv[1:]
        subprocess.call(params)
        runningEnd = time.time()
        print("Completed in "+str('%.3f'%(runningEnd-runningStart))+" secs")
        sys.exit()
        
    if option.mode == None:
        errorMessage("execution mode not set")
    if len(args) > 0:
        errorMessage("commands not found ({})".format(args))
        
    print("Started...")
    #######___OBQA mode___#######
    if option.mode == "obqa":    
        if option.cautious != False or option.brave != False:
            errorMessage("reasoning policy (brave or cautious) can be specified only in 'asp' mode")
        if option.inputFormalism == None and option.run == None:
            errorMessage("neither 'import' nor 'run' command specified in 'obqa' mode")
        
        rulFolder=None
        dataFolder=None
        
        print("Input pre-processing... ",end='')
        importStart = time.time()
        if option.inputFormalism != None:
            if option.inputFormalism != "owl" and option.inputFormalism != "dpm":
                errorMessage("input formalism not known")
            if option.inputFormalism == "owl" and (option.tbox == None or option.abox == None):
                errorMessage("no input folders (tbox or abox)")
            if option.inputFormalism == "owl" and option.kb != None:
                errorMessage("--kb option cannot be specified when input is in OWL (use --tbox and --abox options)")
            if option.inputFormalism == "dpm" and option.kb != None and (option.tbox != None or option.abox != None):
                errorMessage("--kb option cannot be specified together with --tbox or --abox options")
                        
            #manage input knowledge base
            if option.tbox != None:
                rulFolder = processTBox(option.tbox,option.inputFormalism)
            if option.abox != None:
                dataFolder = processABox(option.abox,option.inputFormalism)
            if option.kb != None:
                processKB(option.kb)
            importEnd = time.time()
            print("Completed in "+str('%.3f'%(importEnd-importStart))+" secs")
        else:
            print("Not required")
        
        print("Running... ",end='')
        runningStart = time.time()
        if option.run != None:
            if option.run != "pchase" and option.run != "datarewclip" and option.run != "skdlv":
                errorMessage("approach not known")
            if (option.tbox == None or option.abox == None) and option.kb == None:
                errorMessage("no input folders (tbox, abox or kb)")
            if option.kb != None and (option.tbox != None or option.abox != None):
                errorMessage("kb and abox/tbox folders names cannot be specified together")
            if option.query == None:
                errorMessage("no input query")
            
            if rulFolder == None:
                rulFolder = checkRunningFolder(option.tbox,__tboxFolder)
            if dataFolder == None:
                dataFolder = checkRunningFolder(option.abox,__aboxFolder)
            obqa(option.run,rulFolder,dataFolder,option.query)
            runningEnd = time.time()
            print("Completed in "+str('%.3f'%(runningEnd-runningStart))+" secs")
        else:
            print("Not required")
    
    #######___CLEAR_WORKSPACE mode___#######
    elif option.mode == "clear-workspace":
        runningStart = time.time()
        tmpFolderPath = os.path.join(__basePath,__tmpFolder)
        if os.path.exists(tmpFolderPath):
            subprocess.call(["rm","-r",tmpFolderPath])
        runningEnd = time.time()
        print("Completed in "+str('%.3f'%(runningEnd-runningStart))+" secs")

    #######___ASP_mode___#######
    elif option.mode == "asp":
        print("Running... ",end='')
        runningStart = time.time()
        if option.brave == None and option.cautious == None:
            errorMessage("no reasoning strategy (neither brave nor cautious")
        if option.brave == True and option.cautious == True:
            errorMessage("multiple reasoning strategies")
        if (option.inputFormalism != None or option.abox != None or option.tbox != None or 
            option.kb != None or option.run != None or option.query != None):
            errorMessage("options not valid")
                    
        if option.brave == True:
            asp(args,"brave")
        elif option.cautious == True:
            asp(args,"cautious")
        runningEnd = time.time()
        print("Completed in "+str('%.3f'%(runningEnd-runningStart))+" secs") 
    
    #######___LOAD_RESULTS_mode___#######
    elif option.mode == "load-results":
        runningStart = time.time()
        resultPath = os.path.join(__basePath,__resultFilename)
        os.system("gedit "+resultPath)
        runningEnd = time.time()
        print("Completed in "+str('%.3f'%(runningEnd-runningStart))+" secs")
        sys.exit()
    else:
        errorMessage("execution mode not known")
        
