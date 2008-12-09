
import re
import sys
import pbsconfig
import deterministic_fw_wls as fair_workloads
import single_core_fw as single_core
import fairmha.getInterference
import parsemethods

# Parse mandatory options =======================

TOLERABLE_INST_OFFSET = 0.15

HARMONIC = 1
ARITHMETIC = 2
NO_AVG = 3
SUM = 4
PRINT_ALL = 5

NO_FAIRNESS = 10
HARMONIC_SPEEDUP = 11
WEIGHTED_SUM_IPC = 12
QOS = 13
UNFARINESS_INDEX = 14
IPC_FAIRNESS = 15
ERROR_METRIC = 16

options = {"sum_ipc": ('detailedCPU..COM:IPC'+'.*', SUM, NO_FAIRNESS),
           "all_ipc":('detailedCPU..COM:IPC'+'.*', PRINT_ALL, NO_FAIRNESS),
           "all_com_insts":('detailedCPU..COM:count'+'.*', PRINT_ALL, NO_FAIRNESS),
           "ticks": ('sim_ticks.*', NO_AVG, NO_FAIRNESS),
           "avg_blocked_mshrs": ('L1dcaches..blocked_no_mshr.*', ARITHMETIC, NO_FAIRNESS),
           "avg_blocked_targets": ('L1dcaches..blocked_no_targets.*', ARITHMETIC, NO_FAIRNESS),
           "bus_util": ('toMemBus.bus_utilization.*', NO_AVG, NO_FAIRNESS),
           "bus_latency": ('toMemBus.avg_queue_cycles.*', NO_AVG, NO_FAIRNESS),
           "bus_accesses_per_cpu": ('toMemBus.accesses_per_cpu_[0-9].*', PRINT_ALL, NO_FAIRNESS),
           "bus_blocked": ('toMemBus.blocked_cycles.*',NO_AVG, NO_FAIRNESS),
           "l2_blocked_mshrs": ('L2Bank..blocked_no_mshr.*', ARITHMETIC, NO_FAIRNESS),
           "l2_blocked_targets": ('L2Bank..blocked_no_targets.*', ARITHMETIC, NO_FAIRNESS),
           "total_l2_misses": ('L2Bank..overall_misses.*', SUM, NO_FAIRNESS),
           "HMoS": ('detailedCPU..COM:IPC'+'.*', PRINT_ALL, HARMONIC_SPEEDUP),
           "weighted_sum_ipc": ('detailedCPU..COM:IPC'+'.*', PRINT_ALL, WEIGHTED_SUM_IPC),
           "QoS": ('detailedCPU..COM:IPC'+'.*', PRINT_ALL, QOS),
           "seconds": ('host_seconds.*', NO_AVG, NO_FAIRNESS),
           "UI": ('detailedCPU..COM:total_ticks_stalled_for_memory.*', PRINT_ALL, UNFARINESS_INDEX),
           "fairness": ('detailedCPU..COM:IPC.*', PRINT_ALL, IPC_FAIRNESS),
           "avg_mem_lat_error": ('not a pattern', PRINT_ALL, ERROR_METRIC),
           "avg_hit_service_read": ('ram.average_page_hit_latency_read.*', NO_AVG, NO_FAIRNESS),
           "avg_hit_service_write": ('ram.average_page_hit_latency_write.*', NO_AVG, NO_FAIRNESS),
           "avg_miss_service_read": ('ram.average_page_miss_latency_read.*', NO_AVG, NO_FAIRNESS),
           "avg_miss_service_write": ('ram.average_page_miss_latency_write.*', NO_AVG, NO_FAIRNESS),
           "avg_conflict_service_read": ('ram.average_page_conflict_latency_read.*', NO_AVG, NO_FAIRNESS),
           "avg_conflict_service_write": ('ram.average_page_conflict_latency_write.*', NO_AVG, NO_FAIRNESS),
           "page_read_hits" :('ram.number_of_page_hits_0.*', NO_AVG, NO_FAIRNESS),
           "ram_accesses" :('ram.accesses_per_bank .*', NO_AVG, NO_FAIRNESS),
           }

