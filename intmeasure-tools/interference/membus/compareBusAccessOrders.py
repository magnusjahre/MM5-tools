
import sys

def readFile(filename):
    order = []
    
    file = open(filename)
    for line in file.readlines()[1:]:
        data = line.split(";")
        order.append(data[1])

    return order

if len(sys.argv) != 3:
    print 'Usage: python -c "import fairmha.compareBusAccessOrders" <sharedFile> <aloneFile>'
    sys.exit(-1)
    
print "Reading shared file "+sys.argv[1]
so = readFile(sys.argv[1])

print "Reading alone file "+sys.argv[2]
ao = readFile(sys.argv[2])

matchCnt = 0
missCnt = 0
for i in range(len(so)):
    if so[i] == ao[i]:
        print so[i]+" Match!"
        matchCnt += 1
    else:
        print so[i]+" Miss!"
        missCnt += 1
        
print "Checking finished, matched "+str(matchCnt)+" addrs and missed "+str(missCnt)+" addrs"