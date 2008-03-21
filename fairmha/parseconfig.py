
import re
import pbsconfig

HARMONIC = 1
ARITHMETIC = 2
NO_AVG = 3
SUM = 4
PRINT_ALL = 5

avg_type = NO_AVG
patternString = 'sim_ticks.*'

#avg_type  = HARMONIC
#avg_type = SUM
#avg_type = PRINT_ALL
#patternString = 'detailedCPU..COM:IPC'+'.*'

#avg_type = NO_AVG
#patternString = 'data_idle_fraction.*'

#avg_type = ARITHMETIC
#patternString = 'L1dcaches..blocked_no_mshr.*'
#patternString = 'L1dcaches..blocked_no_targets.*'

#patternString = 'toMemBus.data_queued.*\.'
patternString = 'toMemBus.data_idle_fraction.*'
avg_type = NO_AVG


BW_INTENSE = 1
NOT_BW_INTENSE = 2
ALL = 3

# print_wls = BW_INTENSE
# print_wls = NOT_BW_INTENSE
print_wls = ALL
bwIntenseWls = [6,7,8,11,12,15,18,24,27,28,35]

np = 4

pattern = re.compile(patternString)

cpuIDPattern = re.compile("[0-9]+")

bmPattern = re.compile("-EBENCHMARK=[a-zA-Z0-9]*")

# PROCEDURES ====================================

def getBenchmark(cmd):
    res = bmPattern.findall(cmd)
    bm = res[0].split('=')[1]
    return int(bm)

# MAIN SCIRPT ===================================

results = {}

for cmd, config in pbsconfig.commandlines:
    resID = pbsconfig.get_unique_id(config)

    resultfile = None
        
    try:
        resultfile = open(resID+'/'+resID+'.txt')
    except IOError:
        print "WARNING (quickparse.py):\tCould not find file "+resID+'/'+resID+'.txt'
        
    if resultfile != None:
        res = pattern.findall(resultfile.read())
        sum = 0.0
        avg = 0.0
        data = []

        for string in res:
            try:
                if avg_type == ARITHMETIC:
                    sum = sum + float(string.split()[1])
                elif avg_type == HARMONIC:
                    num = float(string.split()[1])
                    if num == 0:
                        avg = -2.0
                        break
                    sum = sum + (1.0/num)
                elif avg_type == SUM:
                    sum = sum + float(string.split()[1])
                elif avg_type == PRINT_ALL:
                    tmp = string.split()
                    cpuID = cpuIDPattern.findall(tmp[0])[0]
                    data.append((cpuID, float(tmp[1])))

                else:
                    sum = sum + float(string.split()[1])
            except ValueError:
                avg = -1.0
                break
            
            if avg >= 0.0:
                if avg_type == ARITHMETIC:
                    avg = sum / np
                elif avg_type == HARMONIC:
                    if sum == 0:
                        avg = -1.0
                    else:
                        avg = np/sum
                else:
                    avg = sum

                # store result
                benchmark = getBenchmark(cmd)
                if avg_type == PRINT_ALL:
                    for id, r in data:
                        key = "CPU "+str(id)
                        if benchmark not in results:
                            results[benchmark] = {}
                        results[benchmark][key] = r
                else:
                    key = pbsconfig.get_key(cmd, config)
                                
                    if benchmark not in results:
                        results[benchmark] = {}
                                
                results[benchmark][key] = avg


sortedKeys = results.keys()
sortedKeys.sort()

sortedResKeys = results[sortedKeys[0]].keys()
sortedResKeys.sort()

bmWidth = 10
dataWidth = 35

print " ".ljust(bmWidth),
for k in sortedResKeys:
    print str(k).rjust(dataWidth),
print

for key in sortedKeys:
    
    if print_wls == NOT_BW_INTENSE and int(key) in bwIntenseWls:
        continue
    
    if print_wls == BW_INTENSE and int(key) not in bwIntenseWls:
        continue
    
    print (str(key)).ljust(bmWidth),
    for res in sortedResKeys:
        if res in results[key]:
            print (str(results[key][res])).rjust(dataWidth),
        else:
            print ("N/A").rjust(dataWidth),
    print

