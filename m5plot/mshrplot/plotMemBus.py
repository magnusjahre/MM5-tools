
import os
import pbsconfig
import popen2

def writeFile(benchmark, suffix, numMSHRs, ylabel, maxtick, mintick, input):
    scriptfile = open(str(benchmark)+suffix+".g", "w")
    scriptfile.write("set title \"Workload "+str(benchmark)+" Memory Bus Utilization with "+str(numMSHRs)+" MSHRs\n")
    scriptfile.write("set xlabel \"Million Clock Cycles\"\n")
    scriptfile.write("set ylabel \""+ylabel+"\"\n")
    scriptfile.write("set xr["+str(mintick)+":"+str(maxtick)+"]\n");
    scriptfile.write("set yr[0:1.2]\n");

    scriptfile.write("set key outside below\n")

    scriptfile.write("set terminal postscript eps color enhanced 18\n")
    scriptfile.write("set output \""+str(benchmark)+suffix+".eps\"\n")
  
    scriptfile.write("plot \""+input+"\" using 1:2 title \'Utilisation\' with lines \n")

    scriptfile.flush()
    scriptfile.close()

    res = popen2.popen3("gnuplot "+str(benchmark)+suffix+".g")
    text = res[0].read()

    res = popen2.popen3("epstopdf "+str(benchmark)+suffix+".eps")
    text = res[0].read()

np = 4
    
for benchmark in pbsconfig.benchmarks:
    for L1mshrCount in pbsconfig.l1mshrs:
        for L2mshrCount in pbsconfig.l2mshrs:
            for L1targets in pbsconfig.l1mshrTargets:
                for L2targets in pbsconfig.l2mshrTargets:

                    resID = pbsconfig.get_unique_id(np, benchmark, L1mshrCount, L2mshrCount, L1targets, L2targets)
                    
                    print "Processing experiment " + resID

                    os.chdir(resID)
    
                    statsfile = open("memoryBusTrace.txt")
                    gpReadable = open("memoryBusTrace_gpInput.txt", 'w')
    
                    first = True
                    firstDataLine = True
                    mintick = -1
                    maxtick = -1
    
                    for line in statsfile.readlines():
                        if first:
                            fields = line.split(';')
                            gpReadable.write((fields[0]).ljust(30)+fields[2].ljust(30))
                            first = False
                
                        else:
                            fields = line.split(';')
                            gpReadable.write(fields[0].ljust(30)+fields[2].ljust(30))
                            
                            if firstDataLine:
                                mintick = int(fields[0])
                                firstDataLine = False
                            
                            maxtick = int(fields[0])
                        gpReadable.write("\n")
    
                    gpReadable.flush()
                    gpReadable.close()
        
                    statsfile.close()
        
                    writeFile(benchmark,
                            "_"+resID,
                            str(L1mshrCount),
                            "Memory Bus Utilisation",
                            maxtick+100000,
                            mintick-100000,
                            "memoryBusTrace_gpInput.txt")
    
                    os.chdir('..')

