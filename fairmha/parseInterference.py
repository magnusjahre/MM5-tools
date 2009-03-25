
import sys
import getInterference
import parsemethods
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
                    text += str(data[k][wl][reskey][i]).rjust(w)
                else:
                    text += str(data[k][wl][i]).rjust(w)
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


options = {"ic_entry": "IC Entry",
           "ic_transfer": "IC Transfer",
           "ic_delivery": "IC Delivery",
           "bus_entry": "Bus Entry",
           "bus_queue": "Bus Queue",
           "bus_service": "Bus Service",
           "total": "Total",
           "all": "",
           "one": "",
           "rwerror": "",
           "breakdown": ""}

if len(sys.argv) < 3 or sys.argv[2] not in options:
    print "Usage: python -c \"import fairmha.parseInterference\" np interference_type [absolute]"
    print "Usage: python -c \"import fairmha.parseInterference\" np all"
    print "Usage: python -c \"import fairmha.parseInterference\" np one workload"
    print "Usage: python -c \"import fairmha.parseInterference\" np rwerror"
    print "Usage: python -c \"import fairmha.parseInterference\" np breakdown"
    print
    print "Available Commands:"
    for a in options:
        print a
    sys.exit()
    

np = int(sys.argv[1])
printAll = False
printOne = False
printWl = ""
printRW = False
printAbsError = False
printBreakdown = False
if sys.argv[2] == "all":
    print "Writing all results to files..."
    printAll = True
elif sys.argv[2] == "one":
    printOne = True
    printWl = sys.argv[3]
elif sys.argv[2] == "rwerror":
    printRW = True
elif sys.argv[2] == "breakdown":
    printBreakdown = True
#    printAbsError = True
else:
    pattern = options[sys.argv[2]]

if len(sys.argv) >= 4 and sys.argv[3] == "absolute":
    printAbsError = True

if printOne:
    for cmd, config in pbsconfig.commandlines:
        wl = parsemethods.getBenchmark(cmd)
        if wl == printWl:
            shName,aloneNames = getFilenames(cmd,config)
            getInterference.getInterferenceBreakdownError(shName,aloneNames,True)

    sys.exit()


data = {}
reqerrors = {}
for cmd, config in pbsconfig.commandlines:
    shName, aloneNames = getFilenames(cmd,config)
    wl = parsemethods.getBenchmark(cmd)
    key = pbsconfig.get_key(cmd, config)
    if key not in data:
        data[key] = {}
    assert wl not in data[key]
    data[key][wl] = getInterference.getInterferenceErrors(shName,aloneNames,printAbsError)

    if key not in reqerrors:
        reqerrors[key] = {}
    assert wl not in reqerrors[key]
    
    reqerrors[key][wl] = getInterference.getReadWriteCount(shName,aloneNames)

if printAll:
    for o in options:
        if options[o] != "":
            text = createOutputText(data,options[o])
            
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
            assert "Total" in data[key][wl]
            for o in options:
                if options[o] != "" and options[o] != "Total":
                    
                    for i in range(np):
                        if i not in newdata[key][wl]:
                            newdata[key][wl][i] = {}

                        assert options[o] not in newdata[key][wl][i]
                        newdata[key][wl][i][options[o]] = data[key][wl][options[o]][i]

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


else:
    print createOutputText(data, pattern)
    
    