if len(sys.argv) < 2 or sys.argv[1] not in options:
    print "Usage: python -c \"import fairmha.parseconfig\" patternid [otherOptions...]"
    print
    print "Avaliable patterns:"
    for a in options:
        print "- "+a
    sys.exit()

patternString = options[sys.argv[1]][0]
avg_type = options[sys.argv[1]][1]
fairness_metric = options[sys.argv[1]][2]


# Parse optional options ========================

optionalOptions = {"no_hog": "",
                   "amha_wls": "",
                   "not_amha_wls": "",
                   "acp_wl_only": "",
                   "std_wl_only": "",
                   "all_amha_wls": "",
                   "print_max": "",
                   "one_benchmark":"",
                   "invert_dims":"",
                   "disable_drift_check":"",
                   "compare_to_alone":"",
                   "print_commit_diffs":"",
                   "print_best_w_key":""
                  }

AMHA_WL = 1
NOT_AMHA_WL = 2
ALL = 3
selectedWls = []
BW_WLS = 5
STD_WLS = 6

# default settings
EXCLUDE_HOG = False
print_wls = ALL
wl_selection = ALL
print_max = False
keys_vertical = False
disable_drift_check = False
compare_to_alone = False
print_commit_diffs = False
print_best_w_key = False
invert_dims = False

random_wls = [i for i in range(1,41)]
acp_wls = [i for i in range(41,81)]

std_wls = ['fair08','fair11','fair14','fair27','fair32', 'fair38', 'fair40']  #['05', '07', '15', '20', '27', '28']

bw_wls = ['fair47','fair49','fair52','fair53','fair55','fair60','fair61','fair68','fair76', 'fair79']
#bw_wls = ['fair47','fair51','fair68','fair75','fair77','fair78','fair79'] #['bw03', 'bw18', 'bw23', 'bw27', 'bw31', 'bw35']

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

    if option == "amha_wls":
        print_wls = AMHA_WL
    if option == "not_amha_wls":
        print_wls = NOT_AMHA_WL

    if option == "acp_wl_only":
        wl_selection = BW_WLS
        selectedWls = bw_wls
    if option == "std_wl_only":
        wl_selection = STD_WLS
        selectedWls = std_wls
    if option == "all_amha_wls":
        wl_selection = ALL # simple, inefficent solution
        print_wls = AMHA_WL
        selectedWls = std_wls + bw_wls
    
    if option == "print_max":
       print_max = True

    if option == "one_benchmark":
        keys_vertical = True

    if option == "disable_drift_check":
        disable_drift_check = True

    if option == "compare_to_alone":
        compare_to_alone = True

    if option == "print_commit_diffs":
        print_commit_diffs = True

    if option == "print_best_w_key":
        print_best_w_key = True

    if option == "invert_dims":
        invert_dims = True

# Prepare for analysis ==========================

np = 4

pattern = re.compile(patternString)

cpuIDPattern = re.compile("[0-9]+")

instCntPattern = re.compile("detailedCPU..COM:count.*")
simpleCPUStringPattern = re.compile("simpleCPU[0-9]")

# Control error from instruction drift ==========

starts = {}
if not disable_drift_check:
    for cmd, config in pbsconfig.commandlines:
        resID = pbsconfig.get_unique_id(config)
    
        switchfile = None
        try:
            switchfile = open(resID+'/cpuSwitchInsts.txt')
        except IOError:
            sys.stderr.write("WARNING: could not open switch file for experiment "+resID+"!\n")

        if switchfile != None:
            bm = parsemethods.getBenchmark(cmd)
            key = pbsconfig.get_key(cmd, config)
            if bm not in starts:
                starts[bm] = {}

            if key not in starts[bm]:
                starts[bm][key] = {}

            insts = []
            for i in range(np):
                insts.append(-1)
            for line in switchfile.readlines():
                res = parsemethods.instPattern.findall(line)
                scpuRes = simpleCPUStringPattern.findall(line)
                cpuIDRes = cpuIDPattern.findall(scpuRes[0])
                insts[int(cpuIDRes[0])]= int(res[0])

            starts[bm][key] = insts

    maxdiff = 0.0
    mindiff = 1000.0
    for bm in starts:
        configs = starts[bm].keys()
        for x in configs:
            for y in configs:
                assert len(starts[bm][x]) == len(starts[bm][y])
                for z in range(len(starts[bm][x])):
                    diff = float(starts[bm][x][z]) / float(starts[bm][y][z])
                    testpass = True
                    if diff > maxdiff:
                        maxdiff = diff

                    if diff < mindiff:
                        mindiff = diff

                    if diff < 1.0:
                        if diff < (1.0 - TOLERABLE_INST_OFFSET):
                            testpass = False
                    else:
                        if diff > (1.0 + TOLERABLE_INST_OFFSET):
                            testpass = False
                    if not testpass:
                        print "FATAL: The instruction drift after fast-forwarding was to large: "+str(diff)
                        sys.exit()

    sys.stderr.write("Max difference in drift check: "+str(maxdiff)+"\n")
    sys.stderr.write("Min difference in drift check: "+str(mindiff)+"\n")

