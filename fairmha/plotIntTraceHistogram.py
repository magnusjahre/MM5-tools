
import sys
import plot
import parsemethods

impactfilename = sys.argv[1]
binsize = int(sys.argv[2])
pruneimpact = float(sys.argv[3])
outname = sys.argv[4]
viewstr = sys.argv[5]

view = False
if viewstr == "view":
    view = True

data,colnames,minkey,maxkey = parsemethods.readInterferenceTraceSummary(impactfilename)

# modfiy data according to input
startBin = (minkey / binsize) * binsize
endBin = ((maxkey / binsize)+1) * binsize
binnedData = {}
for i in range(startBin, endBin)[::binsize]:
    binnedData[i] = [0 for j in range(len(colnames))]

zeros = [0 for j in range(len(colnames))]
totals = [0 for j in range(len(colnames))]

for k,da in data:

    cindex = 0
    for d in da:
        if d != -1:
            totals[cindex] += d
        cindex += 1

    if k == 0:
        index = 0
        for d in da:
            if d != -1:
                zeros[index] += d
            index += 1
    else:
        newkey = k - (k%binsize)
        
        index = 0
        for d in da:
            if d != -1:
                binnedData[newkey][index] += d
            index += 1

plotarr = []
keys = binnedData.keys()
keys.sort()
for k in keys:
    useKey = False
    for e in binnedData[k]:
        if not (e < pruneimpact and e > -pruneimpact):
            useKey = True
    
    if useKey:
        plotarr.append( (str(k)+"-"+str(k+binsize),binnedData[k]) )

names = ["Impact Factor", "Interference (cycles)"]
plot.plotHistogram(plotarr,outname,names,colnames, view, True)

sumplotarr = []
for i in range(len(totals)):
    sumplotarr.append( (colnames[i], [totals[i]]) )

names = ["Aggregate Impact Factor", "Interference Type"]
plot.plotHistogram(sumplotarr, outname+"_sum", names, ["Impact"], view, False)