#!/usr/bin/python

import sys
import pbsconfig
import re
import os
import parsemethods
import fairmha.plot.plot as plot

def writeResults(histograms):
        
    averages = {}
    
    for k in histograms:
        
        filenames = []
        figureTitles = []
        avgLats = []
        
        for latType in histograms[k]:
        
            filename = k+"-"+latType
            filenames.append(filename)
            figureTitles.append(latType)
            
            print "Plotting results for file "+filename
            
            titles = ["Percentage of Observed Requests", "Service Latency"]
            seriesheaders = ["Percentage of Observed Requests"]
            
            plotdata = []
            sortedKeys = histograms[k][latType].keys()
            sortedKeys.sort()
            
            reqsum = 0.0
            latsum = 0.0
            for e in sortedKeys:
                reqsum += float(histograms[k][latType][e])
                latsum += float(histograms[k][latType][e])*e
            
            avgLats.append( (latType, latsum / reqsum) )
            
            for e in sortedKeys:
                plotdata.append( (e, [float(histograms[k][latType][e]) / reqsum])  )
            
            plot.plotLine(plotdata,
                          filename,
                          titles,
                          seriesheaders,
                          0,
                          1.2,
                          min(sortedKeys)-10,
                          max(sortedKeys)+10)
        
        averages[k] = avgLats
        
        freetext = "Average latencies:"
        freetext += "\\begin{itemize}\n"
        for type, avg in avgLats:
            freetext += "\\item \\textit{"+str(type.replace("_","-"))+":} "+str(avg)+"\n"
        freetext += "\\end{itemize}\n"
        
        plot.createSummaryPdf(filenames,
                              k,
                              "DRAM Latency Distribution",
                              figureTitles,
                              0.45,
                              k,
                              False,
                              freetext)
    
    return averages

def mergeAndPrintHistogram(histogram):
    histkeys = histogram.keys()
    histkeys.sort()
    
    types = histogram[histkeys[0]].keys()
    types.sort()
    
    typehistograms = {}
    
    for t in types:
        assert t not in typehistograms
        typehistograms[t] = {}
        
        total = 0
        for histkey in histkeys:
            for latval in histogram[histkey][t]:
                if latval in typehistograms[t]:
                    typehistograms[t][latval] += histogram[histkey][t][latval]
                else:
                    typehistograms[t][latval] = histogram[histkey][t][latval]
                total += histogram[histkey][t][latval]
    
    for t in types:
        outfile = open(t+".dat", "w")
        
        outfile.write("Service Latency;Number of Request\n")
        
        latvals =  typehistograms[t].keys()
        latvals.sort()
        
        for latval in latvals:
            outfile.write(str(latval)+";"+str(typehistograms[t][latval])+"\n")
        
        outfile.flush()
        outfile.close()

def main(argv):

    print
    print "DRAM latency distribution parser"
    print
    print "Reading files..."
    print

    try:
        os.mkdir("dram-latencies")
    except:
        print "Output directory exists, quitting..."
        return -1

    
    distributionNames = ["conflict_distribution_read",
                         "conflict_distribution_write",
                         "miss_distribution_read",
                         "miss_distribution_write"]
    
    histograms = parsemethods.createHistograms(pbsconfig, distributionNames)

    print
    print "Parsing finished, writing result files..."
    print

    os.chdir("dram-latencies")
    
    mergeAndPrintHistogram(histograms)
    averages = writeResults(histograms)
    
    print
    print "Average latencies"
    print
    
    w = 40
    types = []
    for t,val in averages[averages.keys()[0]]:
        types.append(t)
    
    print "".ljust(w),
    for t in types:
        print t.rjust(w),
    print
    
    latsum = {}
    for t in types:
        latsum[t] = 0.0
    archs = len(averages.keys())
    
    for k in averages:
        print k.ljust(w),
        for type,avg in averages[k]:
            print ("%.2f" % avg).rjust(w),
            latsum[type] += avg
        print
    
    print
    print "Architecture-wide averages"
    print

    for t in types:
        print (t+":").ljust(w),
        print ("%.2f" % (latsum[t] / float(archs))).rjust(w)
    
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
