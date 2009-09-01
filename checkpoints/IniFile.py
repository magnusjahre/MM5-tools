
from IniFileSection import IniFileSection
import re
import sys

__metaclass__ = type

class IniFile():

    sectionPattern = re.compile("\[.*\]")
    whitespacePattern = re.compile("^\s+")
    commentPattern = re.compile("^//.*")
    elementPattern = re.compile(".*=.*")
    
    cacheBlockPattern = re.compile("blk.*")

    def __init__(self):
        pass
        
    def read(self, filename):
        inifile = open(filename)
        
        sections = {}
        
        curSec = None
        
        for l in inifile:
            
            if self.whitespacePattern.findall(l) != []:
                # skip whitespace
                continue
            elif self.commentPattern.findall(l) != []:
                # skip comments
                continue
            
            elif self.sectionPattern.findall(l) != []:
                name = l.strip()
                name = name.replace("[","")
                name = name.replace("]", "") 
                
                path = name.split(".")
                
                currentDict = sections
                while path != []:
                    
                    if path[0] not in currentDict:
                        thisSection = IniFileSection()
                        thisSection.setName(path[0])
                        currentDict[thisSection.name] = thisSection
                    else:
                        thisSection = currentDict[path[0]]
                            
                    currentDict = thisSection.children
                    path.pop(0)
                
                curSec = thisSection
                
                
            elif self.elementPattern.findall(l) != []:
                data = l.split("=")
                curSec.addDataElement(data[0].strip(), data[1].strip())
            
            else:
                print "Unknown section encountered in checkpointfile "+filename
                print "Line: "+l
                sys.exit(-1)
            
            
        inifile.close()
        
        self.pruneSections(sections)
        
        return sections
        
        
    def write(self, filename, sectionDict):
        
        outfile = open(filename, "w")
        
        outfile.write("// Checkpoint written by script\n\n")
        
        self.writeSection(outfile, sectionDict, [])
        
        outfile.flush()
        outfile.close()
        
    def writeSection(self, file, sectionDict, parentNames):
        
        for secName in sectionDict:
            
            curParentNames = parentNames[:]
            curParentNames.append(secName)
            
            path = curParentNames[0]
            for pathElement in curParentNames[1:]:
                path += "."+pathElement
            
            file.write("["+path+"]\n")
            sectionDict[secName].writeValues(file)
            self.writeSection(file, sectionDict[secName].children, curParentNames)
            file.write("\n")

        
    def pruneSections(self, parentDict):
        
        delkeys = []
        for secName in parentDict:
            self.pruneSections(parentDict[secName].children)
            if parentDict[secName].isEmpty():
                delkeys.append(secName)
                
        for dk in delkeys:
            del parentDict[dk]
                
    def printStructureWithoutCacheBlks(self, parentList, indent):
        for secName in parentList:
            if self.cacheBlockPattern.findall(secName) != []:
                continue
            
            print indent+secName+" empty="+str(parentList[secName].isEmpty())
            self.printStructureWithoutCacheBlks(parentList[secName].children, indent+"\t")
            