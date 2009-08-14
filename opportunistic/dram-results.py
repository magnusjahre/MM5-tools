#!/usr/bin/python

import re
import pbsconfig
import sys

reference_run = '/home/grannas/14-base/'

patternIPC = 'detailedCPU..COM:IPC.*'

prefetchers = sys.argv[2:]
benchmarks = range(1,41)

patternIPC = re.compile(patternIPC)

# Get reference (first on command line)
referenceIPC = {}
for benchmark in benchmarks:
  resID = 'opp_' + str(benchmark) +'_Base'

  try:
    resultfile = open(reference_run+'/'+resID+'.txt')
  except:
    print resID + " reference missing"
    continue

  foo = resultfile.read()
  res = patternIPC.findall(foo)
  try:
    for cpu in range(0,4):
      referenceIPC[str(benchmark)+'-'+str(cpu)] = float(res[cpu].split()[1])
  except:
    print resID + ' is corrupt'

for config in pbsconfig.configs:
    num = 40.0
    total = 0.0
    print config[0],
    print '\t',

    for benchmark in benchmarks:
      resID = 'opp_' + str(benchmark) +'_' + config[0]

      try:
        resultfile = open(resID+'.txt')
      except:
        #print 'Missing: ' + resID
        num = num - 1.0
        continue

      if resultfile != None:
        foo = resultfile.read()
        res = patternIPC.findall(foo)

        speedup = 0.0

        for cpu in range(0,4):
          try:
            cpuspeedup = float(res[cpu].split()[1]) / referenceIPC[str(benchmark)+'-'+str(cpu)]
            speedup = speedup + cpuspeedup
            if cpuspeedup > 10:
              print 'strange! ',
              print benchmark,
              print ' ' + str(cpu)
          except:
            #print 'foul ' + str(cpu) + ':' + str(benchmark)
            num = num - 0.25
        #print speedup

        total = total + speedup
    print total / num,
    print '\t (',
    print str(num) + ')'
    
