
import numpy as np
import matplotlib.pyplot as plt
from enthought.mayavi import mlab

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
    
def plot3DPoints(data):
    
    plotData, xticLabels, legendTiles = createInvertedPlotData(data)
    
    if len(plotData) != 3:
        raise Exception("Surface plots must consist of three dimensions")
    
    mlab.points3d(plotData[0],plotData[1],plotData[2],plotData[2], scale_mode="none", scale_factor=0.2)
    mlab.axes(x_axis_visibility=True, xlabel=legendTiles[0],
              y_axis_visibility=True, ylabel=legendTiles[1],
              z_axis_visibility=True, zlabel=legendTiles[2])
    mlab.show()
    
def plotNormalized3DPoints(data):
    
    plotData, xticLabels, legendTiles = createInvertedPlotData(data)
    
    if len(plotData) != 3:
        raise Exception("Surface plots must consist of three dimensions")
    

    xmax = max(plotData[0])
    xdata = [float(plotData[0][i]) / float(xmax) for i in range(len(plotData[0]))]
    ymax = max(plotData[1])
    ydata = [float(plotData[1][i]) / float(ymax) for i in range(len(plotData[1]))]
    zmax = max(plotData[2])
    zdata = [float(plotData[2][i]) / float(zmax) for i in range(len(plotData[2]))]
    
    mlab.points3d(xdata,ydata,zdata,zdata, scale_mode="none", scale_factor=0.2)
    mlab.axes(x_axis_visibility=True, xlabel=legendTiles[0],
              y_axis_visibility=True, ylabel=legendTiles[1],
              z_axis_visibility=True, zlabel=legendTiles[2])
    mlab.show()
    