#!/usr/bin/env python
from statparse import printResults, metrics, isInt
from statparse.util import warn
from optcomplete import DirCompleter
from statparse.tracefile import isFloat
from statparse.plotResults import plotRawBarChart

from workloadfiles.workloads import typedWorkloadIdentifiers 

import sys
import os
import re

from optparse import OptionParser
import optcomplete
from CodeWarrior.Standard_Suite import lines

INT_MAX = 2147483648

def fatal(message):
    print
    print "ERROR: "+message
    print
    sys.exit(-1)

def parsePrintSpec(opts):
    mergeSpec = []
    if opts.printSpec != "":
        vals = opts.printSpec.split(",")
        for v in vals:
            try:
                colID = int(v)
            except:
                fatal("Print spec parse error for string "+str(opts.printSpec))
            
            mergeSpec.append( colID )
    return mergeSpec

def parseArgs():
    parser = OptionParser(usage="mergeDataFiles.py [options] FILENAME [FILENAME ...]")

    parser.add_option("--quiet", action="store_true", dest="quiet", default=False, help="Only write results to stdout")
    parser.add_option("--decimals", action="store", dest="decimals", type="int", default=2, help="Number of decimals to use when printing results")
    parser.add_option("--data-separator", action="store", dest="dataSeparator", type="string", default="\s+", help="Separator for data lines text files")
    parser.add_option("--head-separator", action="store", dest="headSeparator", type="string", default="\s\s+", help="Separator for header lines text files")
    parser.add_option("--print-spec", action="store", dest="printSpec", type="string", default="", help="A comma separated list of one-indexed column IDs include in output (e.g. 2,3,1)")
    parser.add_option("--normalize-to", action="store", dest="normalizeTo", type="int", default=-1, help="Print values relative to this column")
    parser.add_option("--print-names", action="store_true", dest="printColumnNames", default=False, help="Print the column ID to column name mapping for the provided files")
    parser.add_option("--col-prefix", action="store", dest="columnPrefix", default="", help="Prefix the columns from each file with the following prefix (Comma separated)")
    parser.add_option("--col-names", action="store", dest="columnNames", default="", help="Rename the columns to the names in this list (Comma separated)")
    parser.add_option("--row-names", action="store", dest="rowNames", default="", help="Rename the rows to the names in this list (Comma separated)")
    parser.add_option("--outfile", action="store", dest="outfile", default="", help="Print output to this file")
    parser.add_option("--average", action="store_true", dest="doAverage", default=False, help="Print the average values")
    parser.add_option("--typed-average", action="store_true", dest="doTypedAverage", default=False, help="Print the average values for each workload type")
    parser.add_option("--no-color", action="store_true", dest="noColor", default=False, help="Do not color code output")
    parser.add_option("--plot", action="store_true", dest="plot", default=False, help="Plot the results")
    parser.add_option("--invert", action="store_true", dest="invert", default=False, help="Invert the datafile")
    parser.add_option("--disable-row-sort", action="store_true", dest="disableRowSort", default=False, help="Don't sort the rows in the merged file")
    parser.add_option("--filter-pattern", action="store", dest="filterPattern", default="", help="Filter output lines with this pattern")
    parser.add_option("--plot-filename", action="store", dest="pltfilename", type="string", default="", help="Provide a filename to store the plot in a file")
    parser.add_option("--plot-legend-cols", action="store", dest="legendcols", type="int", default=3, help="Number of columns to use in the legend")

    optcomplete.autocomplete(parser, optcomplete.AllCompleter())
    opts, args = parser.parse_args()
    
    mergeSpec = parsePrintSpec(opts)
    
    if len(args) == 0:
        fatal("Commandline error\nUsage: "+parser.usage)
    
    return opts,args, mergeSpec
    
def readFiles(filenames, opts):
    
    data = []
    
    for fileID in range(len(filenames)):
        filename = filenames[fileID]
        curFile = open(filename)
        
        first = True
        fileRows = []
        numVals = 0
        
        for line in curFile:
            if first:
                head = re.split(opts.headSeparator, line.strip())
                firstLength = len(head) 
                first = False
            else:
                values = re.split(opts.dataSeparator, line.strip())
                if numVals != 0:
                    if len(values) != numVals:
                        if not opts.quiet:
                            warn("Cannot parse line: "+str(line.strip()))
                        continue
                numVals = len(values)
                
                fileRows.append(values)
                
        if not (firstLength == numVals or firstLength == numVals-1):
            fatal("Unknown header format in file "+filename+", possibly a parse error") 
        
        if opts.columnPrefix != "":
            try:
                prefix = opts.columnPrefix.split(",")[fileID]
            except:
                fatal("Column prefix parse error in string"+opts.columnPrefix)
            
            for i in range(len(head)):
                head[i] = prefix+head[i]
        
        data.append( (head, fileRows, numVals, filename) )
    
    return data

