
import sys
import re

##### MAIN SCRIPT ##########################################

# don't change (it won't work :-) )
PROCS = 4
BANKS = 4
ARB_DELAY = 8

requests = [[],[],[],[]]
curFromID = {}
lowestRequest = 100000 #temp start val, assumes first request before 100000 ticks
finishTimes = [0,0,0,0,0,0,0,0]
vclock = 0

resetVclockAt = 0
curStartTag = 0

if len(sys.argv) != 2:
    print "Usage: python -c \"import fairmha.validateNFQ\" filename"
    exit()

reqPattern = re.compile("Requesting Address Bus.*")
reReqPattern = re.compile("Re-Requesting Address Bus.*")
#arbPattern = re.compile("Arbitrating address bus.*")
grantPattern = re.compile("Granting access to.*")
updateVclockPattern = re.compile("Updating virtual clock.*")
resetVclockPattern = re.compile("Resetting clock and start.*")
checkPattern = re.compile("Checking for request from.*")

tracefile = open(sys.argv[1])
lines = tracefile.readlines()
tracefile.close()

for line in lines:

    res = reqPattern.findall(line)
    if res != []:
        resarr  = res[0].split(",")
        fromInt = int(resarr[1])
        atTick = int(resarr[2])
        curVclock = int(resarr[3])
        
        if curVclock != vclock:
            print "Vclock was wrong at request (1)"
            exit()

        requests[fromInt].append((atTick, curVclock))

    res = reReqPattern.findall(line)
    if res != []:
        resarr  = res[0].split(",")
        fromInt = int(resarr[1])
        atTick = int(resarr[2])
        curVclock = int(resarr[3])
        
        if curVclock != vclock:
            print "Vclock was wrong at request (1)"
            exit()

        requests[fromInt].append((atTick, curVclock))


    res = grantPattern.findall(line)
    if res != []:
        lowestTick = 999999999999999999999999999
        lowestTag = 99999999999999999999999999
        lowestInterface = -1

        for i in range(0, PROCS+BANKS):
            if i in curFromID:
                fromInt, startTag = curFromID[i]
                reqTick, reqVclock = requests[fromInt][0]
                update = False
                
                # Start tags take priority
                if startTag < lowestTag:
                    update = True
                # If equal start tags, then oldest request first
                elif startTag == lowestTag and reqTick < lowestTick:
                    update = True
                # Equal tag and time: lowest interface id decides
                elif startTag == lowestTag and reqTick == lowestTick and fromInt < lowestInterface:
                    update = True
                
                if update:
                    lowestTag = startTag
                    lowestTick = reqTick
                    lowestInterface = fromInt
                
        curFromID.clear()

        resarr = res[0].split(",")
        grantInterface = int(resarr[1])
        grantInternalID = int(resarr[2])
        lowestTimeStamp = int(resarr[3])
        tick = int(resarr[4])

        if lowestInterface == -1:
            print "FATAL: no interface granted access at tick " + str(tick)
            exit()

        if grantInterface != lowestInterface:
            print "FATAL: granted access to interface " + str(grantInterface) + ", correct was " + str(lowestInterface) + " at tick " + str(tick)
            print requests
            exit()
 
        if lowestTimeStamp != lowestTag:
            print "FATAL: incorrect start tag, was "+str(lowestTimeStamp)+", should have been "+str(lowestTag)+ " at tick " + str(tick)

        curStartTag = lowestTag
        requests[grantInterface].pop(0)



    res = updateVclockPattern.findall(line)
    if res != []:
        resarr  = res[0].split(",")
        found = resarr[1]
        oldestID = int(resarr[2])
        tick = int(resarr[3])

        if found == "False" or oldestID == -1:
            resetVclockAt = tick

        vclock = curStartTag

    res = resetVclockPattern.findall(line)
    if res != []:
        resarr = res[0].split(",")
        tick = int(resarr[1])

        if tick != resetVclockAt:
            print "Resetting Vclock at wrong time, was "+str(tick)
        tick = -1
    
    res = checkPattern.findall(line)
    if res != []:
        resarr  = res[0].split(",")
        fromInt = int(resarr[1])
        internalID = int(resarr[2])
        startStamp = int(resarr[3])
        
        curFromID[internalID] = (fromInt, startStamp)

print "Trace file has been parsed completely without errors!"
