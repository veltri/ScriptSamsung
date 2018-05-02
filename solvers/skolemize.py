#!/usr/bin/env python3

import sys
import re

assert len(sys.argv) == 3
with open(sys.argv[1]) as fIn, open(sys.argv[2],'w+') as fOut:
    ruleId = 0
    for line in fIn:
        if line.startswith("#exists"):
            #print("Rule: "+line.__str__())
            posStartFr = line.find("(")
            posEndFr = line.find(")")
            headVars = line[posStartFr+1:posEndFr]
            headVars = headVars.split(",")
            headVars = [v.strip(" ") for v in headVars]
            #print("headVars: "+headVars.__str__())
            posStart = line.find("{")
            posEnd = line.find("}")
            exVars = line[posStart+1:posEnd]
            exVars = exVars.split(",")
            exVars = [v.strip(" ") for v in exVars]
            #print("exVars"+exVars.__str__())
            frVars = [v for v in headVars if v not in exVars]
            #print("frVars: "+frVars.__str__())
            skArgs = ",".join(frVars)
            outLine = line[posEnd+1:]
            for var in exVars:
                skTerm = "f"+ruleId.__str__()+"_"+var+"("+skArgs+")"
                #print("replace {} with {}".format(var,skTerm))
                outLine = re.sub(r'\b'+var+r'\b',skTerm,outLine)
            outLine = outLine.strip(" ")
            #print("skolemized rule: "+outLine)
            fOut.write(outLine)
        else:
            fOut.write(line)
        ruleId += 1
    
