from statparse.processResults import findAllParams, findAllWorkloads
from deterministic_fw_wls import getBms
from statparse.tracefile import isFloat

import metrics

redPrefix   = '\033[1;31m'
greenPrefix = '\033[1;32m'
colorSuffix = '\033[1;m'

def printData(textarray, leftJust, outfile, decimals, **kwargs):
    
    if "plotFunction" in kwargs:
        plotFunction = kwargs["plotFunction"]
    else:
        plotFunction = None
        
    if "normalizeToColumn" in kwargs:        
        normalizeToColumn = kwargs["normalizeToColumn"]
    else:
        normalizeToColumn = -1
        
    if "plotParamString" in kwargs:        
        plotParamString = kwargs["plotParamString"]
    else:
        plotParamString = ""
    
    if "colorCodeOffsets" in kwargs:
        doColor = kwargs["colorCodeOffsets"]
    else:
        doColor = False
    
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
            print >> outfile, justify(colorCodeOffsets(textarray[i][j], doColor),
                                      leftJust[j],
                                      colwidths[j]),
        print >> outfile, ""
        
    if plotFunction != None:
        plotFunction(textarray, plotParamString=plotParamString)

def colorCodeOffsets(text, doColor):
    if not doColor:
        return text
    
    if not isFloat(text):
        return text
    
    floatVal = float(text)
    
    if floatVal == 0.0:
        return text
    
    if floatVal > 0.0:
        return greenPrefix+text+colorSuffix
    
    return redPrefix+text+colorSuffix
    
def justify(text, left, width):
    
    if colorSuffix not in text:
        padding = width - len(text)
    else:
        tmpText = text.replace(colorSuffix, "")
        tmpText = tmpText.replace(redPrefix, "")
        tmpText = tmpText.replace(greenPrefix, "")
        padding = width - len(tmpText)
    
    padStr = ""
    for i in range(padding):
        padStr += " "
    
    if left:
        return text+padStr
    return padStr+text

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

def paramsToString(params, valuesOnly = False):
    
    if valuesOnly:
        if len(params.keys()) != 1:
            raise Exception("Value only parameter keys only makes when there is one parameter class in the search result")
        return str(params[params.keys()[0]])
    
    sortedKeys = params.keys()
    sortedKeys.sort()
    
    retstr = ""
    isFirst = True
    for k in sortedKeys:
        if isFirst:
            isFirst = False
        else:
            retstr += "-"
        
        retstr += str(k)[0:3]+"-"+str(params[k])
        
    
    return retstr

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
                
                if data[i][j] == metrics.errorString or data[i][toColumnID] == metrics.errorString:  
                    normval = 0.0
                else:
                    try:
                        normval = (float(data[i][j]) / float(data[i][toColumnID]))-1.0
                    except:
                        raise Exception("Normalization failed on elements "+str(data[i][j])+" and "+str(data[i][toColumnID]))
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

def printResultDictionary(resultdict, decimals, outfile, titles = None, plotFunction = None):
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
    
    printData(outdata, leftjust, outfile, decimals, plotFunction=plotFunction)

    
def printWorkloadResultTable(resultdict, decimals, outfile, np, plotFunction = None):
    """ Prints the dictionary provided.
    
        Arguments:
            resultdict, dictionary: configuration -> value
            decimals, int: number of decimal points
            outfile, file: an open file to use for printing
    """
    
    if resultdict == {}:
        raise Exception("Result dicionary cannot be empty")
    
    allParams = findAllParams(resultdict.keys())
    paramlist = createSortedParamList(allParams)    
    
    outdata = []
    leftjust = [True]
    headrow = [""]
    for paramcomb in paramlist:
        headrow.append(paramsToString(paramcomb))
        leftjust.append(False)
    outdata.append(headrow)
    
    allWls = findAllWorkloads(resultdict.keys())
    allWls.sort()
    
    for wl in allWls:
        for bm in getBms(wl, np, True):
            line = [wl+"-"+bm]
            for paramcomb in paramlist:
                found = False
                value = -1
                for config in resultdict.keys():
                    if config.parameters == paramcomb and config.workload == wl and config.benchmark == bm:
                        assert not found
                        value = resultdict[config]
                        found = True
                        
                assert found
                line.append(numberToString(value, decimals))
            outdata.append(line)
    
    printData(outdata, leftjust, outfile, decimals, plotFunction=plotFunction)
