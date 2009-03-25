
import sys
import pbsconfig
import re

np = int(sys.argv[1])
channels = int(sys.argv[2])

patterns = {
    "avg_hit_service_read": re.compile('ram..average_page_hit_latency_read.*'),
    "avg_hit_service_write": re.compile('ram..average_page_hit_latency_write.*'),
    "avg_miss_service_read": re.compile('ram..average_page_miss_latency_read.*'),
    "avg_miss_service_write": re.compile('ram..average_page_miss_latency_write.*'),
    "avg_conflict_service_read": re.compile('ram..average_page_conflict_latency_read.*'),
    "avg_conflict_service_write": re.compile('ram..average_page_conflict_latency_write.*')}

chanpattern = re.compile("[0-9]")

results = {}

for cmd,config in pbsconfig.commandlines:
    if config[1] == np and config[2] == channels:
        resID = pbsconfig.get_unique_id(config)
        
        resfile = None
        try:
            resfile = open(resID+"/"+resID+".txt")
        except:
            print "Could not find "+resID

        if resfile != None:
            restext = resfile.read()

            if resID not in results:
                results[resID] = {}

            for p in patterns:
                res = patterns[p].findall(restext)

                for r in res:
                    tmp = r.split()
                    key = tmp[0]
                    cs = int(chanpattern.findall(key)[0])
                    val = tmp[1]
                    
                    if p not in results[resID]:
                        results[resID][p] = {}

                    assert cs not in results[resID][p]
                    results[resID][p][cs] = val

            resfile.close()

width = 30

pats = patterns.keys()
pats.sort()

print "".ljust(width),
for p in pats:
    for c in range(channels):
        print (p+"-c"+str(c)).rjust(width),
print

for id in results:
    print id.ljust(width),
    for p in pats:
        for c in range(channels):
            if c in results[id][p] and "no" != results[id][p][c]:
                print str(results[id][p][c]).rjust(width),
            else:
                print "N/A".rjust(width),
    print
