
import sys
import deterministic_fw_wls as workloads

if len(sys.argv) != 3:
    print "Usage: python -c 'import fairmha.analyzePageResults' filename np"
    sys.exit()
    
infile = open(sys.argv[1])
np = int(sys.argv[2])

print "Reading input data from "+sys.argv[1]+"..."

resdata = {}
for l in infile.readlines()[1:]:
    text = l.split()
    keysplit = text[0].split("_")
    assert len(keysplit) == 4
    wl = keysplit[2]
    rflimit = int(keysplit[3])
    
    data = []
    for t in text[1:]:
        if t == "N/A":
            data.append(-1.0)
        else:
            data.append(float(t))
    
    assert len(data) == np
    
    if wl not in resdata:
        resdata[wl] = [{} for i in range(np)]
        
    for i in range(len(data)):
        assert rflimit not in resdata[wl][i]
        resdata[wl][i][rflimit] = data[i]

infile.close()

print "Done!"
print "Writing output file..."

rflimits = resdata[resdata.keys()[0]][0].keys()

outfile = open("rflimtResults.txt", "w")

width = 20

outfile.write("".ljust(width))
for l in rflimits:
    outfile.write(str(l).rjust(width))
outfile.write("\n")

wls = resdata.keys()
wls.sort()

for wl in wls:
    bmnames = workloads.getBms(wl, np)
    for cpuid in range(np):
        outfile.write((wl+"-"+str(cpuid)+"-"+bmnames[cpuid]).ljust(width))
        for rk in resdata[wl][cpuid]:
            outval = resdata[wl][cpuid][rk]
            if outval >= 0:
                outfile.write(str(outval).rjust(width))
            else:
                outfile.write("".rjust(width))
        outfile.write("\n")

outfile.flush()
outfile.close()

print "done!"

