
import sys
import plot
import parsemethods

infiles = sys.argv[1:]

aggdata = {}
colnames = []

for filename in infiles:

    data,incolnames,minkey,maxkey = parsemethods.readInterferenceTraceSummary(filename)

    sums = [0 for i in range(len(incolnames))]
    for k, ds in data:
        index = 0
        for d in ds:
            if d != -1:
                sums[index] += d
            index += 1

    if colnames == []:
        colnames = incolnames
    else:
        assert len(colnames) == len(incolnames)
        for i in range(len(colnames)):
            assert colnames[i] == incolnames[i]

    assert filename not in aggdata
    aggdata[filename] = sums


clusters = aggdata.keys()
clusters.sort()
plotdata = []
# for i in range(len(colnames)):
#     coldata = []
#     for c in clusters:
#         coldata.append(aggdata[c][i])
        
#     plotdata.append( (colnames[i], coldata) )

for c in clusters:
    tmp = c.split("_")
    key = ""
    if tmp[1] == "CrossbarBased":
        key += "CB-"
    elif tmp[1] == "RingBased":
        key += "Ring-"
    else:
        assert False
    key += tmp[2]

    plotdata.append( (key, aggdata[c]))

headers = ["Aggregate Interference Impact Factor",
           "CMP Architecture"]
#plot.plotClusteredHistogram("plot_sum_impact",plotdata,clustertitles, headers)
plot.plotHistogram(plotdata, "plot-sum-impact", headers, colnames, False, False)

