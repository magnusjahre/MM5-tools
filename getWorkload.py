
import sys
import workloads

try:
    list = workloads.workloads[int(sys.argv[1])][int(sys.argv[2])][0]
    id = 0
    for bm in list:
        print str(id)+": "+bm
        id = id + 1
except:
    print "Usage: python -c \"import getWorkload\" np workloadID"
