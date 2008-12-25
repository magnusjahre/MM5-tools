
import sys
import workloads
import bw_workloads
import deterministic_fw_wls as fair_wls

try:

    if sys.argv[1] == "regular":
        list = workloads.workloads[int(sys.argv[2])][int(sys.argv[3])][0]
    elif sys.argv[1] == "bw":
        list = bw_workloads.bw_workloads[int(sys.argv[2])][int(sys.argv[3])][0]
    elif sys.argv[1] == "fair":
        list = fair_wls.workloads[int(sys.argv[2])][int(sys.argv[3])][0]

    id = 0
    for bm in list:
        print str(id)+": "+bm
        id = id + 1
except:
    print "Usage: python -c \"import getWorkload\" type np workloadID"
