import requests
import ast
from datetime import *
from dateutil.easter import *
from dateutil.relativedelta import *

def togglRequest(baseurl, params):
    r = requests.get(baseurl, params=params, auth=('223867917969fce808959853d3776185', 'api_token'))
    content = r.content
    content = content.replace("null", "0") #FIXME: not particularly safe, e.g. the string nullify
    data = ast.literal_eval(content)
    return data

def getWeekDayRange(year, weeknum):
    first = date(year, 1, 1)
    firstThurs = first+relativedelta(weekday=TH)
    firstMon = firstThurs+relativedelta(weekday=MO(-1))
    firstSun = firstThurs+relativedelta(weekday=SU)
    weekMon = firstMon+relativedelta(weeks=(weeknum-1))
    weekSun = firstSun+relativedelta(weeks=(weeknum-1))
    return [weekMon, weekSun]

def getRedDays(year):
    reddays = []
    reddays.append(date(year, 1, 1))
    reddays = reddays + getEasterRedDays(year)
    reddays.append(date(year, 5, 1))
    reddays.append(date(year, 12, 25))
    reddays.append(date(year, 12, 26))
    return reddays
    
def getHalfDays(year):
    halfdays = []
    easterSunday = easter(year)
    halfdays.append(easterSunday-relativedelta(days=4))    
    halfdays.append(date(year, 12, 24))
    return halfdays

def getEasterRedDays(year):
    easterSunday = easter(year)
    skjaertorsdag = easterSunday-relativedelta(days=3)
    langfredag = easterSunday-relativedelta(days=2)
    paaskedag = easterSunday+relativedelta(days=1)
    himmelfart = easterSunday+relativedelta(days=39)
    pinsedag = easterSunday+relativedelta(days=50)
    return [skjaertorsdag, langfredag, paaskedag, himmelfart, pinsedag]
