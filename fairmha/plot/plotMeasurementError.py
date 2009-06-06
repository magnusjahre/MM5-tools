#!/usr/bin/python

import sys
import pbsconfig
import fairmha.plot.plot as plot
import fairmha.interference.interferencemethods as getInterference
import os
import deterministic_fw_wls as workload_info


workload = ""
if len(sys.argv) == 2:
    
    workload = sys.argv[1]
    
    os.mkdir(workload+"-figures")
    os.chdir(workload+"-figures")

else:
    os.mkdir("estimationPlots")
    os.chdir("estimationPlots")

os.mkdir("figures")

for cmd, params in pbsconfig.commandlines:
    
    wl = pbsconfig.get_workload(params)
    
    if workload == "" or wl == workload:
    
        resID = pbsconfig.get_unique_id(params)
        sharedFiles = []
        interferenceFiles = []
        np = pbsconfig.get_np(params)
        for i in range(np):
            sharedFiles.append("../"+resID+'/CPU'+str(i)+'LatencyTrace.txt')
            interferenceFiles.append("../"+resID+'/CPU'+str(i)+'InterferenceTrace.txt')
    
        wlNum = int(wl.replace("fair", ""))
        bms = workload_info.getBms(wl, np)
        
        aloneFiles = []
        for i in range(len(bms)):
            a_params = pbsconfig.get_alone_params(wl, i, params)
            aResID = pbsconfig.get_unique_id(a_params)
            aloneFiles.append("../"+aResID+'/CPU0LatencyTrace.txt')
    
        print "Plotting results for experiment "+resID
        plotfiles = []
        for i in range(np):
            data = getInterference.getSampleErrors(sharedFiles[i], interferenceFiles[i], aloneFiles[i], False)
            plotfile = plot.plotGraph("Interference Results", 
                                      "Million Requests", 
                                      "Latency (clock cycles)", 
                                      data, 
                                      ['Shared', 'Interference', 'Estimate', 'Alone'],
                                      "figures/"+resID+"-"+wl+"-"+bms[i],
                                      False)
            
            plotfiles.append(plotfile)
    
        
        plot.createSummaryPdf(plotfiles, 
                              "Results for workload "+wl,
                              "Interference Results",
                              bms,
                              0.48,
                              resID,
                              False)
