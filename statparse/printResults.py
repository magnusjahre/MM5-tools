
def printData(textarray, leftJust, outfile):
    if textarray == []:
        raise ValueError("array cannot be empty")
    if textarray[0] == []:
        raise ValueError("array cannot be empty")
    if len(textarray[0]) != len(leftJust):
        raise ValueError("justification array must be the same with as the rows")
    
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
            
    printData(outtext, leftJustify, outfile)