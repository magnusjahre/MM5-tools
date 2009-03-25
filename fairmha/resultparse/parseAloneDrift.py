
import sys
import pbsconfig
import parsemethods

def getIDs(cmd, config):
    sharedID = pbsconfig.get_unique_id(config)
    wl = parsemethods.getBenchmark(cmd)
    
    aloneIDs = []
    for i in range(np):
        tmpaparams = pbsconfig.get_alone_params(wl, i, config)
        tmpID = pbsconfig.get_unique_id(tmpaparams)
        aloneIDs.append(tmpID)

    return sharedID, aloneIDs

if len(sys.argv) != 2:
    print "Number of CPUs must be provided as an argument"
    sys.exit(0)

np = int(sys.argv[1])

kw = 40
nw = 10

print "".ljust(kw),
for i in range(np):
    print ("CPU"+str(i)).rjust(nw),
print

for cmd,config in pbsconfig.commandlines:
    if pbsconfig.get_np(config) == np:
        sID,aIDs = getIDs(cmd,config)
        error,diff = parsemethods.getAloneDrift(sID,aIDs)
        
        print sID.ljust(kw),
        for e in error:
            try:
                print ("%.2f" % e).rjust(nw),
            except TypeError:
                print e.rjust(nw),
        print
