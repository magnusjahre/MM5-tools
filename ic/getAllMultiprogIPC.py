
import re
import pbsconfig
import workloads

patternString = '.*COM:IPC'+'.*#'

cpuNumPatternStr = '[0-9]'

np = 4

pattern = re.compile(patternString)
cpuNumPattern = re.compile(cpuNumPatternStr)

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
        for match in res:

          # find CPU number and value
          split = match.split()
          cpuNum = int(cpuNumPattern.findall(split[0])[0])

          try:
            value = float(split[1])
          except ValueError:
            value = -1.0
          #print split

          # find benchmark
          bm = workloads.workloads[np][benchmark][0][cpuNum]
          #print "workload is "+str(benchmark)+", bm is "+bm+" has value "+str(value)

          # store result
          if interconnect not in results:
            results[interconnect] = {}

          if bm not in results[interconnect]:
            results[interconnect][bm] = {}

          results[interconnect][bm][benchmark] = value

bmwidth = 20
numwidth = 20

for ic in pbsconfig.interconnects:

	print
	print ic
	print
	print "Benchmark".ljust(bmwidth),
	for i in range(1, len(workloads.workloads[np])+1):
		print str(i).rjust(numwidth),
	print

	bms = results[pbsconfig.interconnects[0]].keys()
	bms.sort()

	for bm in bms:
		print bm.ljust(bmwidth),
		for i in range(1, len(workloads.workloads[np])+1):
			if i in results[ic][bm]:
				print str(results[ic][bm][i]).rjust(numwidth),
			else:
				print "0".rjust(numwidth),
		print
    
