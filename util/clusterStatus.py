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
        self.queue = data[1]
        self.user = data[3]
        self.state = data[4]
        self.nodes = int(data[6])
        self.reason = data[7]

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

def printQueueStatus(jobstate, qname, status, opts):
    print "Status of "+jobstate+" jobs in queue "+qname+":"
    qs = sortQueueStatus(status)
    for u,cnt in qs:
        print u.ljust(opts.userWidth)+str(cnt).rjust(4)
    print

def readSqueueOutput(output, opts):
    # Dict structure: queue -> user -> [reason for pending] -> nodecnt
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
        printQueueStatus("running", opts.queue, runningStatus[opts.queue], opts)
        printQueueStatus("pending", opts.queue, pendingStatus[opts.queue], opts)
    else:
        for q in runningStatus:
            printQueueStatus("running", q, runningStatus[q], opts)
            printQueueStatus("pending", q, pendingStatus[q], opts)

def main():
    opts, args = parseArgs()
    
    print
    print "CLUSTER STATUS"
    print

    command = ["squeue"]
    output = check_output(command)
    data = readSqueueOutput(output, opts)

    

if __name__ == '__main__':
    main()
