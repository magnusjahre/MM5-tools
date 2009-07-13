
import sys
import re

##### PROCEDURES ###########################################

def handleState(procData):

    if caches[bank].has_key(set):
        for d in procData:
            tmp = d.split("=")
            if int(tmp[1]) != caches[bank][set][tmp[0]]["cnt"]:
                print "State error 1, count is "+str(caches[bank][set][tmp[0]]["cnt"])+" tmp is "+tmp[1]
                print "Bank: "+bank+", set: "+set+" data: "+str(caches[bank][set])
                exit()
    else:
        caches[bank][set] = {}
        for d in procData:
            tmp = d.split("=")
            caches[bank][set][tmp[0]] = {"cnt": int(tmp[1])}
            if int(tmp[1]) != 0:
                print "State error 2"
                exit()


def handleNewLine(string):
    addrPattern = re.compile("addr is [0-9a-f]*")
    procPattern = re.compile("proc [0-9a-f]")
    addr = addrPattern.findall(string)[0].split(" ")[2]
    proc = procPattern.findall(string)[0].split(" ")[1]
    
    # assumes that a state line has been printed before
    if caches[bank][set]["p"+proc].has_key("stack"):
        caches[bank][set]["p"+proc]["stack"].insert(0,addr)
        if len(caches[bank][set]["p"+proc]["stack"]) > 2:
            print "Handle new line error 1"
            exit()
    else:
        caches[bank][set]["p"+proc]["stack"] = [addr]

    caches[bank][set]["p"+proc]["cnt"] = caches[bank][set]["p"+proc]["cnt"] + 1
    if caches[bank][set]["p"+proc]["cnt"] > 2:
        print "Handle new line, too large allocation, "+str(caches[bank][set]["p"+proc]["cnt"])
        exit()


def handleHit(string):
    addrPattern = re.compile("addr is [0-9a-f]*")
    procPattern = re.compile("processor [0-9]")

    addr = addrPattern.findall(string)[0].split(" ")[2]
    proc = procPattern.findall(string)[0].split(" ")[1]

    stack = caches[bank][set]["p"+proc]["stack"]

    if len(stack) > 2:
        print "Handle hit, too large allocation"
        exit()

    if addr != stack[0] and addr != stack[1]:
        print "Handle hit, hit in address not stored in cache"
        exit()

    if stack[0] != addr:
        # swap
        tmp = stack[0]
        stack[0] = stack[1]
        stack[1] = tmp

    caches[bank][set]["p"+proc]["stack"] = stack
    
def handleReplacement(string):

    proc1pat = re.compile("processor [0-9]")
    proc2pat = re.compile("proc [0-9]")
    newAddrPattern = re.compile("request addr is [0-9a-f]*")
    oldAddrPattern = re.compile("replaced block addr is [0-9a-f]*")

    p1 = proc1pat.findall(string)[0].split(" ")[1]
    p2 = proc2pat.findall(string)[0].split(" ")[1]

    newAddr = newAddrPattern.findall(string)[0].split(" ")[3]
    oldAddr = oldAddrPattern.findall(string)[0].split(" ")[4]

    if p1 != p2:
        print "Handle replacement, replacing block from different processor"
        exit()

    if caches[bank][set]["p"+p1]["cnt"] > 2:
        print "Handle Replacement: to large allocation block count detected"
        exit()

    stack = caches[bank][set]["p"+p1]["stack"]
    
    if len(stack) > 2:
        print "Handle Replacement: to large allocation detected"
        exit()
    
    if stack[1] != oldAddr:
        print "Handle replacement: wrong block got evicted"
        exit()
    
    stack[1] = stack[0]
    stack[0] = newAddr

    caches[bank][set]["p"+p1]["stack"] = stack



##### MAIN SCRIPT ##########################################

# don't change (it won't work :-) )
PROCS = 4
# Assumes an 8-way associative cache


if len(sys.argv) != 2:
    print "Usage: python -c \"import fairmha.validateUniformCachePart\" filename"
    exit()

bankPattern = re.compile("L2Bank[0-9]")
setPattern = re.compile("Set [0-9]*")

statePattern = re.compile("p[0-9]=[0-9]")
notTouchedPattern = re.compile("Choosing block.*proc [0-9]")
hitPattern = re.compile("Hit in block.*processor [0-9].*addr is [0-9a-f]*")
replacedPattern = re.compile("Replacing block.*processor [0-9].*req by proc [0-9].*addr is [0-9a-f].*")

caches = {}
for i in range(4):
    caches["L2Bank"+str(i)] = {}

tracefile = open(sys.argv[1])
lines = tracefile.readlines()
tracefile.close()

for line in lines:

    line = line.strip()
    line = line.strip("\0")

    bankRes = bankPattern.findall(line)
    setRes = setPattern.findall(line)

    # Only consider tracelines
    if len(bankRes) == 1 and len(setRes) == 1:
        bank = bankRes[0]
        set = setRes[0].split(" ")[1]
        
        # Cache state lines
        states = statePattern.findall(line)
        if len(states) == PROCS:
            #print states
            handleState(states)
            continue
        
        # Inserts into lines that are not touched
        newLine = notTouchedPattern.findall(line)
        if len(newLine) == 1:
            #print newLine
            handleNewLine(newLine[0])
            continue

        # Cache hits
        hitLine = hitPattern.findall(line)
        if len(hitLine) == 1:
            #print hitLine
            handleHit(hitLine[0])
            continue

        # Replacements
        replLine = replacedPattern.findall(line)
        if len(replLine) == 1:
            #print replLine
            handleReplacement(replLine[0])
            continue


print "Trace file has been parsed completely without errors!"
