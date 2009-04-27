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
    innerIPC = innerIPC + float(string.split()[1])
  referenceIPC.append(innerIPC)


print '#benchmark',
for config in pbsconfig.configs:
    print '\t',
    print config[0],

print ' ' 

L = [0.0] * len(pbsconfig.configs)

bm = -1

for benchmark in pbsconfig.benchmarks:
    print benchmark,
    sumIPC = 0.0
    index= 0
    bm = bm + 1

    array = []

    for config in pbsconfig.configs:
        resID = pbsconfig.get_unique_id(benchmark,config)

        innerIPC = 0.0
        try:
          resultfile = open(resID+'/'+resID+'.txt')
        except:
          print '-',

        if resultfile != None:
            foo = resultfile.read()
            res = patternIPC.findall(foo)

            try: 
              for string in res:
                    innerIPC = innerIPC + float(string.split()[1])
            except:
              innerIPC = -1.0

            array.append(innerIPC)

        innerIPC = (innerIPC - referenceIPC[bm])/referenceIPC[bm] * 100.0
         
        print '\t',
        print innerIPC,
        L[index] = L[index] + innerIPC
        index = index +1
    print ' '

print "41,",
index = 0
for config in pbsconfig.configs:
  print L[index] / len(pbsconfig.benchmarks),
  print "\t",
  index = index + 1
  
