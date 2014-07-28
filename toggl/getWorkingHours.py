#!/usr/bin/python

import sys
from optparse import OptionParser
from toggl import *

def parseArgs():
    
    parser = OptionParser(usage="getWorkingHours.py [options] year")
    #parser.add_option("--threads", '-t', action="store", dest="threads", default=4, type="int", help="Number of worker threads")
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    year = int(args[0])

    return opts, year

if __name__ == '__main__':
    opts, year = parseArgs()
    #params = {"workspace_id": "626815", "user_agent": "api_test"}
    #data = togglRequest("https://toggl.com/reports/api/v2/weekly", params)
    redDays = getRedDays(year)
    halfDays = getHalfDays(year)
    for i in range(1,54):
        print i, getWeekDayRange(year, i)
