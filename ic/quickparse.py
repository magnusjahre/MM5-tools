
import re
import pbsconfig

HARMONIC = 1
ARITHMETIC = 2
NO_AVG = 3
SUM = 4
MAX = 5

avg_type = NO_AVG
patternString = 'sim_ticks.*'

#avg_type  = HARMONIC
#avg_type = SUM
#patternString = 'COM:IPC'+'.*'

#patternString = 'L1dcaches..overall_misses.*'
#patternString = 'L1icaches..overall_miss_rate.*'
#avg_type = NO_AVG

#patternString = 'L2Bank..overall_misses.*'
#avg_type = SUM

#patternString = 'COM:count.*'
#avg_type = MAX
#avg_type = SUM

np = 4

pattern = re.compile(patternString)

results = {}

for benchmark in pbsconfig.benchmarks:
  for protocol in pbsconfig.protocols:
    for interconnect in pbsconfig.interconnects:
      resID = pbsconfig.get_unique_id(np, benchmark, protocol, interconnect)
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
                avg = -1.0
                break
              sum = sum + (1.0/num)
            elif avg_type == SUM:
              sum += float(string.split()[1])
            elif avg_type == MAX:
							tmp = float(string.split()[1])
							if tmp > sum:
								sum = tmp
            else:
              sum = float(string.split()[1])
          except ValueError:
            avg = -1.0
            break

        if avg != -1.0:
          if avg_type == ARITHMETIC:
            avg = sum / np
          elif avg_type == HARMONIC:
            if sum == 0:
              avg = -1.0
            else:
              avg = np/sum
          else:
            avg = sum

        if benchmark not in results:
          results[benchmark] = {interconnect:avg}
        else:
          results[benchmark][interconnect] = avg

sortedKeys = results.keys()
sortedKeys.sort()

print ("NP="+str(np)).ljust(20),
for ic in pbsconfig.interconnects:
  print ic.rjust(20),
print

for key in sortedKeys:
  thisDict = results[key]
  print (str(key)+': ').ljust(20),
  for ic in pbsconfig.interconnects:
    if ic in thisDict:
      print (str(thisDict[ic])).rjust(20),
    else:
      print (str(-5.0)).rjust(20),
  print
  
                    
                  
                  
