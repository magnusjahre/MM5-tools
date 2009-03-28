
import sys
import interferencemethods
import fairmha.resultparse.parsemethods as parsemethods
from optparse import OptionParser
import pbsconfig

def createOutputText(data, reskey):

    text = ""

    w = 20
    keys = data.keys()
    keys.sort()

    text += "".ljust(w)
    for k in keys:
        for i in range(np):
            text += (str(k)+"_CPU"+str(i)).rjust(w)
    text += "\n"

    wls = data[keys[0]].keys()
    wls.sort()

    for wl in wls:
        text += str(wl).ljust(w)
        for k in keys:
            for i in range(np):
                if reskey != None:
                    if data[k][wl] != {}:
                        text += str(data[k][wl][reskey][i]).rjust(w)
                    else:
                        text += "Error".rjust(w)
                else:
                    if data[k][wl] != {}:
                        text += str(data[k][wl][i]).rjust(w)
                    else:
                        text += "Error".rjust(w)    
        text += "\n"

    return text

def getFilenames(cmd, config):
    sharedID = pbsconfig.get_unique_id(config)
    shName = sharedID+'/'+sharedID+'.txt'
    wl = parsemethods.getBenchmark(cmd)
    
    aloneIDs = []
    aloneNames = []
    for i in range(np):
        tmpaparams = pbsconfig.get_alone_params(wl, i, config)
        tmpID = pbsconfig.get_unique_id(tmpaparams)
        aloneIDs.append(tmpID)
        aloneNames.append(tmpID+'/'+tmpID+'.txt')

    return shName, aloneNames


usage = "usage: %prog [options] <cpu-count> <architecture> <command>"
parser = OptionParser(usage=usage,prog="parseInterference.py")
parser.add_option("-a", "--absolute-error", action="store_true", dest="absolute", default="True", help="Print errors in clock cycles")
parser.add_option("-r", "--relative-error", action="store_false", dest="absolute", help="Print errors in percentage difference")
parser.add_option("-t", "--interference-type", dest="type", default="total", help="Interference type to retrieve")
parser.add_option("-w", "--workload", dest="workload", help="Workload to parse (only works with the 'one' command)")

inoptions,args = parser.parse_args()

if(len(args)) != 3:
    parser.error("incorrect number of arguments")

iTypes = {"ic-entry": "IC Entry",
           "ic-transfer": "IC Transfer",
           "ic-delivery": "IC Delivery",
           "bus-entry": "Bus Entry",
           "bus-queue": "Bus Queue",
           "bus-service": "Bus Service",
           "total": "Total"}

commands = {"all": "",
           "one-wl": "",
           "rwerror": "",
           "breakdown": "",
           "best-static": "",
           "one-type": ""}

if args[2] not in commands:
    posCom = ""
    for a in commands:
        posCom += " "+a
    
    parser.error("Unknown command\nSupported commands:"+posCom)
    
if inoptions.type not in iTypes:
    posCom = ""
    for a in iTypes:
        posCom += " "+a
    parser.error("Unknown interference type\nAvailable types:"+posCom)

np = int(args[0])
memsys = args[1]

printAll = False
printOne = False
printWl = ""
printRW = False
printAbsError = inoptions.absolute
printBreakdown = False
doBestStatic = False

if args[2] == "all":
    print "Writing all results to files..."
    printAll = True
elif args[2] == "rwerror":
    printRW = True
elif args[2] == "breakdown":
    printBreakdown = True
elif args[2] == "one-wl":
    printOne = True
    if inoptions.workload == None:
        parser.error("A workload name must be specified when the 'one' command is used")
    printWl = inoptions.workload
elif args[2] == "best-static":
    doBestStatic = True
elif args[2] == "one-type":
    assert inoptions.type != None
    pattern = iTypes[inoptions.type]
else:
    assert False, "Unknown command"



