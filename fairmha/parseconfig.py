
import re
import sys
import pbsconfig

# Parse mandatory options =======================

HARMONIC = 1
ARITHMETIC = 2
NO_AVG = 3
SUM = 4
PRINT_ALL = 5

options = {"sum_ipc": ('detailedCPU..COM:IPC'+'.*', SUM),
           "ticks": ('sim_ticks.*', NO_AVG),
           "avg_blocked_mshrs": ('L1dcaches..blocked_no_mshr.*', ARITHMETIC),
           "avg_blocked_targets": ('L1dcaches..blocked_no_targets.*', ARITHMETIC),
           "bus_util": ('toMemBus.bus_utilization.*', NO_AVG),
           "bus_latency": ('toMemBus.avg_queue_cycles.*', NO_AVG)
           }

if len(sys.argv) < 2 or sys.argv[1] not in options:
    print "Usage: python -c \"import fairmha.parseconfig\" patternid [otherOptions...]"
    print
    print "Avaliable patterns:"
    for a in options:
        print "- "+a
    exit()

patternString = options[sys.argv[1]][0]
avg_type = options[sys.argv[1]][1]


# Parse optional options ========================

optionalOptions = {"no_hog": "",
                   "selected_wls": "",
                   "not_selected_wls": "",
                   "bw_wl_only": "",
                   "std_wl_only": "",
                  }

SELECTED_WL = 1
NOT_SELECTED_WL = 2
ALL = 3
selectedWls = []
BW_WLS = 5
STD_WLS = 6

# default settings
EXCLUDE_HOG = False
print_wls = ALL
wl_selection = ALL

for option in sys.argv[2:]:
    if option not in optionalOptions:
        print "Unrecognised option: "+option
        print
        print "Available options:"
        for a in optionalOptions:
            print "- "+a
        exit()
    
    if option == "no_hog":
        EXCLUDE_HOG = True

    if option == "selected_wls":
        print_wls = SELECTED_WL
    if option == "not_selected_wls":
        print_wls = NOT_SELECTED_WL

    if option == "bw_wl_only":
        wl_selection = BW_WLS
        selectedWls = ['bw04', 'bw07', 'bw10', 'bw11', 'bw15', 'bw16', 'bw18', 'bw23', 'bw31', 'bw32', 'bw37', 'bw40']
    if option == "std_wl_only":
        wl_selection = STD_WLS
        selectedWls = ['08', '12', '15', '27', '28', '35']


# Prepare for analysis ==========================

np = 4

pattern = re.compile(patternString)

cpuIDPattern = re.compile("[0-9]+")

bmPattern = re.compile("-EBENCHMARK=[a-zA-Z0-9]*")

# PROCEDURES ====================================

def getBenchmark(cmd):
    res = bmPattern.findall(cmd)
    bm = res[0].split('=')[1]
    return bm

# MAIN SCIRPT ===================================

results = {}

for cmd, config in pbsconfig.commandlines:

    if wl_selection != ALL:
        desicionBM = getBenchmark(cmd)
        if wl_selection == STD_WLS and desicionBM.startswith("bw"):
            continue
        elif wl_selection == BW_WLS and desicionBM.isdigit():
            continue
    
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
                    if EXCLUDE_HOG:
                        tmp = string.split()
                        cpuID = int(cpuIDPattern.findall(tmp[0])[0])
                        if cpuID != np-1:
                            sum = sum + float(string.split()[1])
                    else:
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
    
    if print_wls == NOT_SELECTED_WL and key in selectedWls:
        continue
    
    if print_wls == SELECTED_WL and key not in selectedWls:
        continue
    
    print (str(key)).ljust(bmWidth),
    for res in sortedResKeys:
        if res in results[key]:
            print (str(results[key][res])).rjust(dataWidth),
        else:
            print ("N/A").rjust(dataWidth),
    print

