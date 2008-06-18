
import os
import pbsconfig
import popen2

def writeFile(benchmark, suffix, thres, ylabel, maxtick, mintick, input):
    scriptfile = open(str(benchmark)+suffix+".g", "w")
    scriptfile.write("set title \"Workload "+str(benchmark)+": IPC Profile\n")
    scriptfile.write("set xlabel \"Million Clock Cycles\"\n")
    scriptfile.write("set ylabel \""+ylabel+"\"\n")
    scriptfile.write("set xr["+str(mintick)+":"+str(maxtick)+"]\n");

    scriptfile.write("set key outside below\n")

    scriptfile.write("set terminal postscript eps color enhanced 18\n")
    scriptfile.write("set output \""+str(benchmark)+suffix+".eps\"\n")
  
    scriptfile.write("plot ")
    for i in range(np):
        if i > 0:
            scriptfile.write(", ")
        scriptfile.write("\""+input+"\" using 1:"+str(i+2)+" title \'CPU "+str(i)+"\' with lines")

    scriptfile.flush()
    scriptfile.close()

    res = popen2.popen3("gnuplot "+str(benchmark)+suffix+".g")
    text = res[0].read()

    res = popen2.popen3("epstopdf "+str(benchmark)+suffix+".eps")
    text = res[0].read()

    return str(benchmark)+suffix+".pdf"

np = 4

os.mkdir("IPCPlot")

for cmd, config in pbsconfig.commandlines:

    resID = pbsconfig.get_unique_id(config)
                            
    print "Processing experiment " + resID
    
    os.chdir(resID)    
    statsfile = None
    try:
        statsfile = open("ipcTrace.txt")
    except:
        print "File not found for experiment "+resID
    
    if statsfile != None:

        gpReadable = open("IPCPlot_gpInput.txt", 'w')
    
        first = True
        second = True
        firstDataLine = True
        mintick = -1
        maxtick = -1
            
        for line in statsfile.readlines():
            if first:
                fields = line.split(';')
                gpReadable.write(("Tick").ljust(30))
                for i in range(np):
                    gpReadable.write(("CPU"+str(i)+" IPC").ljust(30))
                first = False
            else:
                fields = line.split(';')
                gpReadable.write(fields[0].ljust(30))
                for f in fields[1:5]:
                    if not second:
                        gpReadable.write(f.strip().ljust(30))
                    else:
                        gpReadable.write("0.0".ljust(30))
                                    
                if firstDataLine:
                    mintick = int(fields[0])
                    firstDataLine = False

                if second:
                    second = False
                maxtick = int(fields[0])
            gpReadable.write("\n")
            
        gpReadable.flush()
        gpReadable.close()
    
        statsfile.close()
                            
        thresStr = pbsconfig.get_key(cmd, config)
                
        name = writeFile(config[0],                  
                         "_adaptive_"+str(thresStr),
                         thresStr,
                         "IPC",
                         maxtick+100000,
                         mintick-100000,
                         "IPCPlot_gpInput.txt")

        os.rename(name, '../IPCPlot/'+name)

    os.chdir('..')