def mergeData(fileData, opts): 
    
    totalHeaders = [""]
    mergedData = {}
    columnToFileList = []
    
    maxVals = 0
    for headers, values, numVals, filename in fileData:
        maxVals += numVals-1
         
        if len(headers) == numVals:
            headers = headers[1:]
        
        for h in headers:
            totalHeaders.append(h)
            columnToFileList.append(filename)
        
        lineOrder = []
        for v in values:
            assert len(v) == numVals
            
            wltypes = "hmls"
            match = re.search("fair[0-9][0-9]", v[0])
            
            if match == None:
                match = re.search("[0-9]+-t-["+wltypes+"]-[0-9]+", v[0])
            
            if match == None:
                match = re.search("t-["+wltypes+"]-[0-9]*-[0-9].*\S", v[0])       
            
            if match != None:
                wl = match.group()
                wlsections = wl.split("-")
                if len(wlsections) == 4:
                    wlnum = int(wlsections[3])
                    wlnumstr = str(wlnum)
                    if wlnum < 10:
                        wlnumstr = "0"+str(wlnum)
                    wl = "-".join(wlsections[0:3])+"-"+wlnumstr
            else:
                wl = v[0]
            
            #Since simpoints are not used we don't need it in the output
            #TODO: Should be fixed in a cleaner way
            sp = False
#             spmatch = re.search("sp[0-9]", v[0])
#             if spmatch != None:
#                 sp = spmatch.group()
#             else:
#                 sp = False
            
            linekey = wl
            lineOrder.append(linekey)
            if sp:
                linekey = wl+"-"+sp
            
            if linekey not in mergedData:
                mergedData[linekey] = []
                
            for val in v[1:]:
                mergedData[linekey].append(val)
    
    wls = mergedData.keys()
    wls.sort()
    if opts.disableRowSort:
        sortedLineOrder = sorted(lineOrder)
        assert sortedLineOrder == wls
        wls = lineOrder
            
    mergedMatrix = []
    mergedMatrix.append(totalHeaders)
    
    for wl in wls:
        if len(mergedData[wl]) == maxVals:
            line = [wl]
            for v in mergedData[wl]:
                line.append(v)
                
            mergedMatrix.append(line) 
    
    return mergedMatrix, columnToFileList

def renameColumns(mergedData, opts):
    if opts.columnNames != "":
        newheader = opts.columnNames.split(",")
        newheader.insert(0, "")

        if len(newheader) != len(mergedData[0]):
            fatal("New header must be the same length as the old header")
            
        for i in range(len(newheader))[1:]:
            print "Renaming column "+mergedData[0][i]+" to "+newheader[i]
        mergedData[0] = newheader
        
def renameRows(mergedData, opts):
    if opts.rowNames != "":
        newrownames = opts.rowNames.split(",")
        newrownames.insert(0, "")
        
        if len(newrownames) != len(mergedData):
            fatal("New row header must be the same length as the old row header")
        for i in range(len(mergedData)):
            if i != 0:
                print "Renaming row "+mergedData[i][0]+" to "+newrownames[i]
            mergedData[i][0] = newrownames[i]

def filterData(mergedData, opts):
    if opts.filterPattern == "":
        return mergedData
    
    header = mergedData[0]
    newdata = {}
    for i in range(len(mergedData))[1:]:
        if re.search(opts.filterPattern, mergedData[i][0]):
            thisKey = mergedData[i][0] 
            if isInt(thisKey):
                thisKey = int(thisKey)
            
            newdata[thisKey] = mergedData[i]
    
    newdatakeys = sorted(newdata.keys())
    
    printData = []
    printData.append(header)
    for k in newdatakeys:
        printData.append(newdata[k])
    
    return printData

def processData(mergedData, mergeSpec, opts):
    
    if mergeSpec != []:
        newData = []
        for line in mergedData:
            newLine = [line[0]]
            for cID in mergeSpec:
                newLine.append(line[cID])
            newData.append(newLine)
        mergedData = newData
    
    if opts.normalizeTo != -1:
        normalizedData = {}
        for i in range(1, len(mergedData)):
            normalizedData[i] = {}
            for j in range(1, len(mergedData[i])):
                
                if mergedData[i][j] == metrics.errorString or mergedData[i][opts.normalizeTo] == metrics.errorString:
                    normalizedData[i][j] = metrics.errorString
                else:
                    if float(mergedData[i][opts.normalizeTo]) == 0.0:
                        normalizedData[i][j] = "inf"                
                    else:    
                        try:
                            relVal = (float(mergedData[i][j]) / float(mergedData[i][opts.normalizeTo])) 
                        except:
                            fatal("Normalization failed on line "+str(i)+", column "+str(j)+", trying to normalize to column "+str(opts.normalizeTo))
                
                        normalizedData[i][j] = printResults.numberToString(relVal, opts.decimals)
        
        for i in normalizedData:
            for j in normalizedData[i]:
                mergedData[i][j] = normalizedData[i][j]
    
    renameColumns(mergedData, opts)
    renameRows(mergedData, opts)
    
    mergedData = filterData(mergedData, opts)
    
    if opts.invert:
        mergedData = [[mergedData[j][i] for j in range(len(mergedData))] for i in range(len(mergedData[0]))]
    
    justify = [False for i in range(len(mergedData[0]))]
    justify[0] = True
    return mergedData, justify

