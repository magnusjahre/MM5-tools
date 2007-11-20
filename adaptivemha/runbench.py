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

bmroot = os.getenv("BMROOT")
if bmroot == None:
    print "Envirionment variable BMROOT not set. Quitting..."
    sys.exit(-1)

def get_command(np, 
                benchmark,
                coherenceProtocol,
                interconnect,
                L1mshrCount,
                L2mshrCount,
                L1targets,
                L2targets,
                adaptiveLow,
                adaptiveHigh,
                adaptiveRepeats):
    
    arguments = []
    arguments.append('-ENP='+str(np))
    arguments.append('-EBENCHMARK='+str(benchmark))
    arguments.append('-EPROTOCOL='+coherenceProtocol)
    arguments.append('-EINTERCONNECT='+interconnect)
    arguments.append('-ESTATSFILE='+pbsconfig.get_unique_id(np, benchmark, L1mshrCount, L2mshrCount, L1targets, L2targets, adaptiveLow, adaptiveHigh, adaptiveRepeats)+'.txt')
    arguments.append('-EMSHRSL1D='+str(L1mshrCount))
    arguments.append('-EMSHRSL1I='+str(L1mshrCount))
    arguments.append('-EMSHRL1TARGETS='+str(L1targets))
    arguments.append('-EMSHRSL2='+str(L2mshrCount))
    arguments.append('-EMSHRL2TARGETS='+str(L2targets))
    arguments.append('-EISEXPERIMENT')
  
    if str(benchmark).isdigit():
        arguments.append('-ESIMULATETICKS='+str(pbsconfig.simticks))
    else:
        arguments.append('-ESIMULATETICKS='+str(pbsconfig.simticks))
        arguments.append('-EFASTFORWARDTICKS='+str(pbsconfig.fwticks))

    
    arguments.append('-EUSE-ADAPTIVE-MHA')
    arguments.append('-EADAPTIVE-MHA-HIGH-THRESHOLD='+str(adaptiveHigh))
    arguments.append('-EADAPTIVE-MHA-LOW-THRESHOLD='+str(adaptiveLow))
    arguments.append('-EADAPTIVE-REPEATS='+str(adaptiveRepeats))

    command = pbsconfig.simbinary+' '
    for argument in arguments:
        command = command+argument+' '

    command = command+pbsconfig.configfile

    return command
  
def do_copy_hack(benchmark, to_file):
    
    if benchmark == 'WaterSpatial':
        from_file = bmroot+'/splash2/codes/apps/water-spatial/random.in'
    else:
        from_file = bmroot+'/splash2/codes/apps/water-nsquared/random.in'
    
    shutil.copy(from_file, to_file)
    print "Copied "+from_file+" to "+to_file
    
count = 0
for np in pbsconfig.number_of_cpus:
    for benchmark in pbsconfig.benchmarks:
        for L1mshrCount in pbsconfig.l1mshrs:
            for L2mshrCount in pbsconfig.l2mshrs:
                for L1targets in pbsconfig.l1mshrTargets:
                    for L2targets in pbsconfig.l2mshrTargets:
                        for threshold in pbsconfig.adaptiveMHAThresholds:
                            for repeats in pbsconfig.adaptiveRepeats:

                                fileID = pbsconfig.get_unique_id(np, benchmark, L1mshrCount, L2mshrCount, L1targets, L2targets, threshold[0], threshold[1], repeats)
                                pbsfilename = fileID+".pbs"
                
                                command = get_command(np, benchmark, 'none', 'crossbar', L1mshrCount, L2mshrCount, L1targets, L2targets, threshold[0], threshold[1], repeats)
                
                                # make experment directory
                                os.mkdir(fileID)
                                print 'Created an experiment directory for '+fileID
                    
                                output = open(pbsconfig.experimentpath+'/'+fileID+'/'+pbsfilename,'w')
                                output.write(header)
                
                                output.write('module load Python.2.5\n')
                    
                                # Change directory into the output directory
                                output.write('cd ' + pbsconfig.experimentpath + '/'+fileID+'\n');
                        
                                # Write command into pbsfile    
                                output.write(command + '\n');
                    
                                # Some files needs to be moved so that the benchmarks can find them
                                if benchmark == 'WaterNSquared' or benchmark == 'WaterSpatial':
                                    do_copy_hack(benchmark, pbsconfig.experimentpath+'/'+fileID)
                    
                                # Finish file
                                output.close()
                
                                count = count + 1
                    
                                results = popen2.popen3('qsub '+pbsconfig.experimentpath+'/'+fileID+'/'+pbsfilename)
                                print results[0].readline(),

print 'Number of submitted jobs:',
print count
