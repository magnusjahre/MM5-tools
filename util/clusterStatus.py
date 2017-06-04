#!/usr/bin/env python

import sys
import os
from optparse import OptionParser
from util import fatal
from subprocess import check_output

def parseArgs():
    
    parser = OptionParser(usage="clusterStatus.py [options]")
    parser.add_option("--verbose", '-v', action="store_true", dest="verbose", default=False, help="Print all lines")
    parser.add_option("--user-width", action="store", type="int", dest="userWidth", default=10, help="Width of user column")
    parser.add_option("--queue", action="store", type="string", dest="queue", default="", help="Only print status of selected queue")
    opts, args = parser.parse_args()
    
    if len(args) != 0:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    return opts, args

class JobStatus:
    def __init__(self, line):
        data = line.split()
        self.queue = data[2]
        self.user = data[4]
        self.state = data[5]
        self.nodes = int(data[7])
        self.reason = data[8]

    def fixStatusDictStructure(self, status, initVal):
        if self.queue not in status:
            status[self.queue] = {}

        if self.user not in status[self.queue]:
            status[self.queue][self.user] = initVal

    def processRunningJob(self, status):
        self.fixStatusDictStructure(status, 0)
        status[self.queue][self.user] += self.nodes

    def processPendingJob(self, status):
        self.fixStatusDictStructure(status, 0)
        status[self.queue][self.user] += self.nodes
    
    def __str__(self):
        return ", ".join([self.queue, self.user, self.state, str(self.nodes), self.reason])

def sortQueueStatus(status):
    inverted = {}
    for k in status:
        inverted[status[k]] = k

    sk = sorted(inverted.keys(), reverse=True)
    data = []
    for k in sk:
        data.append([inverted[k], k])
    return data

def printQueueStatus(jobstate, qname, status, opts, clusterStatus):
    print "Status of "+jobstate+" jobs in queue "+qname+":"
    qs = sortQueueStatus(status)
    for u,cnt in qs:
        outstr = u.ljust(opts.userWidth)+str(cnt).rjust(4)
        if jobstate == "running":
            outstr += getPerc(cnt, clusterStatus[qname]["alloc"]).rjust(10)
        print outstr
    print

def processSqueueOutput(output, clusterStatus, opts):
    runningStatus = {}
    pendingStatus = {}

    lines = output.split("\n")
    for l in lines[1:]:
        if l != "":
            job = JobStatus(l) 
            
            if job.state == "R":
                job.processRunningJob(runningStatus)
            elif job.state == "PD":
                job.processPendingJob(pendingStatus)
            else:
                if opts.verbose:
                    print "Skipping job with state "+job.state+", details: "+str(job)

    if opts.queue != "":
        if opts.queue not in runningStatus.keys():
            fatal("Unknown queue "+opts.queue+", candidates are: "+" ".join(runningStatus.keys()))
        printQueueStatus("running", opts.queue, runningStatus[opts.queue], opts, clusterStatus)
        printQueueStatus("pending", opts.queue, pendingStatus[opts.queue], opts, clusterStatus)
    else:
        for q in runningStatus:
            printQueueStatus("running", q, runningStatus[q], opts, clusterStatus)
        for q in pendingStatus:
            printQueueStatus("pending", q, pendingStatus[q], opts, clusterStatus)

def processSinfoOutput(output, opts): 

    status = {}

    for l in output.split("\n")[1:]:
        if l!= "":
            data = l.split()
            queue = data[0].replace("*","")
            nodes = int(data[3])
            state = data[4].replace("*","")
            
            if queue not in status:
                status[queue] = {}
            
            if state == "comp":
                state = "alloc"
            if state == "mix":
                state = "alloc"

            if state not in status[queue]:
                status[queue][state] = 0
            status[queue][state] += nodes

    return status

def getPerc(v1, v2):
    return ("%.1f" % ((float(v1)/float(v2))*100))+" %"

def getValue(status, q, key, width):
    if key not in status[q]:
        return "0".rjust(width)
    return str(status[q][key]).rjust(width)

def printClusterStatus(status, opts):

    print "Overall Node Status:"
    print

    queuewidth = 15
    numberWidth = 6
    header = "".ljust(queuewidth)
    header += "Alloc".rjust(numberWidth)
    header += "Idle".rjust(numberWidth)
    header += "Down".rjust(numberWidth)
    header += "Alloc (%)".rjust(10)

    print header
    for q in status:
        outstr = q.ljust(queuewidth)
        outstr += getValue(status, q, "alloc", numberWidth)
        outstr += getValue(status, q, "idle", numberWidth)
        outstr += getValue(status, q, "down", numberWidth)
        
        if sum(status[q].values()) > 0 and "alloc" in status[q]:
            outstr += getPerc(status[q]["alloc"], sum(status[q].values())).rjust(10)
        else:
            outstr += "0.0 %".rjust(10)
        print outstr
        
def main():
    opts, args = parseArgs()
    
    print
    print "CLUSTER STATUS"
    print

    command = ["sinfo"]
    output = check_output(command)
    clusterStatus = processSinfoOutput(output, opts)

    command = ["squeue", "-o", '"%.18i %.15P %.8j %.8u %.2t %.10M %.6D %R"']
    output = check_output(command)
    processSqueueOutput(output, clusterStatus, opts)

    printClusterStatus(clusterStatus, opts)

if __name__ == '__main__':
    main()