# RETRIVE ALONE RESULTS IF NEEDED  ==============

aloneValues = {}
aloneInstCounts = {}
aloneInstCntPerBM = {}

if compare_to_alone:

    assert len(pbsconfig.alonecommands) > 0

    # Retrieve results
    tmpAloneVals = {}
    tmpICounts = {}
    aloneStarts = {}
    for cmd, config in pbsconfig.alonecommands:
        resID = pbsconfig.get_unique_id(config)

        resultfile = None
        
        try:
            resultfile = open(resID+'/'+resID+'.txt')
        except IOError:
            sys.stderr.write("WARNING (quickparse.py):\tCould not find file "+resID+'/'+resID+'.txt\n')
        
        if resultfile != None:
            tmpText = resultfile.read()
            ipc = pattern.findall(tmpText)[0].split()[1]
            tmpAloneVals[parsemethods.getBenchmark(cmd)] = ipc
            iCount = instCntPattern.findall(tmpText)[0].split()[1]
            tmpICounts[parsemethods.getBenchmark(cmd)] = iCount

        switchfile = None
        try:
            switchfile = open(resID+'/cpuSwitchInsts.txt')
        except IOError:
            sys.stderr.write("WARNING: could not open switch file!\n")

        if switchfile != None:     
            insts = []
            for line in switchfile.readlines():
                res = parsemethods.instPattern.findall(line)
                insts.append(int(res[0]))
            
            assert len(insts) == 1
            aloneStarts[parsemethods.getBenchmark(cmd)] = insts[0]

    warningTolerance = 0.5

    mindiff = 1000.0
    minkey = ""
    maxdiff = 0.0
    maxkey = ""

    sum = 0.0
    cnt = 0.0

    for wl in fair_workloads.workloads:
        if wl not in pbsconfig.bmints: #hack
            # Skip workloads that are not part of the experiment
            continue

        bms = fair_workloads.workloads[wl][0]
        
        bmCnt = {}
        transBms = []
        for bm in bms:
            if bm not in bmCnt:
                bmCnt[bm] = 0
            transBms.append(bm+str(bmCnt[bm]))
            bmCnt[bm] = bmCnt[bm] + 1

        key = ""
        if wl < 10:
            key = "fair0"+str(wl)
        else:
            key = "fair"+str(wl)

        aloneValues[key] = []
        aloneInstCounts[key] = []
        for bm in transBms:
            aloneValues[key].append(tmpAloneVals[bm])
            aloneInstCounts[key].append(tmpICounts[bm])

            if bm not in aloneInstCntPerBM:
                aloneInstCntPerBM[bm] = tmpICounts[bm]

        # Compute maximum drift
        if not disable_drift_check:
            assert len(starts) > 0
            wlStarts = starts[key]

            for configs in wlStarts:
                startArray = wlStarts[configs]
                assert len(startArray) == len(transBms)
                for i in range(len(startArray)):
                    diff = float(startArray[i]) / float(aloneStarts[transBms[i]])
                    
                    if diff > maxdiff:
                        maxdiff = diff
                        maxkey = str(key)+"_"+str(configs)
                    if diff < mindiff:
                        mindiff = diff
                        minkey = str(key)+"_"+str(configs)

                    if diff < 1.0:
                        sum = sum + diff
                        cnt = cnt + 1

                    if diff < warningTolerance:
                        sys.stderr.write("WARNING: experiment "+str(key)+"_"+str(configs)+" has a difference of "+str(diff)+"\n")
    if not disable_drift_check:
        sys.stderr.write("Max difference in drift check with alone: "+str(maxdiff)+" for experiment "+maxkey+"\n")
        sys.stderr.write("Min difference in drift check with alone: "+str(mindiff)+", for experiment "+minkey+"\n")
        sys.stderr.write("Average difference where alone outperforms workload: "+str(sum / cnt)+"\n")