def printNames(mergedData, columnToFileList):
    
    if len(mergedData) < 1:
        fatal("Merged data is empty, cannot retrieve headers")
    
    headerRow = mergedData[0]
    
    print
    print "Column ID to column name mapping"
    print
    
    idWidth = 7
    dataWidth = 45
    
    print "ColID".ljust(idWidth),
    print "Column name".ljust(dataWidth),
    print "Filename".ljust(dataWidth)
    
    id = 1
    for name in headerRow[1:]:
        print str(id).ljust(idWidth),
        print name.ljust(dataWidth),
        print columnToFileList[id-1].ljust(dataWidth)
        id += 1

def computeAverage(processedData, justify, opts):
    header = processedData.pop(0)[1:]
    datalen = len(header)
    values = [0 for i in range(datalen)]
    lines = 0.0

    for l in processedData:
        for i in range(datalen):
            try:
                values[i] += float(l[i+1])
            except:
                warn("Cannot convert to float, dropping line "+str(l))
                break
        lines += 1

    resData = []
    resData.append(header)
    averages = [v / lines for v in values]
    averageStrs = [printResults.numberToString(a, opts.decimals) for a in averages]
    resData.append(averageStrs)

    return resData, justify[1:]

def computeTypedAverage(processedData, justify, opts):
    
    resData = [processedData.pop(0)]
    datalen = len(processedData[0])-1

    for t in typedWorkloadIdentifiers:
        typedData = [0.0 for i in range(datalen)]
        lines = 0.0
        for l in processedData:
            if re.search("-"+t+"-", l[0]):
                for i in range(datalen):
                    try:
                        typedData[i] += float(l[i+1])
                    except:
                        warn("Cannot convert to float, dropping line "+str(l))
                        break
                lines += 1
                
        averages = [v / lines for v in typedData]
        dataline = [t]
        for a in averages:
            dataline.append(printResults.numberToString(a, opts.decimals))
        resData.append(dataline)

    return resData, justify

def makeFileData(data, columnToFileList):
    filedata = []
    header = [""]
    fileIndex = {}
    for c in columnToFileList[1:]:
        if c not in header:
            fileIndex[c] = len(header)
            header.append(c)
    filedata.append(header)

    legend = []
    for d in data[0][1:]:
        if d not in legend:
            legend.append(d)
    
    for l in legend:
        line = [0.0 for i in range(len(header))]
        line[0] = l
        for i in range(len(data[1]))[1:]:
            if data[0][i] == l:
                pos = fileIndex[columnToFileList[i]]
                assert line[pos] == 0.0
                line[pos] = float(data[1][i])
        
        filedata.append(line)
    
    return filedata
    

def plotData(processedData, columnToFileList, opts, filecnt):
    
    if opts.doAverage:
        processedData = makeFileData(processedData, columnToFileList)
        
    legend = processedData[0][1:]
    bms = []
    datavals = []
    for i in range(1, len(processedData)):
        curdata = []
        for j in range(len(processedData[i])):
            if j == 0:
                bms.append(processedData[i][j])
            else:
                curdata.append(float(processedData[i][j]))
        datavals.append(curdata)            
    
    plotRawBarChart(datavals, xticklabels=bms, legend=legend, filename=opts.pltfilename, legendcols=opts.legendcols)

def main():

    opts,args, printSpec = parseArgs()
    
    for filename in args:
        if not os.path.exists(filename):
            fatal("File "+filename+" does not exist!")
    
    filecnt = len(args)
    fileData = readFiles(args, opts)
    mergedData, columnToFileList = mergeData(fileData, opts)
    
    if opts.printColumnNames:
        printNames(mergedData, columnToFileList)
        return
    
    if opts.normalizeTo != -1 and not opts.noColor:
        doColor = True
    else:
        doColor = False
    
    processedData, justify = processData(mergedData, printSpec, opts)
    if opts.doAverage:
        processedData, justify = computeAverage(processedData, justify, opts)
    if opts.doTypedAverage:
        processedData, justify = computeTypedAverage(processedData, justify, opts)
    
    if opts.outfile == "":
        outfile = sys.stdout
    else:
        outfile = open(opts.outfile, "w")
    
    printResults.printData(processedData, justify, outfile, opts.decimals, colorCodeOffsets=doColor)
    

    if opts.plot:
        plotData(processedData, columnToFileList, opts, filecnt)
        

if __name__ == '__main__':
    main()
