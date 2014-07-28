#!/usr/bin/python

import sys
from optparse import OptionParser
from toggl import *
from statparse.printResults import printData, numberToString

def parseArgs():
    
    parser = OptionParser(usage="getWorkingHours.py [options] year")
    parser.add_option("--decimals", action="store", dest="decimals", default=1, type="float", help="Number of decimals")
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    year = int(args[0])

    return opts, year

def printHours(year, opts):
    printdata = [["Week", "Start Date", "Hours Worked", "Expected Hours", "Difference"]]
    leftJust = [True, True, False, False, False]
    for i in range(1,54):
        dayrange = getWeekDayRange(year, i)
        params = {"workspace_id": "626815", 
                  "user_agent": "magnus.jahre@idi.ntnu.no", 
                  "since": str(dayrange[0]),
                  "client_ids": "15314619"}
        data = togglRequest("https://toggl.com/reports/api/v2/weekly", params)
        
        weekTotals = data['week_totals']
        weekHrs = [float(d)/(1000.0*60.0*60.0) for d in weekTotals]

        expectedHrs = getExpectedHours(dayrange, year)
        diff = weekHrs[-1] - expectedHrs
        printdata.append([str(i),
                          str(dayrange[0]),
                          numberToString(weekHrs[-1], opts.decimals),
                          numberToString(expectedHrs, opts.decimals),
                          numberToString(diff, opts.decimals)])
    
    printData(printdata, leftJust, sys.stdout, opts.decimals)

if __name__ == '__main__':
    opts, year = parseArgs()
    printHours(year, opts)
    
