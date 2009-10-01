#!/usr/bin/python

import re
import pbsconfig
import sys

reference_run = '/home/grannas/15-base/'

patternGood = 'L2Bank..good_prefetches.*'
patternIssued = 'L2Bank..issued_prefetches.*'
patternMiss = 'L2Bank..demand_misses.*'
patternHits = 'L2Bank..demand_hits.*'

type = sys.argv[1]
benchmarks = range(1,41)

reHits = re.compile(patternHits)
reMiss = re.compile(patternMiss)
reIssued = re.compile(patternIssued)
reGood = re.compile(patternGood)

prefetchers = ['16-seq-','16-rpt-','20-cdc-','17-srp-','20-dcpt-']

config = '1'


i = 0

for prefetcher in prefetchers:
  totalAccuracy = 0.0
  totalHitrate = 0.0
  totalCoverage = 0.0


  for benchmark in benchmarks:
    resID = prefetcher + type + '/opp_' + str(benchmark) +'_' + config[0]

    try:
      resultfile = open(resID+'.txt')
    except:
      print 'missing: ' + resID
      continue

    if resultfile != None:
      foo = resultfile.read()
      goodList = reGood.findall(foo)
      issuedList = reIssued.findall(foo)
      missList = reMiss.findall(foo)
      hitsList = reHits.findall(foo)

      for bank in range(0,4):
        issued = float(issuedList[bank].split()[1])
        good = float(goodList[bank].split()[1])
        hits = float(hitsList[bank].split()[1])
        misses = float(missList[bank].split()[1])
        accuracy = good/issued
        hitrate = hits / (hits + misses)
        coverage = good / (misses + good)
        totalAccuracy = totalAccuracy + accuracy
        totalHitrate = totalHitrate + hitrate
        totalCoverage = totalCoverage + coverage

      
  i = i + 1

  print i,
  print '\t',
  print totalAccuracy / (len(benchmarks) * 4.0),
  print '\t',
  print totalHitrate / (len(benchmarks) * 4.0),
  print '\t',
  print totalCoverage / (len(benchmarks) * 4.0),
  print '# ' + prefetcher

