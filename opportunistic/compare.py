#!/usr/bin/python

import re
#import pbsconfig
from math import sqrt
import sys

patternIPC = 'detailedCPU..COM:IPC.*'
#patternIPC = '.*issuedprewrites.*'
#patternIPC = 'L2Bank..writebacks.*'

#patternIPC = 'ram.number_of_reads.*'

#patternIPC = 'L2Bank..issued_prefetches.*'
#patternIPC = 'L2Bank..good_prefetches.*'
np = 4

prefetchers = sys.argv[2:]
benchmarks = range(1,41)

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

# Get reference (first on command line)
referenceIPC = {}
for benchmark in benchmarks:
  resID = 'opportunistic_' + str(benchmark) +'_FR-FCFS' 

  resultfile = open(sys.argv[1] + '/' + resID+'/'+resID+'.txt')

  foo = resultfile.read()
  res = patternIPC.findall(foo)
  sum = 0.0
  for cpu in range(0,np):
    referenceIPC[str(benchmark)+'-'+str(cpu)] = float(res[cpu].split()[1])
    sum = sum + float(res[cpu].split()[1])
  referenceIPC[str(benchmark)+'-sum'] = sum

if len(referenceIPC) != (np + 1) * len(benchmarks):
  print 'Error in key generation!'
  sys.exit()


  
print '#benchmarks',
for config in prefetchers:
    print '\t',
    print config,

print ' ' 

for benchmark in benchmarks:
    print benchmark,
    index= 0

    for config in prefetchers:
        resID = 'opportunistic_' + str(benchmark) +'_FR-FCFS'

        try:
          resultfile = open(config + '/' + resID+'/'+resID+'.txt')
        except:
          print 'Not found \t',
          continue

        if resultfile != None:
            foo = resultfile.read()
            res = patternIPC.findall(foo)

            for cpu in range(0,np):
              try:
                speedup = float(res[cpu].split()[1]) / referenceIPC[str(benchmark)+'-'+str(cpu)] 
                print speedup,
              except:
                print '--',
              print ' /',

        print '\t',
        index = index +1
    print ' '
