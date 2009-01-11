
import pbsconfig
import sys
import os
import re

options = sys.argv[1:]

doSingleRes = False
if "-s" in options:
    doSingleRes = True

finPattern = re.compile("End Simulation Statistics")
ticksPattern = re.compile("sim_ticks.*")
comInstPattern = re.compile(".*COM:count.*")
idPattern = re.compile("[0-9]+")

w = 50
nw = 10
simlength = 100000000
fwlength = 1000000000

print
print "Workload Simulation Progress"
print

for cmd, config in pbsconfig.commandlines:
    id = pbsconfig.get_unique_id(config)
    switchfilename = id+'/cpuSwitchInsts.txt'
    statsfilename = id+'/'+id+".txt"
    ipctracefilename = id+'/ipcTrace.txt'

    if os.path.exists(switchfilename):

        statsfile = open(statsfilename)
        text = statsfile.read()
        statsfile.close()

        res = finPattern.findall(text)
        ticksres = ticksPattern.findall(text)

        if res != []:
            assert len(ticksres) == 1
            ticks = int(ticksres[0].split()[1])
            print id.ljust(w),
            if ticks >= 0.99 * simlength:
                print "100%".rjust(nw),
                print "Finished".ljust(nw)
            else:
                print "Error!".rjust(nw)
                print "Not enough ticks".ljust(nw)
        else:

            ipcfile = open(ipctracefilename)
            lines = ipcfile.readlines()
            ipcfile.close()

            lastline = lines[len(lines)-1]
            curTick = int(lastline.split(";")[0])

            detTicks = curTick - fwlength
            progress = float(detTicks) / float(simlength)
            percProgress = int(progress*100)
            
            print id.ljust(w),
            print (str(percProgress)+"%").rjust(nw)
    else:
        print id.ljust(w),
        print "0%".rjust(nw),
        print "Fastforwarding".ljust(nw)
    

if doSingleRes:
    
    print
    print "Single CPU Status"
    print

    for cmd,params in pbsconfig.commandlines:

        id = pbsconfig.get_unique_id(params)
        statsfilename = id+'/'+id+".txt"
        wl = pbsconfig.get_workload(params)
        
        if os.path.exists(statsfilename):
            statsfile = open(statsfilename)
            stext = statsfile.read()
            statsfile.close()

            finRes = finPattern.findall(stext)
            if finRes != []:
                icounts = comInstPattern.findall(stext)
                for icount in icounts:
                    cpuid = int(idPattern.findall(icount.split()[0])[0])
                    cnt = int(icount.split()[1])
                    
                    singleParams = pbsconfig.get_alone_params(wl, cpuid, params)
                    aID = pbsconfig.get_unique_id(singleParams)
                    astatsfilename = aID+"/"+aID+".txt"

                    if os.path.exists(astatsfilename):
                        astatsfile = open(astatsfilename)
                        atext = astatsfile.read()
                        astatsfile.close()

                        aFinRes = finPattern.findall(atext)
                        if aFinRes != []:
                            
                            actualIcountRes = comInstPattern.findall(atext)
                            assert len(actualIcountRes) == 1
                            actualIcount = int(actualIcountRes[0].split()[1])
                            
                            if actualIcount >= cnt*0.99:
                                print aID.ljust(w),
                                print "100%".rjust(nw),
                                print "Finished".ljust(nw)
                            else:
                                print aID.ljust(w),
                                print "Error!".rjust(nw),
                                print "Too few instructions committed".ljust(nw)

                            continue

                    print aID.ljust(w),
                    print "?%".rjust(nw),
                    print "Running".ljust(nw)

                continue

        print id.ljust(w),
        print "".rjust(nw),
        print "Workload not finished".ljust(nw)

            
