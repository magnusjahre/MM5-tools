
import re
import sys
import pbsconfig
import workloads

patternString = '.*COM:IPC'+'.*#'

cpuNumPatternStr = '[0-9]'

np = 4

pattern = re.compile(patternString)
cpuNumPattern = re.compile(cpuNumPatternStr)

results = {}

for benchmark in pbsconfig.benchmarks:
	for L1mshrCount in pbsconfig.l1mshrs:
		for L2mshrCount in pbsconfig.l2mshrs:
			for L1targets in pbsconfig.l1mshrTargets:
				for L2targets in pbsconfig.l2mshrTargets:
					resID = pbsconfig.get_unique_id(np,
																					benchmark,
																					L1mshrCount,
																					L2mshrCount,
																					L1targets,
																					L2targets)
					resultfile = None
            
					try:
						resultfile = open(resID+'/'+resID+'.txt')
					except IOError:
						print "WARNING:\tCould not find file "+resID+'/'+resID+'.txt'
          
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

							# find benchmark
							bm = workloads.workloads[np][benchmark][0][cpuNum]

							key = -1.0
				
							# store result
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
							
							if key not in results:
								results[key] = {}

							if bm not in results[key]:
								results[key][bm] = {}

							results[key][bm][benchmark] = value

bmwidth = 20
numwidth = 20

keys = results.keys()
keys.sort()

for key in keys:

	print
	print key
	print
	print "Benchmark".ljust(bmwidth),
	for i in range(1, len(workloads.workloads[np])+1):
		print str(i).rjust(numwidth),
	print

	bms = results[keys[0]].keys()
	bms.sort()

	for bm in bms:
		print bm.ljust(bmwidth),
		for i in range(1, len(workloads.workloads[np])+1):
			if i in results[key][bm]:
				print str(results[key][bm][i]).rjust(numwidth),
			else:
				print "0".rjust(numwidth),
		print
			
					
    
