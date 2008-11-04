
import os
import pbsconfig
import fairmha.plot as plot
import deterministic_fw_wls as workload_info

os.mkdir("latencyPlots")
os.chdir("latencyPlots")

for cmd, params in pbsconfig.commandlines:
    resID = pbsconfig.get_unique_id(params)
    print "Plotting "+resID+"..."
    filename = "../"+resID+"/memoryBusTrace.txt"
    resfile = open(filename)

    wl = pbsconfig.get_workload(params)
    bms = workload_info.getBms(wl)
    

    if resfile != None:
        plotdata = []
        for line in resfile.readlines()[1:]:
            splitted = line.split(";")
            tmp = []
            tmp.append(int(splitted[0]))
            for d in splitted[7:11]:
                tmp.append(float(d))

            plotdata.append(tmp)

        
        plot.plotGraph("Average Memory Queue Latencies",
                       "Time",
                       "Average Latency",
                       plotdata,
                       bms,
                       resID,
                       False)
