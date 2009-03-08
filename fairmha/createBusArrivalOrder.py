
import sys

def readFile(filename):
    newOrder = {}
    
    file = open(filename)
    for line in file.readlines()[1:]:
        data = line.split(";")
        if len(data) == 10:
            seqnum = int(data[9])
        elif len(data) == 7:
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
        outfile.write(str(k).ljust(20)+str(order[k]).ljust(20)+"\n")
    outfile.flush()
    outfile.close()

def find(element, list):
    index = len(list) / 2

    while list[index] != element:
        if list[index] < element:
            index = index / 2
        elif list[index] > element:
            index = index + (index/2)
    
    assert False
    return index

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

akeys = ao.keys()
akeys.sort()

for sk in skeys:
    aindex = find(sk, akeys)