# RETRIEVE SIMULATION STATISTICS ================================

results = {}
instCounts = {}

for cmd, config in pbsconfig.commandlines:

    if wl_selection != ALL:
        desicionBM = parsemethods.getBenchmark(cmd)
        
        assert desicionBM.startswith("fair")

        wlNum = int(desicionBM.replace("fair", ""))
        if wl_selection == STD_WLS and wlNum not in random_wls:
            continue
        elif wl_selection == BW_WLS and wlNum not in acp_wls:
            continue
    
    resID = pbsconfig.get_unique_id(config)

    resultfile = None

    try:
        resultfile = open(resID+'/'+resID+'.txt')
    except IOError:
        sys.stderr.write("WARNING (quickparse.py):\tCould not find file "+resID+'/'+resID+'.txt\n')
    
    if resultfile != None:
        fileText = resultfile.read()
        res = pattern.findall(fileText)
        instCntRes = instCntPattern.findall(fileText)
        sum = 0.0
        avg = 0.0
        data = []

        for string in instCntRes:
            tmp = string.split()
            cpuID = cpuIDPattern.findall(tmp[0])[0]
            benchmark = parsemethods.getBenchmark(cmd)
            key = pbsconfig.get_key(cmd, config)

 
            if benchmark not in instCounts:
                instCounts[benchmark] = {}
            
            if str(key) not in instCounts[benchmark]:
                instCounts[benchmark][str(key)] = {}

            instCounts[benchmark][str(key)][cpuID] = tmp[1]
 
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
                    cpuID = cpuIDPattern.findall(string)[0]
                    data.append((cpuID, float(tmp[1])))
                else:
                    assert avg_type == NO_AVG
                    val = string.split()[1]
                    outval = -1.0
                    if val != "no":
                        outval = float(val)
                    sum = outval
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
                benchmark = parsemethods.getBenchmark(cmd)
                key = pbsconfig.get_key(cmd, config)
                if avg_type != PRINT_ALL:
                    if benchmark not in results:
                        results[benchmark] = {}
                    results[benchmark][key] = avg

        key = pbsconfig.get_key(cmd, config)
        if fairness_metric != NO_FAIRNESS:
            benchmark = parsemethods.getBenchmark(cmd)
            key = pbsconfig.get_key(cmd, config)

            if benchmark not in results:
                results[benchmark] = {}
            
            if str(key) not in results[benchmark]:
                results[benchmark][str(key)] = {}

            for id, r in data:
                results[benchmark][str(key)][id] = str(r)
        elif not keys_vertical:
            for id, r in data:
                thisKey = str(key) + "_CPU"+str(id)
                print thisKey
                if benchmark not in results:
                    results[benchmark] = {}
                assert thisKey not in results[benchmark]
                results[benchmark][thisKey] = str(r)
        else:
            for id, r in data:
                resKey = "CPU"+str(id)
                lineKey = str(key)
                if lineKey not in results:
                    results[lineKey] = {}

                assert resKey not in results[lineKey]
                results[lineKey][resKey] = str(r)

# COMPUTE FAIRNESS METRICS ===================================

