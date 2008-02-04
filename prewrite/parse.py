
import re
import pbsconfig

HARMONIC = 1
ARITHMETIC = 2
NO_AVG = 3
SUM = 4
PRINT_ALL = 5

avg_type = NO_AVG
patternString = '.*[.]prewrites'
#patternString = 'sucessful_prewrites'

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
#patternString = 'toMemBus.data_idle_fraction.*'
#avg_type = NO_AVG


# print_wls = BW_INTENSE
# print_wls = NOT_BW_INTENSE
np = 4

pattern = re.compile(patternString)

cpuIDPattern = re.compile("[0-9]+")

results = {}

sum = 0
num = 0

for benchmark in pbsconfig.benchmarks:
                resID = pbsconfig.get_unique_id(benchmark)

                resultfile = None
        
                try:
                    resultfile = open(resID+'/'+resID+'.txt')
                except IOError:
                    print "WARNING (quickparse.py):\tCould not find file "+resID+'/'+resID+'.txt'
        
                if resultfile != None:
                    try:
							res = pattern.findall(resultfile.read())

							for string in res:
								print string						
								sum = sum + float(string.split()[1])
                    except:
                        print "N/C" 
			
	
print sum
