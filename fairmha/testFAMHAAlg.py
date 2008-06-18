
import sys
import re

if len(sys.argv) != 2:
    print "Usage: python -c \"import fairmha.testFAMHAAlg algnum\""
    sys.exit()

alg = int(sys.argv[1])
filename = "fairAlgTrace.txt"
np = 4

print
print "Running algorithm "+str(alg)+" on file "+filename
print


# Storage ===============================================

curTick = 0
stall_cycles = {}
read_interference = {}
write_interference = {}
total_reads = {}
total_writes = {}
interference_points = {}
relative_interference_points = {}
relative_interference_searchpoints = {}

inFile = open(filename)
fileLines = inFile.readlines()
inFile.close()

# Parse =================================================

intPattern = re.compile("[0-9]+")
doublePattern = re.compile("[0-9]+\.[0-9]+") 
numPattern = re.compile("([0-9]+\.[0-9]+|[0-9]+)") 

def readIntMatrix(matrix):
    for i in range(np):
        tmpRes = intPattern.findall(fileLines[0])
        fileLines.pop(0)
        for j in range(1, np+1):
            if i not in matrix:
                matrix[i] = {}
            matrix[i][j-1] = int(tmpRes[j])

def readDoubleMatrix(matrix):
    for i in range(np):
        tmpRes = numPattern.findall(fileLines[0])
        fileLines.pop(0)
        for j in range(1,np+1):
            if i not in matrix:
                matrix[i] = {}
            matrix[i][j-1] = float(tmpRes[j])

def parseSection():

    stall_cycles.clear()
    stall_cycles.clear()
    read_interference.clear()
    write_interference.clear()
    total_reads.clear()
    total_writes.clear()
    interference_points.clear()
    relative_interference_points.clear()
    relative_interference_searchpoints.clear()
    
    running = True
    while running:
        if len(fileLines) == 0:
            return False

        if fileLines[0].startswith("FAIR ADAPTIVE"):
            running = False
            fileLines.pop(0)
            return True
        
        elif fileLines[0].startswith("stall cycles", 5):
            for i in range(np):
                tmpRes = intPattern.findall(fileLines[0])[1]
                stall_cycles[i] = int(tmpRes)
                fileLines.pop(0)
            continue
        
        elif fileLines[0].startswith("Read interference matrix"):
            fileLines.pop(0)
            readIntMatrix(read_interference)
        
        elif fileLines[0].startswith("Write interference matrix"):
            fileLines.pop(0)
            readIntMatrix(write_interference)
        
        elif fileLines[0].startswith("Total number of"):
            fileLines.pop(0)
            for i in range(np):
                tmpRes = intPattern.findall(fileLines[0])
                fileLines.pop(0)
                total_reads[i] = int(tmpRes[1])
                total_writes[i] = int(tmpRes[2])

        elif fileLines[0].startswith("Interference points per"):
            fileLines.pop(0)
            for i in range(np):
                tmpRes = doublePattern.findall(fileLines[0])
                fileLines.pop(0)
                interference_points[i] = float(tmpRes[0])
        
        elif fileLines[0].startswith("Relative Interference Point"):
            fileLines.pop(0)
            readDoubleMatrix(relative_interference_points)

        elif fileLines[0].startswith("Relative Interference Searchpoints"):
            fileLines.pop(0)
            readDoubleMatrix(relative_interference_searchpoints)
        else:
            fileLines.pop(0)
    
    


# Algorithms ============================================

mshrs = {0:16, 1:16, 2:16, 3:16}
wb = {0:8, 1:8, 2:8, 3:8}

def controlAlg():
    
    stallPerRead = {}
    for i in range(np):
        stallPerRead[i] = float(stall_cycles[i]) / float(total_reads[i])

    print stallPerRead


# Main Script ===========================================

running = parseSection()
while running:
    running = parseSection()
    if alg == 1:
        controlAlg()
    else:
        print "PANIC: Unknown algorithm"
        sys.exit()
