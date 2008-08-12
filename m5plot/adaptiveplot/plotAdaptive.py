
import os
import pbsconfig
import popen2
import workloads

def writeFile(benchmark, suffix, thres, ylabel, maxtick, mintick, input):
    scriptfile = open(str(benchmark)+suffix+".g", "w")
    scriptfile.write("set title \"Workload "+str(benchmark)+": Adaptive MHA Behaviour\n")
    scriptfile.write("set xlabel \"Million Clock Cycles\"\n")
    scriptfile.write("set ylabel \""+ylabel+"\"\n")
    scriptfile.write("set xr["+str(mintick)+":"+str(maxtick)+"]\n")
    scriptfile.write("set yr[0:17]\n")

    scriptfile.write("set key outside above\n")

    scriptfile.write("set terminal postscript eps enhanced 18\n")
    scriptfile.write("set output \""+str(benchmark)+suffix+".eps\"\n")
  
    scriptfile.write("plot ")
    for i in range(np):
        if i != 0:
            scriptfile.write(", ")
        # scriptfile.write("\""+input+"\" using 1:"+str(i+2)+" title \'"+workloads.workloads[np][int(benchmark)][0][i]+"\' with lines")
        scriptfile.write("\""+input+"\" using 1:"+str(i+2)+" title \'A\' with lines")
    scriptfile.write("\n")

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
    statsfile = None
    try:
        statsfile = open("adaptiveMHATrace.txt")
    except:
        print "File not found for experiment "+resID
    
    if statsfile != None:

        gpReadable = open("adaptiveMHATrace_gpInput.txt", 'w')
    
        first = True
        firstDataLine = True
        mintick = -1
        maxtick = -1
            
        for line in statsfile.readlines():
            if first:
                fields = line.split(';')
                gpReadable.write(("Tick").ljust(30))
                for i in range(np):
                    gpReadable.write(("D-Cache "+str(i)+" MSHRs").ljust(30))

                first = False
            
            else:
                fields = line.split(';')

                gpReadable.write(fields[0].ljust(30))
                for f in fields[1:5]:
                    gpReadable.write(str(f).ljust(30))
                                    
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
                         "Resource Allocation",
                         maxtick+100000,
                         mintick-100000,
                         "adaptiveMHATrace_gpInput.txt")

        os.rename(name, '../adaptivePlot/'+name)
    
            
    os.chdir('..')

