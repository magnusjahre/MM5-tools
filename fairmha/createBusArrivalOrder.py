
import sys

def readFile(filename):
    newOrder = {}
    
    file = open(filename)
    for line in file.readlines()[1:]:
        data = line.split(";")
        if len(data) == 11:
            seqnum = int(data[9])
        elif len(data) == 8:
            seqnum = int(data[6])
        else:
            print "Error: unknown trace file format"
            sys.exit(-1)
        addr = int(data[1])
        
        if addr in newOrder:
            newOrder[addr].append(seqnum)
        else:
            newOrder[addr] = [seqnum]
        
#        assert seqnum not in newOrder
#        newOrder[seqnum] = addr

    return newOrder

def writeFile(order, filename):
    keys = order.keys()
    keys.sort()
    
    outfile = open(filename, "w")
    for k in keys:
        addr,anum = order[k]
        outfile.write(str(k).ljust(20))
        outfile.write(str(addr).ljust(20))
        outfile.write(str(anum).ljust(20))
        outfile.write("\n")
    outfile.flush()
    outfile.close()

def find(element, list):
    left = 0
    right = len(list)
    probe = (right - left) / 2

    while left < right:
        probe = left + ((right - left) / 2)
        
        if list[probe] < element:
            left = probe+1
        else:
            right = probe
            
    if left < len(list) and list[left] == element:
        return left
    
    print "Fatal: Value "+str(element)+" not found"    
    sys.exit(-1)

if len(sys.argv) != 3:
    print 'Usage: python -c "import fairmha.createBusArrivalOrder" <sharedFile> <aloneFile>'
    sys.exit(-1)
    
print "Reading shared file "+sys.argv[1]
so = readFile(sys.argv[1])
#writeFile(so, "shared-order.txt")

print "Reading alone file "+sys.argv[2]
ao = readFile(sys.argv[2])
#writeFile(ao, "alone-order.txt")

print "Analyzing results.."
analysisResult = {}

skeys = so.keys()
skeys.sort()

skipCnt = 0
useCnt = 0

for sk in skeys:
    if sk in ao:
        sSeqNums = so[sk]
        aSeqNums = ao[sk]
        
        if len(sSeqNums) <= len(aSeqNums):
            for i in range(len(sSeqNums)):
                assert sSeqNums[i] not in analysisResult

                analysisResult[sSeqNums[i]] = (aSeqNums[i], sk)

                useCnt += 1
        else:
            skipCnt += 1
            print "Warning: skipping address "+str(sk)+" (2)"
    else:
        skipCnt += 1
        print "Warning: skipping address "+str(sk)+" (1)"

print "Used "+str(useCnt)+", skipped "+str(skipCnt)

writeFile(analysisResult, "sharedAloneSeqNums.txt")

resultKeys = analysisResult.keys()
resultKeys.sort()

hits = 0
misses = 0
prevNum = -1
for sn in resultKeys:
    aSeq,addr = analysisResult[sn]
    
    if aSeq == prevNum + 1:
        hits += 1
    else:
        misses += 1

    prevNum = aSeq

print "Prev pred correct "+str(float(hits)/float(len(resultKeys)))
print "Prev pred wrong "+str(float(misses)/float(len(resultKeys)))
                             