
import os
import sys
import pbsconfig
import popen2
import workloads


np = 4

def writeFile(benchmark, suffix, thres, ylabel, maxtick, mintick, input):
    scriptfile = open(str(benchmark)+suffix+".g", "w")
    scriptfile.write("set title \"Workload "+str(benchmark)+" Processor Blocked "+str(thres)+"\n")
    scriptfile.write("set xlabel \"Clock Cycles\"\n")
    scriptfile.write("set ylabel \""+ylabel+"\"\n")
    scriptfile.write("set xr["+str(mintick)+":"+str(maxtick)+"]\n");
    scriptfile.write("set yr[0:1.2]\n");

    scriptfile.write("set key outside below\n")

    scriptfile.write("set terminal postscript eps color enhanced 18\n")
    scriptfile.write("set output \""+str(benchmark)+suffix+".eps\"\n")

    scriptfile.write("plot")
    for i in range(np-1):
        scriptfile.write("\""+input+"\" using 1:"+str(2+i)+" title \'"+workloads.workloads[np][int(benchmark)][0][i]+"\' with linespoints,")
    scriptfile.write("\""+input+"\" using 1:"+str(2+np-1)+" title \'"+workloads.workloads[np][int(benchmark)][0][np-1]+"\' with linespoints\n")

    scriptfile.flush()
    scriptfile.close()

    res = popen2.popen3("gnuplot "+str(benchmark)+suffix+".g")
    text = res[0].read()

    res = popen2.popen3("epstopdf "+str(benchmark)+suffix+".eps")
    text = res[0].read()

    return str(benchmark)+suffix+".pdf"

os.mkdir('cpuStallPlot')

for cmd, config in pbsconfig.commandlines:

    resID = pbsconfig.get_unique_id(config)
                            
    print "Processing experiment " + resID
    
    os.chdir(resID)
    
    cpufiles = []
    for i in range(np):
        cpufiles.append(open("detailedCPU"+str(i)+"BlockedTrace.txt"))
    gpReadable = open("blockedCycles_gpInput.txt", 'w')

    # Write header
    gpReadable.write(("Tick").ljust(30))
    for i in range(np):
        gpReadable.write(("CPU"+str(i)).ljust(30))
    gpReadable.write("\n")

    # "fast forward to first identical tick"
    mintick = -1
    running = True

    curLines = []
    for f in cpufiles:
        f.readline() # discard header
    for f in cpufiles:
        curLines.append(f.readline())
    
    cnt = 0
    while running:
        mintick = 10000000000
        prevtick = int(curLines[0].split(';')[0])
        index = -1
        allEq = True
        
        indexCnt = 0
        for l in curLines:
            tick = int(l.split(';')[0])
            if tick < mintick:
                mintick = tick
                index = indexCnt
            indexCnt = indexCnt + 1

            if tick != prevtick:
                allEq = False

            prevtick = tick

        if allEq:
            running = False
        else:
            assert index > -1
            curLines[index] = cpufiles[index].readline()
    
    # Write the lines that has allready been read to file and set mintick
    gpReadable.write(curLines[0].split(';')[0].ljust(30))
    mintick = int(curLines[0].split(';')[0])
    for l in curLines:
        gpReadable.write(l.split(';')[1].strip().ljust(30))
    gpReadable.write("\n")

    maxtick = -1
    
    for cpu0line in cpufiles[0]:
        lines = [cpu0line]
        for f in cpufiles[1:]:
            lines.append(f.readline())
        
        first = True
        for line in lines:
            fields = line.split(';')
            if first:
                gpReadable.write(fields[0].strip().ljust(30)+fields[1].strip().ljust(30))
                first = False
            else:
                gpReadable.write(fields[1].strip().ljust(30))
                                    
        maxtick = int(fields[0])
        gpReadable.write("\n")
            
    gpReadable.flush()
    gpReadable.close()
    
    for f in cpufiles:
        f.close()
    
    key = pbsconfig.get_key(cmd, config)
    
    name = writeFile(config[0],
                     "_"+str(key),
                     key,
                     "Blocked due to Memory Fraction",
                     maxtick+100000,
                     mintick-100000,
                     "blockedCycles_gpInput.txt")
    
    os.rename(name, '../cpuStallPlot/'+name)
    os.chdir('..')


