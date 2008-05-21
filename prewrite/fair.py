#!/usr/bin/python

import re
import pbsconfig
from math import sqrt

patternIPC = 'detailedCPU..COM:IPC.*'
#patternIPC = '.*issuedprewrites.*'
#patternIPC = 'L2Bank..writebacks.*'

#patternIPC = 'ram.number_of_reads.*'

#patternIPC = 'L2Bank..issued_prefetches.*'
#patternIPC = 'L2Bank..good_prefetches.*'
np = 4

patternIPC = re.compile(patternIPC)

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

# Get reference
referenceIPC = []
for benchmark in pbsconfig.benchmarks:
  config = pbsconfig.configs[0]
  resID = pbsconfig.get_unique_id(benchmark,config)

  innerIPC = 0.0
  resultfile = open(resID+'/'+resID+'.txt')

  foo = resultfile.read()
  res = patternIPC.findall(foo)
  for string in res:
    referenceIPC.append(float(string.split()[1]))


print '#benchmark',
for config in pbsconfig.configs:
    print '\t',
    print config[0],

print ' ' 

index= 0
for benchmark in pbsconfig.benchmarks:
    print benchmark,

    config= pbsconfig.configs[46]
    resID = pbsconfig.get_unique_id(benchmark,config)

    innerIPC = 0.0
    minimum = 5000000
    maximum = -5000000
    try:
      resultfile = open(resID+'/'+resID+'.txt')
    except:
      print '-',

    if resultfile != None:
        foo = resultfile.read()
        res = patternIPC.findall(foo)

        for string in res:
          innerIPC =  float(string.split()[1])

          #print '\t',
          #print innerIPC,
          #print '\t',
          #print referenceIPC[index],


          degradation = (innerIPC - referenceIPC[index]) / referenceIPC[index] * 100.0

          if (minimum > degradation):
            minimum = degradation
       
          if (maximum < degradation):
            maximum = degradation
       
          index = index+1

     
    print '\t',
    print minimum,
    #print '\t',
    #print maximum,
    print ' '

