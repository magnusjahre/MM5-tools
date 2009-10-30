
import plotResults

def printData(textarray, leftJust, outfile, decimals, doPlot = False, normalizeToColumn = -1):
    if textarray == []:
        raise ValueError("array cannot be empty")
    if textarray[0] == []:
        raise ValueError("array cannot be empty")
    if len(textarray[0]) != len(leftJust):
        raise ValueError("justification array must be the same with as the rows")
    
    if normalizeToColumn != -1:
        textarray = normalize(textarray, normalizeToColumn, decimals)
    
    padding = 2
    
    colwidths = [0 for i in range(len(textarray[0]))]
    
    for i in range(len(textarray)):
        for j in range(len(textarray[i])):
            if type(textarray[i][j]) != type(str()):
                raise TypeError("all printed elements must be strings")
            
            if len(textarray[i][j]) + padding > colwidths[j]:
                colwidths[j] = len(textarray[i][j]) + padding
    
    
    for i in range(len(textarray)):
        for j in range(len(textarray[i])):
            if leftJust[j]:
                print >> outfile, textarray[i][j].ljust(colwidths[j]),
            else:
                print >> outfile, textarray[i][j].rjust(colwidths[j]),
        print >> outfile, ""
        
    if doPlot:
        plotResults.plotBarChart(textarray)

def numberToString(number, decimalPlaces):
    if type(number) == type(int()):
        return str(number)
    elif type(number) == type(float()):
        return ("%."+str(decimalPlaces)+"f") % number
    elif type(number) == type(dict()):
        return "Distribution"
    elif type(number) == type(str()):
        return number
    
    raise TypeError("number is not int or float")

def normalize(data, toColumnID, decimals):
    
    newdata = []
    newdata.append(data[0])
    
    for i in range(len(data))[1:]:
        for j in range(len(data[i])):
            if j == 0:
                newdata.append([data[i][j]])
            else:
                if toColumnID >= len(data[i]):
                    raise Exception("Column ID does not exist, must be in the range from 1 to "+str(len(data[i])-1))
                
                try:
                    normval = (float(data[i][j]) / float(data[i][toColumnID]))-1.0
                except:
                    raise Exception("Normalization failed on elements "+str(data[i][j])+" and "+str(float(data[i][toColumnID])))
                newdata[i].append(numberToString(normval, decimals))

    return newdata

def createSortedParamList(allParams):
    
    if allParams == [{}]:
        return allParams
    
    paramVals = {}
    
    for params in allParams:
        for p in params:
            if p not in paramVals:
                paramVals[p] = []
                
            if params[p] not in paramVals[p]:
                paramVals[p].append(params[p])
                
    numCombs = 1
    lengths = {}
    for p in paramVals:
        paramVals[p].sort()
        numCombs *= len(paramVals[p])
        lengths[p] = len(paramVals[p])
    
    sortedKeys = paramVals.keys()
    sortedKeys.sort()
    
    periods = [numCombs / lengths[sortedKeys[0]]]
    for i in range(len(sortedKeys))[1:]:
        periods.append(periods[i-1]/lengths[sortedKeys[i]])
    
    sortedParamVals = []
    for i in range(numCombs):
        params = {}
        for j in range(len(sortedKeys)):
            pos = i / periods[j] % lengths[sortedKeys[j]]
            params[sortedKeys[j]] = paramVals[sortedKeys[j]][pos]
        sortedParamVals.append(params)
            
    return sortedParamVals

def simplePrint(results, decimalPlaces, outfile):
    statkeys = results.keys()
    statkeys.sort()

    outtext = [["Stats key", "Configuration", "Value"]]
    leftJustify = [True, True, False]

    for statkey in statkeys:
        for config in results[statkey]:
            line = []
            line.append(statkey)
            line.append(str(config))
            line.append(numberToString(results[statkey][config], decimalPlaces))
            outtext.append(line) 
            
    printData(outtext, leftJustify, outfile, decimalPlaces)
    
def printResultDictionary(resultdict, decimals, outfile, titles = None):
    """ Prints the dictionary provided. If titles are provided, they are used 
        instead of the header in resultdict
    
        Arguments:
            resultdict, dictionary: configuration -> result header -> value
            decimals, int: number of decimal points
            outfile, file: an open file to use for printing
            titles, dictionary: result header -> title (result header MUST match a key in resultdict)
    """
    
    if resultdict == {}:
        raise Exception("Result dicionary cannot be empty")
    
    configNameDict = {}
    for config in resultdict:
        configNameDict[str(config)] = resultdict[config]
        
    confignames = configNameDict.keys()
    confignames.sort()
    
    headers = configNameDict[confignames[0]].keys()
    headers.sort()

    outdata = []
    leftjust = [True]
    headrow = [""]
    for h in headers:
        if titles != None:
            if h not in titles:
                raise Exception("result header key "+str(h)+" does not match any key in titles")
            
            title = str(titles[h])
        else:
            title = str(h) 
        headrow.append(title)
        leftjust.append(False)
    outdata.append(headrow)
    
    for config in confignames:
        line = [config]
        for h in headers:
            line.append(numberToString(configNameDict[config][h], decimals))
        outdata.append(line)
    
    printData(outdata, leftjust, outfile, decimals)
