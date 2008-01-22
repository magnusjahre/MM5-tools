#!/usr/bin/python
import sys
import time
import popen2
import pbsconfig
import shutil
import os
import workloads

PROJECT_NUM = "nn4650k"
PPN = 8
PBS_DIR_NAME = "pbsfiles"


header = """#!/bin/bash
#PBS -N m5sim
#PBS -lwalltime=16:00:00
#PBS -lpmem=1000MB
#PBS -m a
#PBS -q default
#PBS -j oe
"""
header = header + "#PBS -lnodes=1:ppn="+str(PPN)+"\n"
header = header + "#PBS -A "+str(PROJECT_NUM)+"\n\n"

bmroot = os.getenv("BMROOT")
if bmroot == None:
    print "Envirionment variable BMROOT not set. Quitting..."
    sys.exit(-1)
 
latest_commands = []

def commit_command(fileID, cmd, cnt, fcnt):
    
    # make experiment directory
    os.mkdir(fileID)
    print 'Created an experiment directory for '+fileID
    
    latest_commands.append((fileID, cmd))

    if cnt == PPN-1:
        flush_commands(fcnt)
        return True
    return False


def flush_commands(fcnt):

    output = open(pbsconfig.experimentpath+'/'+PBS_DIR_NAME+'/runfile'+str(fcnt)+'.pbs','w')
    output.write(header)
    
    for fileID, command in latest_commands:

        # Change directory into the output directory
        output.write('cd ' + pbsconfig.experimentpath + '/'+fileID+'\n');
    
        # Write command into pbsfile    
        output.write(command + '\n\n');
    
    del latest_commands[:]

    output.write("wait")

    # Finish file
    output.close()
    
    results = popen2.popen3('qsub '+pbsconfig.experimentpath+PBS_DIR_NAME+'/runfile'+str(fcnt)+'.pbs')
    print results[0].readline(),
    

def get_command(benchmark,
                cachePartitioning,
                memoryBus,
                l1MSHRs):
    
    arguments = []
    arguments.append('-ENP=4')
    arguments.append('-EBENCHMARK='+str(benchmark))
    arguments.append('-EPROTOCOL=none')
    arguments.append('-EINTERCONNECT=crossbar')
    arguments.append('-ESTATSFILE='+pbsconfig.get_unique_id(benchmark, cachePartitioning, memoryBus, l1MSHRs)+'.txt')
    arguments.append('-EMSHRSL1D='+str(l1MSHRs))
    arguments.append('-EMSHRSL1I='+str(pbsconfig.l1InstMshrs))
    arguments.append('-EMSHRL1TARGETS='+str(pbsconfig.l1mshrTargets))
    arguments.append('-EMSHRSL2='+str(pbsconfig.l2mshrs))
    arguments.append('-EMSHRL2TARGETS='+str(pbsconfig.l2mshrTargets))
    arguments.append('-EISEXPERIMENT')
  
    if str(benchmark).isdigit():
        arguments.append('-ESIMULATETICKS='+str(pbsconfig.simticks))
    else:
        arguments.append('-ESIMULATETICKS='+str(pbsconfig.simticks))
        arguments.append('-EFASTFORWARDTICKS='+str(pbsconfig.fwticks))

    
    arguments.append('-ECACHE-PARTITIONING='+str(cachePartitioning))

    
    arguments.append('-EMEMORY-BUS='+str(memoryBus))

    command = pbsconfig.simbinary+' '
    for argument in arguments:
        command = command+argument+' '

    command = command+pbsconfig.configfile+" &"

    return command

count = 0
command_counter = 0
file_counter = 0

os.mkdir(pbsconfig.experimentpath+"/"+PBS_DIR_NAME)

for benchmark in pbsconfig.benchmarks:
    for part in pbsconfig.cachePartitioning:
        for membus in pbsconfig.memoryBusses:
            for l1MSHRs in pbsconfig.l1DataMshrs:

                fileID = pbsconfig.get_unique_id(benchmark,
                                                 part,
                                                 membus,
                                                 l1MSHRs)
            
                command = get_command(benchmark, 
                                      part,
                                      membus,
                                      l1MSHRs)
            
                incFile = commit_command(fileID, command, command_counter, file_counter)
                if incFile:
                    file_counter = file_counter + 1
                command_counter = (command_counter + 1) % PPN
                count = count + 1

flush_commands(file_counter)

print "Submitted "+str(count)+" experiments in "+str(file_counter)+" files"
