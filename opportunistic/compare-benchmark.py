#!/usr/bin/python

import re
#import pbsconfig
from math import sqrt
import sys


workloads = {1:(['ammp', 'mgrid', 'perlbmk', 'parser'],[1041955945, 1047775879, 1025548197, 1008908800]),
2:(['lucas', 'gcc', 'mcf', 'twolf'],[1026388815, 1050246990, 1046272284, 1056602690]),
3:(['eon', 'eon', 'mesa', 'facerec'],[1085828439, 1085086202, 1098261402, 1004267962]),
4:(['vortex1', 'ammp', 'equake', 'galgel'],[1027564658, 1014658355, 1009037399, 1039572509]),
5:(['gcc', 'galgel', 'apsi', 'crafty'],[1029306590, 1091516994, 1016968254, 1091181775]),
6:(['applu', 'equake', 'art', 'facerec'],[1001909990, 1013915170, 1046887563, 1056979138]),
7:(['applu', 'gap', 'gcc', 'parser'],[1082162802, 1059139806, 1013409002, 1085694384]),
8:(['gap', 'swim', 'twolf', 'mesa'],[1042656444, 1061963955, 1085903965, 1036190567]),
9:(['sixtrack', 'fma3d', 'apsi', 'vortex1'],[1074480257, 1031183064, 1098143364, 1012919523]),
10:(['ammp', 'bzip', 'equake', 'parser'],[1077398959, 1003951563, 1072415593, 1053509179]),
11:(['vpr', 'twolf', 'applu', 'eon'],[1040680776, 1031568211, 1082293995, 1041436570]),
12:(['galgel', 'crafty', 'mgrid', 'swim'],[1031527863, 1044545857, 1082173250, 1096751917]),
13:(['twolf', 'fma3d', 'galgel', 'vpr'],[1062306790, 1060828350, 1098129008, 1043023932]),
14:(['bzip', 'vpr', 'bzip', 'equake'],[1084019868, 1038244774, 1003412847, 1097472955]),
15:(['galgel', 'crafty', 'vpr', 'swim'],[1070880481, 1027287316, 1060235344, 1058807655]),
16:(['mcf', 'wupwise', 'mesa', 'mesa'],[1054249832, 1006759950, 1014557494, 1030953598]),
17:(['applu', 'parser', 'apsi', 'perlbmk'],[1075021039, 1053158322, 1034718910, 1026856922]),
18:(['mgrid', 'perlbmk', 'gzip', 'mgrid'],[1049328406, 1079074439, 1096282781, 1079036253]),
19:(['mcf', 'sixtrack', 'gcc', 'apsi'],[1090116441, 1068921998, 1066705590, 1092093538]),
20:(['ammp', 'gcc', 'art', 'mesa'],[1011080402, 1007932868, 1079537464, 1095718719]),
21:(['perlbmk', 'apsi', 'lucas', 'equake'],[1051169802, 1057285545, 1064666557, 1019744818]),
22:(['vpr', 'crafty', 'vpr', 'mcf'],[1073177627, 1082019945, 1021734200, 1066267018]),
23:(['gzip', 'equake', 'mgrid', 'mesa'],[1097569789, 1080949028, 1056929996, 1079797826]),
24:(['facerec', 'applu', 'fma3d', 'lucas'],[1013937124, 1035387836, 1051243465, 1041436071]),
25:(['gap', 'applu', 'parser', 'facerec'],[1008180602, 1067057433, 1083231912, 1080419219]),
26:(['mcf', 'apsi', 'twolf', 'ammp'],[1014292526, 1058328743, 1061373130, 1050686626]),
27:(['swim', 'sixtrack', 'ammp', 'applu'],[1052228680, 1059328443, 1080039777, 1026620495]),
28:(['art', 'fma3d', 'swim', 'parser'],[1082308602, 1095181635, 1012762841, 1035776155]),
29:(['apsi', 'gcc', 'vortex1', 'twolf'],[1050080000, 1076827259, 1024773007, 1088514951]),
30:(['mgrid', 'gzip', 'apsi', 'equake'],[1015952145, 1024722623, 1059266770, 1077591627]),
31:(['mgrid', 'equake', 'vpr', 'eon'],[1015263556, 1063692577, 1044670814, 1092770749]),
32:(['wupwise', 'gap', 'twolf', 'facerec'],[1073842062, 1077919529, 1009246189, 1048001712]),
33:(['galgel', 'equake', 'lucas', 'gzip'],[1040375492, 1037630973, 1017422599, 1094439053]),
34:(['facerec', 'gcc', 'facerec', 'apsi'],[1085839746, 1069300438, 1073285869, 1062627766]),
35:(['mesa', 'mcf', 'swim', 'sixtrack'],[1094695081, 1092502223, 1029829307, 1052267670]),
36:(['mesa', 'sixtrack', 'equake', 'bzip'],[1063594040, 1062127033, 1040041781, 1060015597]),
37:(['mcf', 'gap', 'gcc', 'vortex1'],[1033902102, 1001090684, 1030020762, 1048547872]),
38:(['facerec', 'lucas', 'mcf', 'parser'],[1092600483, 1066508342, 1027466999, 1060969516]),
39:(['twolf', 'eon', 'mesa', 'eon'],[1098504941, 1088612335, 1009372945, 1069289808]),
40:(['apsi', 'apsi', 'mcf', 'equake'],[1092680129, 1068726226, 1098316344, 1073035913])
}

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
            maximum = i
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

speedupprogram = {}
for benchmark in benchmarks:
    programs = workloads[benchmark][0]
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
                if programs[cpu] not in speedupprogram:
                  speedupprogram[programs[cpu]] = [speedup]
                else:
                  speedupprogram[programs[cpu]].append(speedup)
              except:
                print '--',
              print ' /',

        print '\t',
        index = index +1
    print ' '


for key in speedupprogram:
  print key,
  print '\t',
  print sumarray(speedupprogram[key])/len(speedupprogram[key]),
  print '\t',
  print max(speedupprogram[key]),
  print '\t',
  print min(speedupprogram[key])
