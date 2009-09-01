
__metaclass__ = type

class IniFileSection():

    def __init__(self):
        self.name = ""
        self.dataElements = {}
        self.children = {}
    
    def setName(self, name):
        self.name = name
        
    def addDataElement(self, elementName, value):
        if elementName in self.dataElements:
            print elementName+" exists in "+self.name
        assert elementName not in self.dataElements
        self.dataElements[elementName] = value
        
    def addChild(self, child):
        assert child.name not in self.children
        self.children[child.name] = child
        
    def dump(self):
        print "Section "+self.name
        for name in self.dataElements:
            print name+"="+self.dataElements[name]
        
        if self.children != []:
            print "Children:"
            for child in self.children:
                print "-- "+child.name
    
    def isEmpty(self):
        if self.dataElements != {}:
            return False
        
        if self.children !=  {}:
            return False
        
        return True
    
    def writeValues(self, outfile):
        for dataKey in self.dataElements:
            outfile.write(dataKey+"="+self.dataElements[dataKey]+"\n")
        