
__metaclass__ = type

class StatSearch():

    def __init__(self, index, searchConfig):
        self.index = index
        self.searchConfig = searchConfig

    def plainSearch(self, regexp):
        matchingConfigs = self.index.findConfiguration(self.searchConfig)
        self.results = self.index.searchForValues(regexp, matchingConfigs)

    def printAllResults(self, decimalPlaces):
        statkeys = self.results.keys()
        statkeys.sort()
    
        outtext = [["Stats key", "Configuration", "Value"]]
        leftJustify = [True, True, False]
    
        for statkey in statkeys:
            for config in self.results[statkey]:
                line = []
                line.append(statkey)
                line.append(config.toString())
                line.append(self._numberToString(self.results[statkey][config], decimalPlaces))
                outtext.append(line) 
                
        self._print(outtext, leftJustify)
                
    def _numberToString(self, number, decimalPlaces):
        if type(number) == type(int()):
            return str(number)
        elif type(number) == type(float()):
            return ("%."+str(decimalPlaces)+"f") % number
        else:
            raise TypeError("number is not int or float")
    
    def _print(self, textarray, leftJust):
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
                    print textarray[i][j].ljust(colwidths[j]),
                else:
                    print textarray[i][j].rjust(colwidths[j]),
            print
 
        