if fairness_metric == ERROR_METRIC:
    results = {}
    IDs = {}
    for cmd, config in pbsconfig.commandlines:
        resID = pbsconfig.get_unique_id(config)
        wlName = pbsconfig.get_workload(config)
        wlNum = int(wlName.replace("fair",""))
        bmNames = pbsconfig.get_bm_names(fair_workloads.workloads[wlNum], np)
        
        interference = fairmha.getInterference.getInterference(resID+"/"+resID+".txt", np, False)
        assert wlName not in results
        results[wlName] = {}
        
        cpuID = 0
        aloneIDs = []
        for bm in bmNames:
            bmID = pbsconfig.get_bm_id(config, bm)
            aloneIDs.append(bmID)
            aloneTmp = fairmha.getInterference.getInterference(bmID+"/"+bmID+".txt", 1, False)
            aloneLat = float(aloneTmp[1][0])
            sharedInt = float(interference[0][cpuID])
            sharedLat = float(interference[1][cpuID])

            aloneEstimate = sharedLat - sharedInt
            results[wlName][cpuID] = ((aloneEstimate - aloneLat) / aloneLat)
            
            cpuID += 1
        
        IDs[wlName] = (resID, aloneIDs)
    if not disable_drift_check:
        parsemethods.checkAvgLatDriftError(IDs)

elif fairness_metric != NO_FAIRNESS:
    newres = {}
    for wl in results:
        if wl not in newres:
            newres[wl] = {}
        
        for key in results[wl]:
            #compute fairness metric
            if fairness_metric == HARMONIC_SPEEDUP:
                invsum = 0
                for i in range(np):
                    if str(i) in results[wl][key]:
                        result = float(results[wl][key][str(i)])
                        if compare_to_alone:
                            try:
                                invsum = invsum + float(aloneValues[wl][i]) / result
                            except:
                                invsum = -1
                                break
                        else:
                            try:
                                invsum = invsum + (float(results[wl][pbsconfig.fairkey][str(i)]) / result)
                            except:
                                invsum = -1
                                break
                    else:
                        invsum = -1
                        break
                if invsum == -1:
                    newres[wl][key] = "N/A"
                else:
                    newres[wl][key] = np / invsum
                
            elif fairness_metric == WEIGHTED_SUM_IPC:
                sum = 0
                for i in range(np):
                    if str(i) in results[wl][key]:
                        result = float(results[wl][key][str(i)]) 
                        if compare_to_alone:
                            sum = sum + (result / float(aloneValues[wl][i]))
                        else:
                            sum = sum + (result / float(results[wl][pbsconfig.fairkey][str(i)]))
                    else:
                        sum = -1
                        break
                if sum == -1:
                    newres[wl][key] = "N/A"
                else:
                    newres[wl][key] = sum
            elif fairness_metric == QOS:
                val = 0
                for i in range(np):
                    if str(i) in results[wl][key]:

                        result = float(results[wl][key][str(i)])
                        try:
                            if compare_to_alone:
                                val = val + min(0,(result / float(aloneValues[wl][i]))-1)
                            else:
                                val = val + min(0,(result / float(results[wl][pbsconfig.fairkey][str(i)]))-1)
                        except:
                            val = -1
                    else:
                        val = -1
                        break
                if val == -1:
                    newres[wl][key] = "N/A"
                else:
                    newres[wl][key] = val

            elif fairness_metric == UNFARINESS_INDEX:
                values = []
                
                for i in range(np):
                    if str(i) in results[wl][key]:
                        result = float(results[wl][key][str(i)]) / float(instCounts[wl][key][str(i)])
                        if compare_to_alone:
                            tmp = float(aloneValues[wl][i]) / float(aloneInstCounts[wl][i])
                            values.append(result / tmp)
                        else:
                            tmp = float(results[wl][pbsconfig.fairkey][str(i)]) / float(instCounts[wl][pbsconfig.fairkey][str(i)])
                            values.append(result / tmp)
                    else:
                        values = []
                        break

                ui = max(values) / min(values)

                if values == []:
                    newres[wl][key] = "N/A"
                else:
                    newres[wl][key] = ui

            elif fairness_metric == IPC_FAIRNESS:

                values = []
                
                for i in range(np):
                    if str(i) in results[wl][key]:
                        result = float(results[wl][key][str(i)])
                        if compare_to_alone:
                            try:
                                values.append(result / float(aloneValues[wl][i]))
                            except:
                                values = []
                                break
                        else:
                            try:
                                values.append(result / float(results[wl][pbsconfig.fairkey][str(i)]))
                            except:
                                values = []
                                break
                    else:
                        values = []
                        break

                if values == []:
                    newres[wl][key] = "N/A"
                else:
                    ui = min(values) / max(values)
                    newres[wl][key] = ui

            else:
                print "Unknown fairness metric specified, quitting..."
                sys.exit()
            

    results = newres

