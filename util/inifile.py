
from statparse import stringToType


class IniFile:
    
    NO_CPU_KEY = "SYSTEM"
    
    def __init__(self, filename):
        
        self.data = {}
        
        file = open(filename)
        for line in file:
            try:
                splitted = line.split("=")
                if len(splitted) == 3:
                    key, cpuid, val = splitted
                    cpuid = int(cpuid)
                else:
                    key, val = splitted
                    cpuid = self.NO_CPU_KEY
            except:
                raise Exception("Unknown format on line: "+line)
            
            if key not in self.data:
                self.data[key]  = {}
                
            assert cpuid not in self.data[key]
            self.data[key][cpuid] = stringToType(val)
            
            
    def dump(self, width = 25):
        for k in sorted(self.data.keys()):
            print (k+": ").ljust(width),
            for id in sorted(self.data[k].keys()):
                print (str(id)+":"+str(self.data[k][id])).rjust(width),
            print
