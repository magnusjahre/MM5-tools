#!/usr/bin/python

import sys
from optparse import OptionParser
from toggl import *
from statparse.printResults import numberToString, printData
from datetime import *
import dateutil.parser

def parseArgs():
    
    parser = OptionParser(usage="getProjectHours.py [options] project weeknum year")
    parser.add_option("--decimals", action="store", dest="decimals", default=1, type="int", help="Number of decimals")
    opts, args = parser.parse_args()
    
    if len(args) != 3:
        print "Usage:"
        print parser.usage
        sys.exit()
    
    project = args[0]
    weeknum = int(args[1])
    year = int(args[2])

    return opts, project, weeknum, year

PROJECTS = ["READEX", "TULIPP"]
WEEKDAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

PROJECT_NUMBERS = {"READEX":{"WP2":90030602,"WP3":90030604,"WP4":90030606,"WP6":90030609},
                   "TULIPP":{}}

class ProjectTask:
    
    def __init__(self, wp, text):
        self.wp = wp
        self.text = text
        self.hours = [0.0 for i in range(0,7)]
        
    def addHours(self, wp, hours, weekday):
        assert wp == self.wp
        self.hours[weekday] += hours

def getWeekday(num):
    return WEEKDAYS[num]    

def parseTaskString(taskstring, togglProject):
    try:
        splitted = taskstring.split()
        project = splitted[0]
        wp = splitted[1]
        taskname = " ".join(splitted[2:])
                
    except:
        print "Malformed task: "+str(taskstring)
        print "Skipping" 
        return None
    
    assert project in PROJECTS
    assert project == togglProject
    return wp, taskname
    

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
    
    tasks = {}
    
    for task in data["data"]:
        assert task["task"] == project
        startTimeStamp = dateutil.parser.parse(task["start"])
        duration = toHours(task["dur"])
        wp, taskname = parseTaskString(task["description"], task["task"])
          
        if taskname not in tasks:
            tasks[taskname] = ProjectTask(wp, taskname)
        tasks[taskname].addHours(wp, duration, startTimeStamp.weekday())
        
    return tasks

def getProjectNumber(project, wp):
    if wp not in PROJECT_NUMBERS[project]:
        print "ERROR: work package "+wp+" is not available in project "+project
        sys.exit(-1)
    return str(PROJECT_NUMBERS[project][wp])

def printTasks(project, tasks, opts):
    headings = ["WP", "Maconomy Project", "Description"]+WEEKDAYS
    leftJust = [True, True, True]
    for d in WEEKDAYS:
        leftJust.append(False)
    
    totalHours = 0
    
    lines = []
    lines.append(headings)
    for t in tasks:
        assert t == tasks[t].text
        line = []
        line.append(tasks[t].wp)
        line.append(getProjectNumber(project, tasks[t].wp))
        line.append(t)
        for h in tasks[t].hours:
            totalHours += h
            line.append(numberToString(h, opts.decimals))
        lines.append(line)
        
    printData(lines, leftJust, sys.stdout, opts.decimals)
    return totalHours

if __name__ == '__main__':
    opts, project, weeknum, year = parseArgs()
    
    print
    print "Hours for Project "+project+", week "+str(weeknum)+" of year "+str(year)
    print
    
    tasks = getProjectHours(project, weeknum, year)
    totalHours = printTasks(project, tasks, opts)
    
    print
    print "Total hours logged: "+numberToString(totalHours, opts.decimals)