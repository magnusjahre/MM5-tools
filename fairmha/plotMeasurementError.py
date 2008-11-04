
import pbsconfig
import fairmha.plot as plot
import getInterference
import os
import deterministic_fw_wls as workload_info


# filename = plot.plotGraph("test", "x", "y", [[1,1,2,3], [2, 2, 3, 4]], ['a','b','c'], "morradi"+str(i), False)
# plot.createSummaryPdf(graphs, "Doc Title", "Figure", ["a","b","c","d"], 0.48, "sweet")

os.mkdir("estimationPlots")
os.chdir("estimationPlots")
os.mkdir("figures")

for cmd, params in pbsconfig.commandlines:
    
    resID = pbsconfig.get_unique_id(params)
    sharedFiles = []
    np = pbsconfig.get_np(params)
    wl = pbsconfig.get_workload(params)
    for i in range(np):
        sharedFiles.append("../"+resID+'/CPU'+str(i)+'InterferenceTrace.txt')

    wlNum = int(wl.replace("fair", ""))
    bms = pbsconfig.get_bm_names(workload_info.workloads[wlNum], np)
    
    aloneFiles = []
    for i in range(len(bms)):
        a_params = pbsconfig.get_alone_params(wl, i, params)
        aResID = pbsconfig.get_unique_id(a_params)
        aloneFiles.append("../"+aResID+'/CPU0InterferenceTrace.txt')

    print "Plotting results for experiment "+resID
    plotfiles = []
    for i in range(np):
        data = getInterference.getSampleErrors(sharedFiles[i], aloneFiles[i], False)
        plotfile = plot.plotGraph("Interference Results", 
                                  "Number of Samples", 
                                  "Average Memory Latency", 
                                  data, 
                                  ['Estimated SPB','Actual SPB'], 
                                  "figures/"+wl+"_"+bms[i],
                                  False)
        
        plotfiles.append(plotfile)

    
    plot.createSummaryPdf(plotfiles, 
                          "Results for workload "+wl,
                          "Interference Results",
                          bms,
                          0.48,
                          resID,
                          False)
