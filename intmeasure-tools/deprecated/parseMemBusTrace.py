
import pbsconfig

print
print "Creating full access trace from individual benchmark traces"
print

def printGNUPlotStyle(name, data, reqs, w):
    sumfile = open(name, "w")

    for i in range(len(data)):
        for j in range(len(data[0])):
            if reqs[i][j] != 0:
                sumfile.write(str(i).ljust(w)+str(j).ljust(w))
                avg = float(data[i][j]) / float(reqs[i][j])
                sumfile.write(str(avg).ljust(w)+"\n")
        sumfile.write("\n")

def printExcelStyle(data, reqs, w):
    
    sumfile = open("qaverages_excel.txt", "w")

    sumfile.write("".ljust(w))
    for j in range(points):
        sumfile.write(str(j).ljust(w))
    sumfile.write("\n")

    for i in range(len(data)):
        sumfile.write(str(i).ljust(w))
        for j in range(len(data[0])):
            if reqs[i][j] != 0:
                avg = float(data[i][j]) / float(reqs[i][j])
                sumfile.write(str(avg).ljust(w))
            else:
                sumfile.write("".ljust(w))
        sumfile.write("\n")


    sumfile.flush()
    sumfile.close()

def f(x,y):
    a=2.51816
    b=0.251003
    c=41.7237
    d=18.0007
    e=80.2123
    return a*x*x+b*y*y+c*x+d*y+e


longtrace = open("fullMemoryBusQueueTrace.dat", 'w')

w = 25
points = 65

data = [[0 for i in range(points)] for j in range(points)]
reqs = [[0 for i in range(points)] for j in range(points)]

allData = [[[] for i in range(points)] for j in range(points)]

for cmd,config in pbsconfig.commandlines:
    id = pbsconfig.get_unique_id(config)
    fname = id+"/MemoryBusQueueTrace.txt"

    print "Parsing file "+fname

    file = open(fname)
    fdata = file.readlines()
    file.close()

    for l in fdata:
        tmpdata = l.split(";")
        if not tmpdata[0].startswith("Reads"):
            outstr = ""
            vals = []
            for d in tmpdata:
                vals.append(int(d))
                outstr += d.strip().ljust(w)
            if vals[0] == 0 and vals[1] == 0:
                pass
            else:
                longtrace.write(outstr+"\n")
            data[vals[0]][vals[1]] += vals[2]
            reqs[vals[0]][vals[1]] += 1
            allData[vals[0]][vals[1]].append(vals[2])

longtrace.flush()
longtrace.close()

printExcelStyle(data,reqs,w)
printGNUPlotStyle("qaverages_gnuplot.txt", data,reqs,w)


sumfile = open("all_latencies.dat", "w")

for i in range(len(allData)):
    for j in range(len(allData[0])):
        for lat in allData[i][j]:
            sumfile.write(str(i).ljust(w)+str(j).ljust(w))
            sumfile.write(str(lat).ljust(w)+"\n")
    sumfile.write("\n")

sumfile.flush()
sumfile.close()

deviationfile = open("avg_func_deviation.dat","w")
for i in range(len(allData)):
    for j in range(len(allData[0])):
        sum = 0.0
        reqs = 0.0
        for lat in allData[i][j]:
            sum += lat
            reqs += 1

        if reqs > 0:
            avg = sum / reqs
            dev = (f(i,j) - avg) / avg
            deviationfile.write(str(i).ljust(w)+str(j).ljust(w))
            deviationfile.write(str(dev).ljust(w))
            deviationfile.write(str(f(i,j) - avg).ljust(w)+"\n")
    deviationfile.write("\n")
    

deviationfile.flush()
deviationfile.close()


