#!/usr/bin/python

import sys
import pbsconfig
import re
import os
import fairmha.plot.plot as plot

def addToDistribution(data, currentKey, line):
    splitted = line.split()
    try:
        histogramKey = int(splitted[0])
        frequency = int(splitted[1])
    except:
        print "Warning: could not parse: "+line.strip()
        return data, True
        
    
    if histogramKey not in data[currentKey]:
        data[currentKey][histogramKey] = 0
        
    data[currentKey][histogramKey] += frequency
        
    return data, False

def readDistributions(startPatterns, endPatterns, distributionNames, filename, data):
    
    file = open(filename)
    
    numPatterns = len(startPatterns)
    assert numPatterns == len(endPatterns) and numPatterns == len(distributionNames)
    
    if data == {}:
        for dn in distributionNames:
            data[dn] = {}
    
    currentTypeIndex = -1
    
    error = False
    for l in file:
        
        if currentTypeIndex == -1:    
            for i in range(numPatterns):
                searchres = startPatterns[i].findall(l)
                if searchres != []:
                    currentTypeIndex = i
        else:
            searchres = endPatterns[currentTypeIndex].findall(l)
            if searchres != []:
                currentTypeIndex = -1
            else:
                data, error = addToDistribution(data, distributionNames[currentTypeIndex], l)
    
    file.close()
    
    return data, error

def createHistograms():
    startReadName = "min_value"
    endReadName = "max_value"

    distributionNames = ["conflict_distribution_read",
                         "conflict_distribution_write",
                         "miss_distribution_read",
                         "miss_distribution_write"]
    data = {}
    startPatterns = []
    endPatterns = []
    for dn in distributionNames:
        startPatterns.append(re.compile(dn+"."+startReadName))
        endPatterns.append(re.compile(dn+"."+endReadName))
    
    cnt = 0
    for cmd,params in pbsconfig.commandlines:
        expid = pbsconfig.get_unique_id(params)
        key = pbsconfig.get_key(cmd,params)
        resfile = expid+"/"+expid+".txt"
        
        if key not in data:
            data[key] = {}
        
        data[key], error = readDistributions(startPatterns, 
                                             endPatterns,
                                             distributionNames,
                                             resfile,
                                             data[key])
        
        if error:
            print "Warning: parse error for file "+resfile

    return data

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
    
    histograms = createHistograms()

    print
    print "Parsing finished, writing result files..."
    print

    os.chdir("dram-latencies")
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
