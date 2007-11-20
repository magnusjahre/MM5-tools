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

splash2Benchmarks = ['Cholesky', 'Barnes', 'FFT', 'OceanContig', 'LUContig', 'LUNoncontig',  'OceanNoncontig', 'WaterNSquared', 'WaterSpatial',  'FMM', 'Raytrace',  'Radix']

rootdir = os.getenv("DIPPROOT")
if rootdir == None:
    print "Envirionment variable DIPPROOT not set. Quitting..."
    sys.exit(-1)

def get_command(np, benchmark, coherenceProtocol, interconnect):
    arguments = []
    arguments.append('-ENP='+str(np))
    arguments.append('-EBENCHMARK='+str(benchmark))
    arguments.append('-EPROTOCOL='+coherenceProtocol)
    arguments.append('-EINTERCONNECT='+interconnect)
    arguments.append('-ESTATSFILE='+pbsconfig.get_unique_id(np, benchmark, coherenceProtocol, interconnect)+'.txt')
  
    if str(benchmark).isdigit():
        arguments.append('-ESIMULATETICKS='+str(pbsconfig.simticks))
    elif str(benchmark) in splash2Benchmarks:
        arguments.append('-ESIMINSTS='+str(pbsconfig.siminsts))
        arguments.append('-EDUMPCCSTATS=250000')
    else:
        arguments.append('-ESIMULATETICKS='+str(pbsconfig.simticks))
        arguments.append('-EFASTFORWARDTICKS='+str(pbsconfig.fwticks))

    arguments.append('-EISEXPERIMENT')

    command = pbsconfig.simbinary+' '
    for argument in arguments:
        command = command+argument+' '

    command = command+pbsconfig.configfile

    return command
  
def do_copy_hack(benchmark, to_file):
    
    if benchmark == 'WaterSpatial':
        from_file = rootdir+'/experiments/benchmarks/splash2/codes/apps/water-spatial/random.in'
    else:
        from_file = rootdir+'/experiments/benchmarks/splash2/codes/apps/water-nsquared/random.in'
    
    shutil.copy(from_file, to_file)
    print "Copied "+from_file+" to "+to_file
    
count = 0
for np in pbsconfig.number_of_cpus:
    for benchmark in pbsconfig.benchmarks:
        for protocol in pbsconfig.protocols:
            for interconnect in pbsconfig.interconnects:
                  
                fileID = pbsconfig.get_unique_id(np, benchmark, protocol, interconnect)
                pbsfilename = fileID+".pbs"

                command = get_command(np, benchmark, protocol, interconnect)

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
