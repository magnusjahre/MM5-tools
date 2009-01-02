
import pbsconfig
import os
import re

finPattern = re.compile("End Simulation Statistics")
w = 40
nw = 10
simlength = 100000000
fwlength = 1000000000

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

        if res != []:
            print id.ljust(w),
            print "100%".rjust(nw),
            print "Finished".rjust(nw)
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
        print "0%".ljust(nw),
        print "Fastforwarding".rjust(nw)
    
