
from statparse import stringToType


class IniFile:
    
    def __init__(self, filename):
        
        self.data = {}
        
        file = open(filename)
        for line in file:
            try:
                key, cpuid, val = line.split("=")
                cpuid = int(cpuid)
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
