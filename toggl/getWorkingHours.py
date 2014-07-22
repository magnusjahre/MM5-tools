#!/usr/bin/python

import sys
from optparse import OptionParser
from toggl import togglRequest

def parseArgs():
    
    parser = OptionParser(usage="getWorkingHours.py [options]")
    #parser.add_option("--threads", '-t', action="store", dest="threads", default=4, type="int", help="Number of worker threads")
    opts, args = parser.parse_args()
    
    if len(args) != 0:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    return opts, args

if __name__ == '__main__':
    opts, args = parseArgs()
    params = {"workspace_id": "626815", "user_agent": "api_test"}
    data = togglRequest("https://toggl.com/reports/api/v2/weekly", params)
    