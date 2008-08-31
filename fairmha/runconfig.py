#!/usr/bin/python
import sys
import time
import popen2
import pbsconfig
import shutil
import os
import workloads
import time
import re

SLEEP_TIME = 15*60

PROJECT_NUM = "nn4650k"
PPN = 8
PBS_DIR_NAME = "pbsfiles"


header = """#!/bin/bash
#PBS -N m5sim
#PBS -lwalltime=6:30:00
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
    
    results = popen2.popen3('qsub '+pbsconfig.experimentpath+'/'+PBS_DIR_NAME+'/runfile'+str(fcnt)+'.pbs')
    print results[0].read()
    print results[2].read()
    

count = 0
command_counter = 0
file_counter = 0

os.mkdir(pbsconfig.experimentpath+"/"+PBS_DIR_NAME)

for commandline,param in pbsconfig.commandlines:

    fileID = pbsconfig.get_unique_id(param)
            
    incFile = commit_command(fileID, commandline, command_counter, file_counter)
    if incFile:
        file_counter = file_counter + 1
    command_counter = (command_counter + 1) % PPN
    count = count + 1

if latest_commands != []:
    flush_commands(file_counter)
    file_counter += 1
    command_counter = 0

print "Submitted "+str(count)+" experiments in "+str(file_counter)+" files"

if pbsconfig.spm_inst_commands != []:

    ticksPattern = re.compile("sim_ticks.*")
    comInstPattern = re.compile(".*COM:count.*")
    idPattern = re.compile("[0-9]+")

    print
    print "Suspending before attempting to issue single program mode experiments at "+time.strftime("%H:%M, %d. %b")
    time.sleep(SLEEP_TIME)

    while pbsconfig.spm_inst_commands != {}:
        print
        print "Checking for experiments that can be submitted at "+time.stftime("%H:%M, %d. %b")

        for cmd,params in pbsconfig.commandlines:
            resID = pbsconfig.get_unique_id(params)
            wl = pbsconfig.get_workload(params)
            filename = resID+"/"+resID+".txt"
            text = ""
            try:
                file = open(filename)
                text = file.read()
                file.close()
            except:
                pass

            if text != "" and wl in pbsconfig.spm_inst_commands:
                ticks = ticksPattern.findall(text)
                if ticks != []:
                    threshold = int(float(pbsconfig.simticks) * 0.99)
                    if int(ticks[0].split()[1]) > threshold:
                        icounts = comInstPattern.findall(text)
                        # make sure the simulator has finished printing the results
                        if len(icounts) == pbsconfig.get_np(params): 
                            print "Experiment with wl "+wl+" has finished, adding new experiments"
                            for icount in icounts:
                                id = int(idPattern.findall(icount.split()[0])[0])
                                cnt = int(icount.split()[1])
                            
                                singleParams = pbsconfig.spm_inst_commands[wl][id]
                                singleParams = pbsconfig.set_inst_count(singleParams, cnt)
                                cmd,singleParams = pbsconfig.get_command(singleParams)
                                expID = pbsconfig.get_unique_id(singleParams)

                                incFile = commit_command(expID, cmd, command_counter, file_counter)
                                if incFile:
                                    file_counter = file_counter + 1
                                command_counter = (command_counter + 1) % PPN
                                count = count + 1
                            del pbsconfig.spm_inst_commands[wl]
                        


        print "Suspending..."
        time.sleep(SLEEP_TIME)

    # all commands ready, check if we need to flush
    if latest_commands != []:
        flush_commands(file_counter)
        file_counter += 1
        command_counter = 0

    print "Finished submitting all "+str(count)+" experiments in "+str(file_counter)+" files"
    print
