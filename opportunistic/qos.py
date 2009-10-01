#!/usr/bin/python

import re
import sys

reference_run = '/home/grannas/15-base/'

patternIPC = 'detailedCPU..COM:IPC.*'

strategy = sys.argv[1]
benchmarks = range(1,41)

configs = ['16-seq','16-rpt','20-cdc','17-srp', '20-dcpt']

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


count = 1

for config in configs:
    print count,
    print '\t',
    count = count + 1
    min = 20.0
    minbench = -1

    for benchmark in benchmarks:
      resID = config + '-' + strategy + '/opp_' + str(benchmark) +'_1'

      try:
        resultfile = open(resID+'.txt')
      except:
        print 'Missing: ' + resID
        continue

      if resultfile != None:
        foo = resultfile.read()
        res = patternIPC.findall(foo)


        for cpu in range(0,4):
          cpuspeedup = float(res[cpu].split()[1]) / referenceIPC[str(benchmark)+'-'+str(cpu)]
          if cpuspeedup > 10:
            print 'strange! ',
            print benchmark,
            print ' ' + str(cpu)
          if cpuspeedup < min:
            min = cpuspeedup
            minbench = benchmark

    print min,
    print '\t',
    print config,
    print '\t',
    print minbench
    
