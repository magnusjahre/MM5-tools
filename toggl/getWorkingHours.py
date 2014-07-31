#!/usr/bin/python

import sys
from optparse import OptionParser
from toggl import *
from statparse.printResults import printData, numberToString

def parseArgs():
    
    parser = OptionParser(usage="getWorkingHours.py [options] year")
    parser.add_option("--decimals", action="store", dest="decimals", default=1, type="float", help="Number of decimals")
    parser.add_option("--leave", action="store", dest="leave", default="", help="Leave: comma separated list of week-number:days pairs")
    parser.add_option("--holiday", action="store", dest="holiday", default="", help="Holiday: comma separated list of week-number:days pairs")
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    year = int(args[0])

    return opts, year

def getReducedDays(week, reductions):
    days = 0
    for r in reductions:
        if week in r:
            days += r[week]
    return days

def printHours(year, opts, reductions):
    printdata = [["Week", "Start Date", "Hours Worked", "Expected Hours", "Difference", "Comment"]]
    leftJust = [True, True, False, False, False, True]
    for i in range(1,54):
        dayrange = getWeekDayRange(year, i)
        params = {"workspace_id": "626815", 
                  "user_agent": "magnus.jahre@idi.ntnu.no", 
                  "since": str(dayrange[0]),
                  "client_ids": "15314619"}
        data = togglRequest("https://toggl.com/reports/api/v2/weekly", params)
        
        weekTotals = data['week_totals']
        weekHrs = [float(d)/(1000.0*60.0*60.0) for d in weekTotals]

        reducedDays = getReducedDays(i, reductions)
        expectedHrs = getExpectedHours(dayrange, year, reducedDays)
        diff = weekHrs[-1] - expectedHrs

        comment = ""
        if reducedDays > 0:
            comment = str(reducedDays)+" days holiday/leave"

        printdata.append([str(i),
                          str(dayrange[0]),
                          numberToString(weekHrs[-1], opts.decimals),
                          numberToString(expectedHrs, opts.decimals),
                          numberToString(diff, opts.decimals),
                          comment])
    
    printData(printdata, leftJust, sys.stdout, opts.decimals)

def parseHourReductionString(text):
    if text == "":
        return {}

    reductions = {}
    pairs = text.split(",")
    for p in pairs:
        pair = p.split(":")
        try:
            week = int(pair[0])
            days = int(pair[1])
        except:
            print "Could not parse reduction string "+text
        assert week not in reductions
        reductions[week] = days
    return reductions

def parseReductions(opts):
    reductionList = []
    leave = parseHourReductionString(opts.leave)
    if leave != {}:
        reductionList.append(leave)
    holiday = parseHourReductionString(opts.holiday)
    if holiday != {}:
        reductionList.append(holiday)
    return reductionList

if __name__ == '__main__':
    opts, year = parseArgs()
    reductions = parseReductions(opts)
    printHours(year, opts, reductions)
    
