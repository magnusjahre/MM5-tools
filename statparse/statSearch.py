
__metaclass__ = type

class StatSearch():

    def __init__(self, index, searchConfig):
        self.index = index
        self.searchConfig = searchConfig

    def plainSearch(self, regexp):
        matchingConfigs = self.index.findConfiguration(self.searchConfig)
        self.results = self.index.searchForValues(regexp, matchingConfigs)

    def printAllResults(self, width, decimalPlaces):
        statkeys = self.results.keys()
        statkeys.sort()
    
        for statkey in statkeys:
            for config in self.results[statkey]:
                print statkey.ljust(width),
                print config.toString().ljust(width),
                print self._numberToString(self.results[statkey][config], decimalPlaces).ljust(width)
                
                
    def _numberToString(self, number, decimalPlaces):
        if type(number) == type(int()):
            return str(number)
        elif type(number) == type(float()):
            return ("%."+str(decimalPlaces)+"f") % number
        else:
            raise TypeError("number is not int or float")
            