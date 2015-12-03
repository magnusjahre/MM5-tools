#!/usr/bin/python

import sys
from optparse import OptionParser
from toggl import *
from statparse.printResults import numberToString
from datetime import *
import time

def parseArgs():
    
    parser = OptionParser(usage="getProjectHours.py [options] project weeknum year")
    parser.add_option("--decimals", action="store", dest="decimals", default=1, type="float", help="Number of decimals")
    opts, args = parser.parse_args()
    
    if len(args) != 3:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    project = args[0]
    weeknum = int(args[1])
    year = int(args[2])

    return opts, project, weeknum, year

def getProjectHours(project, weeknum, year):
    
    taskIDMap = {"READEX": 6500697,
                 "TULIPP": 7057826}
    
    if project not in taskIDMap:
        print "FATAL: unknown project "+project+", candidates are "+taskIDMap.keys()
        sys.exit(-1)
    
    taskID = taskIDMap[project]
    
    dayrange = getWeekDayRange(year, weeknum)
    params = {"workspace_id": "626815", 
              "user_agent": "magnus.jahre@idi.ntnu.no", 
              "since": str(dayrange[0]),
              "client_ids": "15314619",
              "task_ids": taskID}
    data = togglRequest("https://toggl.com/reports/api/v2/details", params)
    
    for task in data["data"]:
        assert task["task"] == project
        print task["task"], task["description"], toHours(task["dur"])

if __name__ == '__main__':
    opts, project, weeknum, year = parseArgs()
    
    print
    print "Hours for Project "+project+", week "+str(weeknum)+" of year "+str(year)
    print
    
    getProjectHours(project, weeknum, year)