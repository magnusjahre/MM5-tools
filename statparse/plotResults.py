
import numpy as np
import matplotlib.pyplot as plt
from enthought.mayavi import mlab
import statparse.metrics as metrics
from matplotlib.pyplot import boxplot
from statparse import experimentConfiguration

COLORLIST = []
baseRGBOptions = [0.0, 1.0, 0.5]
for i in baseRGBOptions:
    for j in baseRGBOptions:
        for k in baseRGBOptions:
            newtuple = (i,j,k)
            if newtuple not in COLORLIST:
                COLORLIST.append( newtuple )

plotnames = ["bar", "scatter", "box"]
plotFileName = "plot.pdf"

def getPlotFunctionFromName(plotname):
    
    if plotname == "bar":
        return plotBarChart
    if plotname == "scatter":
        return plotScatter
    if plotname == "box":
        return plotBoxPlot
    
    return None

def parsePlotParamString(kwargs):
    if "plotParamString" not in kwargs:
        return {}
    
    if kwargs["plotParamString"] == "":
        return {}
    
    params, spec = experimentConfiguration.parseParameterString(kwargs["plotParamString"])
    return params        

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
            if data[i][j] != metrics.errorString:
                newdata[j][i] = float(data[i][j])                
    
    return newdata, xticLabels, legendTitles

def plotBarChart(data, **kwargs):
    
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
        plottedLines.append(l[0])
    
    cols = 5
    if len(legendTitles) < cols:
        cols = len(legendTitles)
    
    fig.legend(plottedLines, legendTitles, "upper center", ncol=cols)
    ax.set_xticks([i+0.4 for i in range(len(xticLabels))])
    ax.set_xticklabels(xticLabels,rotation="vertical")
    
    plt.savefig(plotFileName)
    plt.show()
    
def plotScatter(data, **kwargs):
    
    plotData, xticLabels, legendTiles = createInvertedPlotData(data)
    
    if len(plotData) != 2:
        raise Exception("Scatter plots must consist of two dimensions")
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(plotData[0], plotData[1], 'o')
    
    fontsize = 14
    
    ax.set_xlabel(legendTiles[0], fontsize=fontsize)
    ax.set_ylabel(legendTiles[1], fontsize=fontsize)
    
    
    for label in ax.get_xticklabels():
        label.set_fontsize(fontsize) 
    
    for label in ax.get_yticklabels():
        label.set_fontsize(fontsize) 
    
    
    plt.savefig(plotFileName, type="pdf")
    plt.show()

""" Boxplot supports the following string parameters:
    - no-outliers: shows/hides scatterplot of outliers
    - xlabel: x-axis label
    - ylabel: y-axis label
    - no-show: do not show plot
    - filename: write plot to this file
    - yrange: minimum y value and maximum y value splitted by a T
"""    
def plotBoxPlot(data, **kwargs):
    
    parameters = parsePlotParamString(kwargs)
    if "no-outliers" in parameters:
        outSymbol = ""
    else:
        outSymbol = "b+"
    
    plotData, xticLabels, legendTiles = createInvertedPlotData(data)
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    boxplot(plotData, sym=outSymbol)
    
    xPositions = [i for i in range(len(plotData)+1)[1:]] 
    averages = [np.average(d) for d in plotData]
    
    avgLine = plt.plot(xPositions, averages, 'o')
    
    ax.set_xticklabels(legendTiles)
    ax.set_xlim(0.5, len(legendTiles)+0.5)
    
    fig.legend(avgLine, ["Arithmetic Mean"], "upper center", numpoints=1)
    
    if "yrange" in parameters:
        try:
            yrange = parameters["yrange"].split("T")
            ymin = float(yrange[0])
            ymax = float(yrange[1])
        except:
            raise Exception("Invalid yrange string")
        ax.set_ylim(ymin, ymax)
    
    if "xlabel" in parameters:
        ax.set_xlabel(parameters["xlabel"])
    
    if "ylabel" in parameters:
        ax.set_ylabel(parameters["ylabel"])
    
    if "filename" in parameters:
        plt.savefig(parameters["filename"], type="pdf")
    else:
        plt.savefig(plotFileName)
    
    if not "no-show" in parameters:
        plt.show()
    
def plot3DPoints(data, **kwargs):
    
    plotData, xticLabels, legendTiles = createInvertedPlotData(data)
    
    if len(plotData) != 3:
        raise Exception("3D point plots must consist of three dimensions")
    
    mlab.points3d(plotData[0],plotData[1],plotData[2],plotData[2], scale_mode="none", scale_factor=0.2)
    mlab.axes(x_axis_visibility=True, xlabel=legendTiles[0],
              y_axis_visibility=True, ylabel=legendTiles[1],
              z_axis_visibility=True, zlabel=legendTiles[2])
    mlab.show()
    
def plotNormalized3DPoints(data, **kwargs):
    
    plotData, xticLabels, legendTiles = createInvertedPlotData(data)
    
    if len(plotData) != 3:
        raise Exception("Normalized 3D point plots must consist of three dimensions")
    

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
    