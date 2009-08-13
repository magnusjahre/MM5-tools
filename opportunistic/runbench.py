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

experimentname = 'opp'

header = """#!/bin/bash
#PBS -N m5sim
#PBS -lwalltime=7:00:00
#PBS -lpmem=1000MB
#PBS -m a
#PBS -q default
#PBS -j oe
"""
header = header + "#PBS -lnodes=1:ppn="+str(PPN)+"\n"
header = header + "#PBS -A "+str(PROJECT_NUM)+"\n\n"

header = header + "date\n"
header = header + "rm -rf /local/work/grannas/\n"
header = header + "mkdir /local/work/grannas/\n"
header = header + "cp " + pbsconfig.experimentpath + '/m5.opt /local/work/grannas/\n'

latest_commands = []

def commit_command(fileID, cmd, cnt, fcnt):
    
    latest_commands.append((fileID, cmd))

    if cnt == PPN-1:
        flush_commands(fcnt)
        return True
    return False


def flush_commands(fcnt):
  if latest_commands != []:
    output = open(pbsconfig.experimentpath+'/'+PBS_DIR_NAME+'/runfile'+str(fcnt)+'.pbs','w')
    output.write(header)
     
    for fileID, command in latest_commands:

        # Change directory into the output directory
        output.write('mkdir /local/work/grannas/' +fileID+'\n');
        output.write('cd /local/work/grannas/' +fileID+'\n');
    
        # Write command into pbsfile    
        output.write(command + '\n\n');
    


    output.write("wait\n")

    for fileID, command in latest_commands:
        output.write('cp /local/work/' + fileID + '/' + fileID + '.txt' + ' ' + pbsconfig.experimentpath + '\n')
        output.write('cp /local/work/' + fileID + '/stdout' + ' ' + pbsconfig.experimentpath + '/stdout.'+ fileID + '\n')

    del latest_commands[:]

    output.write('rm -rf /local/work/grannas/\n')
    output.write('date\n')
    # Finish file
    output.close()
   
    results = popen2.popen3('qsub '+pbsconfig.experimentpath+'/'+PBS_DIR_NAME+'/runfile'+str(fcnt)+'.pbs')
    print results[0].read()
    print results[2].read()
    

def get_command(benchmark,config):
    
    arguments = []
    arguments.append('-ENP=4')
    arguments.append('-EBENCHMARK='+str(benchmark))
    arguments.append('-EPROTOCOL=none')
    arguments.append('-EINTERCONNECT=crossbar')
    arguments.append('-ESTATSFILE='+pbsconfig.get_unique_id(benchmark,config)+'.txt')
    arguments.append('-EMSHRSL1D=8')
    arguments.append('-EMSHRSL1I=8')
    arguments.append('-EMSHRL1TARGETS=4')
    arguments.append('-EMSHRSL2=16')
    arguments.append('-EMSHRL2TARGETS=4')
    #arguments.append('-EISEXPERIMENT')
    arguments.append(pbsconfig.commonconfig)
    arguments.append(config[1])
  
    arguments.append('-ESIMULATETICKS='+str(pbsconfig.simticks))
    arguments.append('-EFASTFORWARDTICKS='+str(pbsconfig.fwticks))

    
    command = '/local/work/grannas/m5.opt'+' '
    for argument in arguments:
        command = command+argument+' '

    command = command+pbsconfig.configfile+" > stdout &"

    return command

count = 0
command_counter = 0
file_counter = 0

os.mkdir(pbsconfig.experimentpath+"/"+PBS_DIR_NAME)
# Copy the binary
os.system('cp ' + pbsconfig.simbinary + ' ' + pbsconfig.experimentpath)

for benchmark in pbsconfig.benchmarks:
    for config in pbsconfig.configs:
                fileID = pbsconfig.get_unique_id(benchmark,config)
            
                command = get_command(benchmark,config)
            
                incFile = commit_command(fileID, command, command_counter, file_counter)
                if incFile:
                    file_counter = file_counter + 1
                command_counter = (command_counter + 1) % PPN
                count = count + 1

flush_commands(file_counter)

print "Submitted "+str(count)+" experiments in "+str(file_counter)+" files"
