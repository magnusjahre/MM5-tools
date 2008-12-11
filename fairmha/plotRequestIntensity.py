
import pbsconfig
import plot
import os
import deterministic_fw_wls as fair_wls

points = 65

def getRequestIntensityData(fname):
    data = [[0 for j in range(points)] for i in range(points)]

    file = open(fname)
    text = file.readlines()
    file.close()

    for l in text[1:]:
        tmp = l.split()
        r = int(tmp[0])
        w = int(tmp[1])
        data[r][w] += 1


    return data
    
def getMaxDims(data):

    maxx = 0
    maxy = 0

    for x in range(len(data)):
        for y in range(len(data[0])):
            if data[x][y] != 0 and x > maxx and y > maxy:
                maxx = x
                maxy = y

    return maxx,maxy
                

os.mkdir("requestIntPlots")
os.chdir("requestIntPlots")
os.mkdir("figures")

print
print "Plotting benchmark request intensity..."
print

for cmd,sparams in pbsconfig.commandlines:
    sid = pbsconfig.get_unique_id(sparams)
    wl = pbsconfig.get_workload(sparams)
    np = pbsconfig.get_np(sparams)
    
    print "Plotting files for workload "+wl

    plots = [[] for i in range(2*np)]

    pcnt = 0
    for i in range(np):

        sfname = "../"+sid+"/MemoryBusQueueTrace"+str(i)+".txt"
        sdata = getRequestIntensityData(sfname)
        smx,smy = getMaxDims(sdata)

        aparams = pbsconfig.get_alone_params(wl,i,sparams)
        aid = pbsconfig.get_unique_id(aparams)
        afname = "../"+aid+"/MemoryBusQueueTrace0.txt"
        adata = getRequestIntensityData(afname)
        amx,amy = getMaxDims(adata)

        mx = max(smx,amx)
        my = max(smy,amy)
        
        plots[pcnt] = plot.plotHeatMap(sdata,"Reads","Writes",mx,my,sid+"_"+str(i))
        os.rename(plots[pcnt],"figures/"+plots[pcnt])
        pcnt += 1


        plots[pcnt] = plot.plotHeatMap(adata,"Reads","Writes",mx,my,aid+"_"+str(i))
        os.rename(plots[pcnt],"figures/"+plots[pcnt])
        pcnt += 1


    for i in range(len(plots)):
        plots[i] = "figures/"+plots[i]

    ptitles = []
    wlid = int(wl.replace("fair",""))
    wldata = fair_wls.workloads[wlid]
    for bm in pbsconfig.get_bm_names(wldata,np):
        ptitles.append(bm+" Shared Mode")
        ptitles.append(bm+" Private Mode")


    plot.createSummaryPdf(plots,
                          "",
                          "Request Intensity for Workload "+wl,
                          ptitles,
                          0.45,
                          wl+"_req_intensity",
                          False)
    

        

