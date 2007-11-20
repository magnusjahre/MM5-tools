
import pbsconfig
import popen2
import re
import os

adaptiveFileName = "adaptiveMHATrace.txt"
memoryFileName = "memoryBusTrace.txt"

cnt = 0
sCnt = 0

patternString = "Adaptive MHA behaviour verified!"
pattern = re.compile(patternString)

for benchmark in pbsconfig.benchmarks:
    for low, high in pbsconfig.adaptiveMHAThresholds:
        for r in pbsconfig.adaptiveRepeats:
    
            resID = pbsconfig.get_unique_id(4, benchmark, pbsconfig.l1mshrs[0], pbsconfig.l2mshrs[0], pbsconfig.l1mshrTargets[0], pbsconfig.l2mshrTargets[0], low, high, r)
    
            os.chdir(resID)
            
            res = popen2.popen3("python -c \"import adaptivemha.verifyAdaptiveActions\" "+adaptiveFileName+" "+memoryFileName+" "+str(high)+" "+str(low)+" "+str(r)+" "+str(pbsconfig.l1mshrs[0]))
            text = res[0].read()
            
            
            res = pattern.findall(text)
            
            cnt = cnt + 1
            if res != []:
                sCnt = sCnt + 1
                print ("Experiment "+str(high)+" "+str(low)+" "+str(r)+":").ljust(30)+("Verified OK!").rjust(20)
            else:
                print ("Experiment "+str(high)+" "+str(low)+" "+str(r)+":").ljust(30)+("Verification FAILED!").rjust(20)
            
            os.chdir("..")
print
print "Adaptive MHA behaved correctly in "+str(sCnt)+" out of "+str(cnt)+" experiments."
print