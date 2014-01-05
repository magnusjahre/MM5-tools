#!/usr/bin/env python

from optparse import OptionParser
from statparse.util import fatal
from statparse.util import readDataFile

from statparse.plotResults import plotBenchmarkBarChart

import optcomplete

def parseArgs():
    parser = OptionParser(usage="plotPerBenchmarkData.py [options] column_id filename")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--outfile", action="store", dest="outfile", type="string", default=None, help="Output filename (Default: plot.pdf)")
    parser.add_option("-y", "--ytitle", action="store", dest="ytitle", type="string", default="Y axis title", help="Y axis title")
    parser.add_option("-x", "--xtitle", action="store", dest="xtitle", type="string", default="X axis title", help="X axis title")
    #parser.add_option("--yrange", action="store", dest="yrange", type="string", default=None, help="Comma separated min,max pair")

    opts, args = parser.parse_args()
    
    try:
        columnID = int(args[0])
    except:
        fatal("Could not parse column ID "+str(args[0]))
    
    try:
        datafile = open(args[1])
    except:
        try:
            fatal("Cannot open file "+str(args[1]))
    #parser.add_option("--legend-columns", action="store", dest="legendColumns", type="int", default=2, help="Number of columns in legend")
    #parser.add_option("--margins", action="store", dest="margins", type="string", default="", help="Comma separated plot margins: left,right,top,bottom ")
        except:
            print parser.usage
            fatal("Command line error")
    
    return opts, args, columnID, datafile

def parseBmName(longname):
    tmp = longname.split("sp0-")
    tmpname = tmp[1].replace("s6-", "")
    if tmpname[len(tmpname)-1] == "0":
        tmpname = tmpname[:len(tmpname)-1]
    
    return tmpname

def processData(header, data, columnID):

    bmdata = {}

    for line in data:
        value = line[columnID]
        bm = parseBmName(line[0])
        
        if bm not in bmdata:
            bmdata[bm] = []
        bmdata[bm].append(value)
    
    return bmdata

def makePlotData(bmdata):
    names = bmdata.keys()
    names.sort()
    
    averages = [0.0 for i in range(len(names))]
    errors = [[0.0 for i in range(len(names))], [0.0 for i in range(len(names))]] 
    
    for i in range(len(names)):
        datalist = bmdata[names[i]]
        averages[i] = sum(datalist) / len(datalist)
        errors[0][i] = averages[i] - min(datalist) 
        errors[1][i] = max(datalist) - averages[i]
        
    return names, averages, errors
    

def main():

    opts, args, columnID, datafile = parseArgs()
    
    print "Data file plot of file "+args[0]
    print "Processing data..."
    
    header, data = readDataFile(datafile, "")
    bmdata = processData(header, data, columnID)
    names, averages, errors = makePlotData(bmdata)
    
    plotBenchmarkBarChart(names,
                          averages,
                          errors,
                          filename=opts.outfile,
                          xlabel=opts.xtitle,
                          ylabel=opts.ytitle)
    
if __name__ == '__main__':
    main()