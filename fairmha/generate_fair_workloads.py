
import random

# Constants
FASTFW_START = 1*10**9
FASTFW_END = int(1.1*10**9)
WORKLOAD_COUNT = 40
SEED = 5669
BW_BM = 2
REST_BM = 2


# Benchmarks
bw_benchmarks = ['mcf','gap','apsi','facerec', 'galgel', 'mesa', 'swim']
other_benchmarks = ['wupwise', 'vortex1', 'sixtrack', 'gcc', 'art', 'gzip', 'mgrid', 'applu']

#bw_benchmarks = ['gcc', 'wupwise', 'swim', 'mgrid', 'applu', 'art', 'facerec', 'ammp', 'lucas', 'apsi']
#other_benchmarks = ['gzip', 'vpr', 'mcf', 'crafty', 'parser', 'eon', 'perlbmk', 'gap', 'vortex1', 'bzip', 'twolf', 'mesa', 'galgel', 'equake', 'sixtrack', 'fma3d']
cpus = [4]

random.seed(SEED)

outfile = open("workloads.py", 'w')
outfile.write("# Autogenerated workload configuration file\n\n")
outfile.write("workloads = {\n\n")

for cpu_count in cpus:

    outfile.write(str(cpu_count)+":{\n")
    for i in range(WORKLOAD_COUNT):
        
        useBenchmarks = []
        useFW = []
        
        num_bw = 0
        num_all = 0

        for j in range(BW_BM):
            fastfw = random.randint(FASTFW_START, FASTFW_END)
            
            bm = -1
            run = True
            while run:
                bm = random.randint(0, len(bw_benchmarks)-1)
                allreadyInUse = False
                for b in useBenchmarks:
                    if bw_benchmarks[bm] == b:
                        allreadyInUse = True
                
                if not allreadyInUse:
                    run = False
                
            useFW.append(fastfw)
            useBenchmarks.append(bw_benchmarks[bm])

        for j in range(REST_BM):
            fastfw = random.randint(FASTFW_START, FASTFW_END)

            bm = -1
            run = True
            while run:
                bm = random.randint(0, len(other_benchmarks)-1)
                allreadyInUse = False
                for b in useBenchmarks:
                    if other_benchmarks[bm] == b:
                        allreadyInUse = True
                
                if not allreadyInUse:
                    run = False
                
            useFW.append(fastfw)
            useBenchmarks.append(other_benchmarks[bm])
        
        if i == (WORKLOAD_COUNT-1):
            outfile.write(str(i+1)+":("+str(useBenchmarks)+","+str(useFW)+")\n")
        else:
            outfile.write(str(i+1)+":("+str(useBenchmarks)+","+str(useFW)+"),\n")

    outfile.write("},\n\n")

outfile.write("}\n")        
outfile.close()
