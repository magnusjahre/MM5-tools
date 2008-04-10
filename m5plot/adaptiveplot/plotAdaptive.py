
import os
import pbsconfig
import popen2

def writeFile(benchmark, suffix, thres, ylabel, maxtick, mintick, input):
    scriptfile = open(str(benchmark)+suffix+".g", "w")
    scriptfile.write("set title \"Workload "+str(benchmark)+" Memory Bus Utilization with "+str(thres)+" MSHRs\n")
    scriptfile.write("set xlabel \"Million Clock Cycles\"\n")
    scriptfile.write("set ylabel \""+ylabel+"\"\n")
    scriptfile.write("set xr["+str(mintick)+":"+str(maxtick)+"]\n");
    scriptfile.write("set yr[0:17]\n");

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

    return str(benchmark)+suffix+".pdf"

np = 4

os.mkdir("adaptivePlot")

for cmd, config in pbsconfig.commandlines:

    resID = pbsconfig.get_unique_id(config)
                            
    print "Processing experiment " + resID
    
    os.chdir(resID)
            
    statsfile = open("adaptiveMHATrace.txt")
    gpReadable = open("adaptiveMHATrace_gpInput.txt", 'w')
    
    first = True
    firstDataLine = True
    mintick = -1
    maxtick = -1
            
    for line in statsfile.readlines():
        if first:
            fields = line.split(';')
            gpReadable.write(("Tick").ljust(30)+("Avg MSHRs").ljust(30))
            first = False
            
        else:
            fields = line.split(';')
            sum = 0.0
            #print fields
            #print fields[1:5]
            for f in fields[1:5]:
                sum = sum + int(f)
                
            gpReadable.write(fields[0].ljust(30)+str(sum/4.0).ljust(30))
                                    
            if firstDataLine:
                mintick = int(fields[0])
                firstDataLine = False
                                    
            maxtick = int(fields[0])
        gpReadable.write("\n")
            
    gpReadable.flush()
    gpReadable.close()
    
    statsfile.close()
                            
    thresStr = pbsconfig.get_key(cmd, config)
                
    name = writeFile(config[0],                  
                     "_adaptive_"+str(thresStr),
                     thresStr,
                     "Number of MSHRS",
                     maxtick+100000,
                     mintick-100000,
                     "adaptiveMHATrace_gpInput.txt")

    os.rename(name, '../adaptivePlot/'+name)
    
            
    os.chdir('..')