if printOne:
    for cmd, config in pbsconfig.commandlines:
        wl = parsemethods.getBenchmark(cmd)
        thisNP = pbsconfig.get_np(config)
        if wl == printWl and np == thisNP:
            shName,aloneNames = getFilenames(cmd,config)
            interferencemethods.getInterferenceBreakdownError(shName,aloneNames,True,memsys)

    sys.exit()


data = {}
reqerrors = {}
for cmd, config in pbsconfig.commandlines:
    if pbsconfig.get_np(config) != np:
        continue
    
    shName, aloneNames = getFilenames(cmd,config)
    wl = parsemethods.getBenchmark(cmd)
    key = pbsconfig.get_key(cmd, config)
    if key not in data:
        data[key] = {}
    assert wl not in data[key]
    data[key][wl] = interferencemethods.getInterferenceErrors(shName, 
                                                              aloneNames, 
                                                              printAbsError,
                                                              memsys)

    if key not in reqerrors:
        reqerrors[key] = {}
    assert wl not in reqerrors[key]
    
    if data[key][wl] != {}:
        reqerrors[key][wl] = interferencemethods.getReadWriteCount(shName,aloneNames)
    else:
        reqerrors[key][wl] = {}

if printAll:
    for o in iTypes:
        if iTypes[o] != "":
            text = createOutputText(data,iTypes[o])
            
            fname = "interference_error_"+o+".txt"
            print "Writing results for file "+fname

            tfile = open(fname, "w")
            tfile.write(text)
            tfile.flush()
            tfile.close()
elif printRW:
    print createOutputText(reqerrors, None)

elif printBreakdown:
    newdata = {}
    
    for key in data:
        
        if key not in newdata:
            newdata[key] = {}
        for wl in data[key]:
            
            if wl not in newdata[key]:
                newdata[key][wl] = {}
                
            if data[key][wl] != {}:
                assert "Total" in data[key][wl]
                for o in iTypes:
                    if iTypes[o] != "" and iTypes[o] != "Total":
                        
                        for i in range(np):
                            if i not in newdata[key][wl]:
                                newdata[key][wl][i] = {}
    
                            assert iTypes[o] not in newdata[key][wl][i]
                            newdata[key][wl][i][iTypes[o]] = data[key][wl][iTypes[o]][i]
            else:
                for o in iTypes:
                    if iTypes[o] != "" and iTypes[o] != "Total":
                        for i in range(np):
                            if i not in newdata[key][wl]:
                                newdata[key][wl][i] = {}
                            
                            newdata[key][wl][i][iTypes[o]] = "Error" 

    ndkey0 = newdata.keys()[0]
    wlkey0 = newdata[ndkey0].keys()[0]
    itypes = newdata[ndkey0][wlkey0][0].keys()
    itypes.sort()

    width = 20
    print "".ljust(width),
    for t in itypes:
        print t.rjust(width),
    print

    for k in newdata:
        for wl in newdata[k]:
            for i in newdata[k][wl]:
                print (k+"-"+wl+"-"+str(i)).ljust(width),
                for t in itypes:
                    print str(newdata[k][wl][i][t]).rjust(width),
                print

elif doBestStatic:
    
    bestResult = {}
    
    wls = data[data.keys()[0]].keys()
    wls.sort()
    
    for wl in wls:
        bestResult[wl] = [10000000 for i in range(np)]

    for key in data:
        for wl in data[key]:
            assert "Total" in data[key][wl] 
            total = data[key][wl]["Total"]
            
            for i in range(np):
                if float(total[i]) < bestResult[wl][i]:
                    bestResult[wl][i] = total[i]            
    
    
    
    width = 20
    print "".ljust(width),
    for i in range(np):
        print ("CPU"+str(i)).rjust(width),
    print
    
    for wl in wls:
        print wl.ljust(width),
        for res in bestResult[wl]:
            print str(res).rjust(width),
        print

else:
    print createOutputText(data, pattern)
    
    
