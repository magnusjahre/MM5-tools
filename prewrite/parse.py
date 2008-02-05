import re
import pbsconfig
from math import sqrt

patternIssued = 'L2Bank..issuedprewrites.*'
patternSuccess = 'L2Bank..sucessful_prewrites.*'

np = 4

patternI = re.compile(patternIssued)
patternS = re.compile(patternSuccess)

def sumarray(tall):
    sum = 0.0
    for i in tall:
        sum = sum + i
    return sum

def stdev(tall):
    n = len(tall)
    sum = sumarray(tall)
    sum_of_squares = sumarray(map((lambda x : x*x), tall))
    return sqrt(sum_of_squares / n - (sum / n) ** 2)    

def min(tall):
    minimum = tall[0] 
    for i in tall:
        if i < minimum:
            minimum = i
    return minimum

def max(tall):
    maximum = tall[0]
    for i in tall:
        if i > maximum:
            minimum = i
    return maximum


for config in pbsconfig.configs:
    sumIssued = 0.0

    sumSuccess = 0.0
    
    array = []

    for benchmark in pbsconfig.benchmarks:
        resID = pbsconfig.get_unique_id(benchmark,config)

        innerIssued = 0.0

        innerSuccess = 0.0
 
        resultfile = open(resID+'/'+resID+'.txt')

        if resultfile != None:
            foo = resultfile.read()
            res = patternI.findall(foo)

            for string in res:
                    sumIssued = sumIssued + int(string.split()[1])
                    innerIssued = innerIssued + int(string.split()[1])

            res = patternS.findall(foo)

            for string in res:
                    sumSuccess = sumSuccess + int(string.split()[1])
                    innerSuccess = innerSuccess + int(string.split()[1])

            array.append(innerSuccess/innerIssued)

    average = sumarray(array) / len(array)
    avvik = stdev(array)

    print config[0] + '\t' + str(average) + '\t' + str(avvik) + '\t' + str(average - 1.65*avvik) 

    #print config[0] + ": average: ",
    #print sumSuccess/sumIssued,
    #print " (" + str(sumSuccess) + "/" + str(sumIssued) +")"
    #print average 
    #print avvik
    #print max(array)
    #print min(array)
    #print average + 1.96*avvik
    #print average - 1.96*avvik
    #print average - 1.65*avvik
