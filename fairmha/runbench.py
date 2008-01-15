#!/usr/bin/python
import sys
import time
import popen2
import pbsconfig
import shutil
import os
import workloads

header = """#!/bin/bash
#PBS -N m5sim
#PBS -l walltime=16:00:00
#PBS -l nodes=1:ppn=1
#PBS -m a
#PBS -q optimist
#PBS -j oe
#

"""

PROJECT_NUM = "nn4650k"

bmroot = os.getenv("BMROOT")
if bmroot == None:
    print "Envirionment variable BMROOT not set. Quitting..."
    sys.exit(-1)

def get_command(benchmark,
                uniformCachePartitioning,
                uniformBusPartitioning):
    
    arguments = []
    arguments.append('-ENP=4')
    arguments.append('-EBENCHMARK='+str(benchmark))
    arguments.append('-EPROTOCOL=none')
    arguments.append('-EINTERCONNECT=crossbar')
    arguments.append('-ESTATSFILE='+pbsconfig.get_unique_id(benchmark, uniformCachePartitioning, uniformBusPartitioning)+'.txt')
    arguments.append('-EMSHRSL1D='+str(pbsconfig.l1mshrs))
    arguments.append('-EMSHRSL1I='+str(pbsconfig.l1mshrs))
    arguments.append('-EMSHRL1TARGETS='+str(pbsconfig.l1mshrTargets))
    arguments.append('-EMSHRSL2='+str(pbsconfig.l2mshrs))
    arguments.append('-EMSHRL2TARGETS='+str(pbsconfig.l2mshrTargets))
    arguments.append('-EISEXPERIMENT')
  
    if str(benchmark).isdigit():
        arguments.append('-ESIMULATETICKS='+str(pbsconfig.simticks))
    else:
        arguments.append('-ESIMULATETICKS='+str(pbsconfig.simticks))
        arguments.append('-EFASTFORWARDTICKS='+str(pbsconfig.fwticks))

    if uniformCachePartitioning:
        arguments.append('-EUNIFORM-CACHE-PARTITIONING')
    if uniformBusPartitioning:
        arguments.append('-EUNIFORM-MEMORY-BUS-PARTITIONING')

    command = pbsconfig.simbinary+' '
    for argument in arguments:
        command = command+argument+' '

    command = command+pbsconfig.configfile

    return command

count = 0

for benchmark in pbsconfig.benchmarks:

    fileID = pbsconfig.get_unique_id(benchmark,
                                     pbsconfig.uniformCachePartitioning,
                                     pbsconfig.uniformBusPartitioning)
    pbsfilename = fileID+".pbs"
    
    command = get_command(benchmark, 
                          pbsconfig.uniformCachePartitioning,
                          pbsconfig.uniformBusPartitioning)
    
    # make experiment directory
    os.mkdir(fileID)
    print 'Created an experiment directory for '+fileID
    
    output = open(pbsconfig.experimentpath+'/'+fileID+'/'+pbsfilename,'w')
    output.write(header)
    
    # Change directory into the output directory
    output.write('cd ' + pbsconfig.experimentpath + '/'+fileID+'\n');
    
    # Write command into pbsfile    
    output.write(command + '\n');
    
    # Finish file
    output.close()
    
    count = count + 1
    
    results = popen2.popen3('qsub '+pbsconfig.experimentpath+'/'+fileID+'/'+pbsfilename)
    print results[0].readline(),

print 'Number of submitted jobs:',
print count
