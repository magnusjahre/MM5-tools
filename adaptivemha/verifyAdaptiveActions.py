
import sys

CPUS = 4

if len(sys.argv) != 7:
    print "Usage:  python -c \"import adaptivemha.verifyAdaptiveActions\" adaptiveMHATrace.txt memoryBusTrace.txt 0.9 0.7 5 8"
    sys.exit(-1)
    
print
print "- Adaptive MHA Verification -"
print
    
print "Verifying adaptive trace file " + sys.argv[1]
print "Memory bus usage is taken from file " + sys.argv[2]
print "High threshold = "+ sys.argv[3]
print "Low threshold = "+ sys.argv[4]
print "Repeats = "+ sys.argv[5]
print "Init MSHR count = "+ sys.argv[6]

NEEDED_REPEATS = int(sys.argv[5])
initMSHRs = int(sys.argv[6])

highThres = float(sys.argv[3])
lowThres = float(sys.argv[4])

adaptivetrace = open(sys.argv[1])
memtrace = open(sys.argv[2])

adaptivelines = adaptivetrace.readlines()
memtracelines = memtrace.readlines()

if len(adaptivelines) == len(memtracelines):
    print "The files have the same length, starting verification.."
else:
    print "The files have different lengths, cannot verify, quitting.."
    sys.exit(-1)
     
print

mshrs = []
for i in range(0,CPUS):
    mshrs.append(initMSHRs)
    
repeats = 0
currID = -1

for i in range(1, len(adaptivelines)):
    adaptiveArray = adaptivelines[i].split(';')
    memArray = memtracelines[i].split(';')
    
    if adaptiveArray[0] != memArray[0]:
        print "FATAL: Clock cycle mismatch"
        sys.exit(-1)

    #decreased = False
    large = False
    small = False
    actuallyReduced = False
    actuallyIncreased = False
    if float(memArray[2]) >= highThres:
        
        large = True
        
        maxNum = 0
        maxId = -1
        tmpId = 0
        for e in memArray[7:11]:
            if int(e) > maxNum and mshrs[tmpId] > 1:
                maxNum = int(e)
                maxId = tmpId
            tmpId = tmpId + 1
            
        if maxId != -1:
            if maxId == currID:
                repeats = repeats + 1
                if repeats == NEEDED_REPEATS:
                    actuallyReduced = True
                    if mshrs[maxId] != 1:
                        mshrs[maxId] = mshrs[maxId] >> 1
                    repeats = 0
            else:
                currID = maxId
                repeats = 1
                
                if repeats == NEEDED_REPEATS:
                    actuallyReduced = True
                    if mshrs[maxId] != 1:
                        mshrs[maxId] = mshrs[maxId] >> 1
                    repeats = 0
        
        #decreased = True
    else:
        repeats = 0
        currID = -1
        
    if float(memArray[2]) <= lowThres:
        
        small = True
        
        minNum = 2000
        minID = -1
        tmpId = 0
        for m in mshrs:
            if m < minNum:
                minNum = m
                minID = tmpId
            
            tmpId = tmpId + 1
        
        if mshrs[minID] != initMSHRs:
            actuallyIncreased = True
            mshrs[minID] = mshrs[minID] << 1
    
    #if not decreased:
        #repeats = 0
        #currID = -1
    
    cnt = 0
    success = True
    for e in adaptiveArray[1:5]:
        if int(e) != mshrs[cnt]:
            success = False
        cnt = cnt +1
    
    if not success:
        print adaptiveArray
        print "FATAL: mshr state was not changed correctly at cycle "+adaptiveArray[0]
        print "Was: "+str(adaptiveArray[1:5])
        print "Should be:"+str(mshrs)
        sys.exit(-1)
        
    print str(adaptiveArray[0]).ljust(10),
    print (str(large)+":").ljust(7)+(str(currID)+", "+str(repeats)).rjust(5),
    print str(small).rjust(7),
    print (str(adaptiveArray[1:5])+" = "+str(mshrs)).rjust(40),
    print "OK!".rjust(5),
    
    if actuallyReduced:
        print "Reducing!".rjust(10),
    elif actuallyIncreased:
        print "Increasing!".rjust(10),
    print
    
print
print "Adaptive MHA behaviour verified!"
print