# CONTROL COMMITTED INSTRUCTION DRIFT =============

if print_commit_diffs:

    bmDict = {}

    for bm in single_core.configuration:
        bmDict[bm] = {}

    for wl in instCounts:
        wlID = int(cpuIDPattern.findall(wl)[0])

        bms = fair_workloads.workloads[wlID][0]
        bmCnt = {}
        transBms = []
        for bm in bms:
            if bm not in bmCnt:
                bmCnt[bm] = 0
            transBms.append(bm+str(bmCnt[bm]))
            bmCnt[bm] = bmCnt[bm] + 1

        for key in instCounts[wl]:
            for i in range(np):
                uniqueKey = str(wl)+"_"+str(key)
                assert uniqueKey not in bmDict[transBms[i]]
                bmDict[transBms[i]][uniqueKey] = int(instCounts[wl][key][str(i)])

    print
    print "Printing larges instruction commit difference between configurations:"
    print
    for bm in bmDict:
        iList = []
        for n, i in bmDict[bm].items():
            iList.append(i)

        print "Diff for "+bm+": "+str(float(max(iList))/float(min(iList)))


    if compare_to_alone:
        print
        print "Printing largest difference with Alone"
        print

        for bm in bmDict:
            iList = []
            for n, i in bmDict[bm].items():
                iList.append(i)

            print "Maxdiff for "+bm+": "+str(float(max(iList))/float(aloneInstCntPerBM[bm]))
            print "Mindiff for "+bm+": "+str(float(min(iList))/float(aloneInstCntPerBM[bm]))

    print
    print "Finished printing commit drift, quitting..."
    print
    sys.exit()

# INVERT DICTIONARY IF NEEDED ================================
if (keys_vertical and avg_type != PRINT_ALL) or invert_dims:
    r2 = {}
    for k1 in results:
        for k2 in results[k1]:
            if k2 not in r2:
                r2[k2] = {}
            if k1 not in r2[k2]:
                r2[k2][k1] = {}
            r2[k2][k1] = results[k1][k2]

    results = r2


# PRINT RESULTS ===================================

sortedKeys = results.keys()
sortedKeys.sort()

sortedResKeys = results[sortedKeys[0]].keys()
sortedResKeys.sort()

if avg_type == PRINT_ALL or keys_vertical:
    bmWidth = 20
    dataWidth = 35
else:
    bmWidth = 10
    dataWidth = 35

if print_best_w_key:
    print " ".ljust(bmWidth),
    print "Best Value".rjust(dataWidth),
    print "Key".rjust(dataWidth)

    for key in sortedKeys:
        
        max = 0
        maxKey = "null"
        for res in sortedResKeys:
            assert res in results[key]
            if results[key][res] > max and res != pbsconfig.fairkey:
                max = results[key][res]
                maxKey = str(res)


        print str(key).ljust(bmWidth),
        print str(max).rjust(dataWidth),
        print maxKey.rjust(dataWidth)

else:
    print " ".ljust(bmWidth),
    for k in sortedResKeys:
        print str(k).rjust(dataWidth),
        if print_max:
            print "Max".rjust(dataWidth),
    print

    for key in sortedKeys:
    
        if print_wls == NOT_AMHA_WL and key in selectedWls:
            continue
    
        if print_wls == AMHA_WL and key not in selectedWls:
            continue
    

        max = 0
        print (str(key)).ljust(bmWidth),
        for res in sortedResKeys:
            if res in results[key]:
                print (str(results[key][res])).rjust(dataWidth),
                if results[key][res] > max:
                    max = results[key][res]
            else:
                print ("N/A").rjust(dataWidth),
            if print_max:
                print str(max).rjust(dataWidth),
        print
    
