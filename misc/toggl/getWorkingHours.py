#!/usr/bin/python

import sys
from optparse import OptionParser
from misc.toggl import *
from statparse.printResults import numberToString
from datetime import *
import time

def parseArgs():
    
    parser = OptionParser(usage="getWorkingHours.py [options] year")
    parser.add_option("--decimals", action="store", dest="decimals", default=1, type="float", help="Number of decimals")
    parser.add_option("--sick", action="store", dest="sick", default="", help="Sick: comma separated list of week-number:days pairs")
    parser.add_option("--holiday", action="store", dest="holiday", default="", help="Holiday/Leave: comma separated list of week-number:days pairs")
    parser.add_option("--input-hours", action="store", dest="inputHours", default=0, type="int", help="Number of hours balance from previous year")
    parser.add_option("--outfile", action="store", dest="outfile", default="workinghours.html", help="File to results to (Default: workinghours.html)")
    opts, args = parser.parse_args()
    
    if len(args) != 1:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    year = int(args[0])

    return opts, year

def getReducedDays(week, reductionDict):
    days = 0
    if week in reductionDict:
        days += reductionDict[week]
    return days

def printHours(year, opts, holiday, sick):
    printdata = [["Week", "Start Date", "Worked Hours", "Expected Hours", "Difference", "Yearly Balance", "Overall Balance", "Comment"]]
    balance = opts.inputHours
    yearBalance = 0
    for i in range(1,54):
        print "Processing week",i
        dayrange = getWeekDayRange(year, i)
        if dayrange[0] > date.today():
            break

        params = {"workspace_id": "626815", 
                  "user_agent": "magnus.jahre@idi.ntnu.no", 
                  "since": str(dayrange[0]),
                  "billable": "yes"}
        data = togglRequest("https://toggl.com/reports/api/v2/weekly", params)
        
        weekTotals = data['week_totals']
        weekHrs = []
        for d in weekTotals:
            if d == None:
                weekHrs.append(0.0)
            else:
                weekHrs.append(toHours(d))

        holidayDays = getReducedDays(i, holiday)
        sickDays = getReducedDays(i, sick)
        expectedHrs = getExpectedHours(dayrange, year, holidayDays+sickDays)
        diff = weekHrs[-1] - expectedHrs
        yearBalance += diff
        balance += diff

        comment = ""
        if holidayDays > 0 and sickDays > 0:
            comment = str(holidayDays)+" days holiday/leave and "+str(sickDays)+" days sick"
        elif holidayDays > 0:
            comment = str(holidayDays)+" days holiday/leave"
        elif sickDays > 0:
            comment = str(sickDays)+" days sick"

        printdata.append([str(i),
                          str(dayrange[0]),
                          numberToString(weekHrs[-1], opts.decimals),
                          numberToString(expectedHrs, opts.decimals),
                          numberToString(diff, opts.decimals),
                          numberToString(yearBalance, opts.decimals),
                          numberToString(balance, opts.decimals),
                          comment])
    
    print "Writing output to file", opts.outfile
    printHTML(printdata, opts.outfile)
    
def printHTML(data, filename):
    f = open(filename, "w")
    
    print >> f, "<html><head>"
    print >> f, "<title>Working hours</title>"
    print >> f,"""<style>
                table {
                    width:100%;
                }
                table, th, td {
                    border: 1px solid black;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 5px;
                    text-align: center;
                }
                table.names tr:nth-child(even) {
                    background-color: #f1f1c1;
                }
                table.names tr:nth-child(odd) {
                   background-color:#ffffff;
                }
                table.names th    {
                    background-color: #c1c1c1;
                }
                #greencell {
                    color: green;
                }
                #redcell {
                    color: red;
                }
                </style>"""
    print >> f, "</head><body>"
    print >> f, "<table class=\"names\">"
    
    print >> f, "<tr>"
    for element in data[0]:
        print >> f, "<th>",element,"</th>",
    print >> f, "</tr>"
    
    for line in data[1:]:
        print >> f, "<tr>"
        cnt = 0
        for element in line:
            if cnt == 4:
                val = float(element)
                if val < 0:
                    print >> f, "<td id=\"redcell\">",element,"</td>",
                else:
                    print >> f, "<td id=\"greencell\">",element,"</td>",
            else:
                print >> f, "<td>",element,"</td>",
            cnt += 1
        print >> f, "</tr>"
    
    print >> f, "</table>"
    print >> f,"<br><br><i>Working hours overview generated "+time.strftime("%d.%m.%Y %H:%M")+"</i><br><br>"
    print >> f, "</body></html>"
    
    f.close()

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
    holiday = parseHourReductionString(opts.holiday)
    sick = parseHourReductionString(opts.sick)
    return holiday, sick

if __name__ == '__main__':
    opts, year = parseArgs()
    
    print
    print "Toggle Working Hours with Norwegian Holidays"
    print
    
    holiday, sick = parseReductions(opts)
    printHours(year, opts, holiday, sick)
    