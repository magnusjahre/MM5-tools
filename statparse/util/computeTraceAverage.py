#!/usr/bin/env python

from statparse.util import fatal

from optparse import OptionParser
import optcomplete


def parseArgs():
    parser = OptionParser(usage="computeTraceAverage.py [options] FILENAME [FILENAME ...]")

    #parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    
    optcomplete.autocomplete(parser, optcomplete.AllCompleter())
    opts, args = parser.parse_args()
        
    if len(args) == 0:
        fatal("Commandline error\nUsage: "+parser.usage)
    
    return opts, args

def computeAverage(tracefile):

    separator = ";"

    head = tracefile.readline().strip()
    headsplit = head.split(separator)[1:]
    linelen = len(headsplit)

    accumulator = [0 for i in range(len(headsplit))]

    lines = 0.0
    for l in tracefile:
        data = l.split(separator)

        if len(data[1:]) != linelen:
            fatal("Cannot parse line: "+l)

        for i in range(linelen):
            accumulator[i] += float(data[i+1])
        
        lines += 1

    for i in range(linelen):
        print headsplit[i],
        print accumulator[i] / lines

def main():

    opts, args = parseArgs()

    try:
        tracefile = open(args[0])
    except:
        fatal("Cannot open file "+str(args[0]))

    computeAverage(tracefile)

if __name__ == '__main__':
    main()
