#!/usr/bin/env python3

import sys
import os
import time
from os import listdir
from os.path import isfile, join, getsize
from optparse import OptionParser
import subprocess

basePath = os.path.dirname(sys.argv[0])
execFolder="solvers"
tmpFolder="tmp"
tboxFolder="tbox"
aboxFolder="abox"
resultFilename="result.txt"
dlv = "dlv"
dlvEx = "dlvEx"
owl2dpm = "owl2dpm.jar"
tstore2facts = "tstore2facts.jar"

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

def manageFolders(folderName):
    folderPath = os.path.abspath(folderName)
    localFolderName = os.path.abspath(os.path.join(folderPath, os.pardir)).__str__().replace("/","_")
    localFolderPath = os.path.join(basePath,tmpFolder,localFolderName)
    if os.path.exists(localFolderPath):
        subprocess.call(["rm","-r",localFolderPath])
    if not os.path.exists(os.path.join(basePath,tmpFolder)):
        subprocess.call(["mkdir",os.path.join(basePath,tmpFolder)])
    subprocess.call(["mkdir",localFolderPath])
    return localFolderPath

def processTBox(inputFolder,outputFolder,formalism):
    if not os.path.isdir(inputFolder):
        errorMessage(inputFolder.__str__()+" is not a valid folder")
    
    inputPath = os.path.abspath(inputFolder)    
    subprocess.call(["mkdir",os.path.join(outputFolder,tboxFolder)])
    execPath = os.path.join(execFolder,owl2dpm)
    for file in os.listdir(inputPath):
        srcFile = os.path.join(inputPath,file)
        trgFile = os.path.join(outputFolder,tboxFolder,file.__str__().replace(".owl","_owl")+".rul")
        subprocess.call(["java","-jar",execPath,srcFile,trgFile])

def processABox(inputFolder,outputFolder,formalism):
    if not os.path.isdir(inputFolder):
        errorMessage(inputFolder.__str__()+" is not a valid folder")
    
    inputPath = os.path.abspath(inputFolder)
    subprocess.call(["mkdir",os.path.join(outputFolder,aboxFolder)])
    execPath = os.path.join(execFolder,tstore2facts)
    localABoxFolder = os.path.join(outputFolder,aboxFolder,"/")
    print("java -jar "+execPath+" "+inputPath+" "+localABoxFolder)
    subprocess.call(["java","-Xmx8192m","-DentityExpansionLimit=100000000","-jar",execPath,inputPath,localABoxFolder])

if __name__ == '__main__':    
    (option,args) = manageOptions()
    optionList = [o for o in sys.argv[1:] if o.__str__().startswith("-")]
    if len(optionList) == 0: #run DLV
        print("Running... ",end='')
        runningStart = time.time()
        execPath = os.path.join(basePath,execFolder,dlv)
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
        
        print("Input preprocessing... ",end='')
        importStart = time.time()
        if option.inputFormalism != None:
            if option.inputFormalism != "owl" and option.inputFormalism != "dpm":
                errorMessage("input formalism not known")
            if (option.tbox == None or option.abox == None) and option.kb == None:
                errorMessage("no input folders (tbox, abox or kb)")
            if option.kb != None and (option.tbox != None or option.abox != None):
                errorMessage("kb and abox/tbox folders names cannot be specified together")
        
            localFolderPath = None
            if option.tbox != None:
                localFolderPath = manageFolders(option.tbox)
            elif option.abox != None:
                localFolderPath = manageFolders(option.abox)
                
            if option.tbox != None:
                processTBox(option.tbox,localFolderPath,option.inputFormalism)
            if option.abox != None:
                processABox(option.abox,localFolderPath,option.inputFormalism)
            if option.kb != None:
                processKB(option.kb,option.inputFormalism)
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
            
            obqa(option.run)
            runningEnd = time.time()
            print("Completed in "+str('%.3f'%(runningEnd-runningStart))+" secs")
        else:
            print("Not required")
    
    #######___CLEAR_WORKSPACE mode___#######
    elif option.mode == "clear-workspace":
        tmpFolderPath = os.path.join(basePath,tmpFolder)
        if os.path.exists(tmpFolderPath):
            subprocess.call(["rm","-r",tmpFolderPath])

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
        basePath = os.dir.path.dirname(sys.args[0])
        resultPath = os.path.join(basePath,execFolder,tmpFolder,resultFilename)
        os.system("gedit "+resultPath)
        sys.exit()
        
    else:
        errorMessage("execution mode not known")
        
