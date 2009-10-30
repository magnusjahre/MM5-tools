
import numpy as np
import matplotlib.pyplot as plt

COLORLIST = []
baseRGBOptions = [0.0, 1.0, 0.5]
for i in baseRGBOptions:
    for j in baseRGBOptions:
        for k in baseRGBOptions:
            newtuple = (i,j,k)
            if newtuple not in COLORLIST:
                COLORLIST.append( newtuple )

def createInvertedPlotData(data):

    legendTitles = data.pop(0)[1:]
    
    xticLabels = []
    for i in range(len(data)):
        xticLabels.append(data[i].pop(0))    
    
    newdata = []
    for i in range(len(legendTitles)):
        newdata.append([0.0 for j in range(len(xticLabels))])
   
    for i in range(len(xticLabels)):
        for j in range(len(legendTitles)):    
            newdata[j][i] = float(data[i][j])                
    
    return newdata, xticLabels, legendTitles

def plotBarChart(data):
    
    plotData, xticLabels, legendTitles = createInvertedPlotData(data)  
    
    ind = np.arange(len(xticLabels))
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    lines = len(legendTitles)
    width = 0.8 / float(lines)
    
    assert len(plotData) == lines
    plottedLines = []
    for i in range(lines):
        if i >= len(COLORLIST):
            raise Exception("Don't have enough colors to plot")        
        l = ax.bar(ind+(width*i), plotData[i], width, color=COLORLIST[i])
        plottedLines.append(l[i])
    
    cols = 5
    if len(legendTitles) < cols:
        cols = len(legendTitles)
    
    fig.legend(plottedLines, legendTitles, "upper center", ncol=cols)
    ax.set_xticks([i+0.4 for i in range(len(xticLabels))])
    ax.set_xticklabels(xticLabels,rotation="vertical")
    
    plt.show()