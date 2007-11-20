
import re
import pbsconfig

HARMONIC = 1
ARITHMETIC = 2
NO_AVG = 3
SUM = 4

#avg_type = NO_AVG
#patternString = 'sim_ticks.*'

#avg_type  = HARMONIC
#avg_type = SUM
#patternString = 'COM:IPC'+'.*'

#avg_type = NO_AVG
#patternString = 'data_idle_fraction.*'

#avg_type = SUM
#patternString = 'L1icaches..blocked_no_mshr.*'
#patternString = 'L1icaches..blocked_no_targets.*'

#patternString = 'toMemBus.data_queued.*\.'
#avg_type = NO_AVG

patternString = 'toMemBus.data_idle_fraction.*'
avg_type = NO_AVG

np = 4

pattern = re.compile(patternString)

results = {}
    
for benchmark in pbsconfig.benchmarks:
    for L1mshrCount in pbsconfig.l1mshrs:
        for L2mshrCount in pbsconfig.l2mshrs:
            for L1targets in pbsconfig.l1mshrTargets:
                for L2targets in pbsconfig.l2mshrTargets:

                    resID = pbsconfig.get_unique_id(np, benchmark, L1mshrCount, L2mshrCount, L1targets, L2targets)
                    resultfile = None

                    try:
                        resultfile = open(resID+'/'+resID+'.txt')
                    except IOError:
                        print "WARNING (quickparse.py):\tCould not find file "+resID+'/'+resID+'.txt'

                    if resultfile != None:
                        res = pattern.findall(resultfile.read())
                        sum = 0.0
                        avg = 0.0
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
                        key = -1.0
    
                        if len(pbsconfig.l2mshrs) == 1 and len(pbsconfig.l1mshrTargets) == 1 and len(pbsconfig.l2mshrTargets) == 1:
                            #L1 MSHR count exp
                            key = L1mshrCount
    
                        elif len(pbsconfig.l1mshrs) == 1 and len(pbsconfig.l1mshrTargets) == 1 and len(pbsconfig.l2mshrTargets) == 1:
                            #L2 MSHR count exp
                            key = L2mshrCount
    
                        elif len(pbsconfig.l1mshrs) == 1 and len(pbsconfig.l2mshrs) == 1 and len(pbsconfig.l2mshrTargets) == 1:
                            # L1 target MSHR exp
                            key = L1targets
    
                        elif len(pbsconfig.l1mshrs) == 1 and len(pbsconfig.l2mshrs) == 1 and len(pbsconfig.l1mshrTargets) == 1:
                            # L2 target MSHR exp
                            key = L2targets
    
                        else:
                            print "FATAL: Only one parameter can be varied at the time"
                            sys.exit()
                        
                        if benchmark not in results:
                            results[benchmark] = {}
                        
                        results[benchmark][key] = avg

sortedKeys = results.keys()
sortedKeys.sort()

sortedResKeys = results[sortedKeys[0]].keys()
sortedResKeys.sort()

bmWidth = 10
dataWidth = 20

print " ".ljust(bmWidth),
for k in sortedResKeys:
    print str(k).rjust(dataWidth),
print "Best static".rjust(dataWidth),
print

for key in sortedKeys:
    print (str(key)).ljust(bmWidth),
    best = 0
    for res in sortedResKeys:
        if res in results[key]:
            if results[key][res] > best:
                best = results[key][res]
            print (str(results[key][res])).rjust(dataWidth),
        else:
            print ("N/A").rjust(dataWidth),
    print str(best).rjust(dataWidth),
    print

