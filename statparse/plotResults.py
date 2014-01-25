
import statparse.metrics as metrics
from statparse import experimentConfiguration
from matplotlib.pyplot import xticks

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
    
    import numpy as np
    import matplotlib.pyplot as plt
    
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
    
    import matplotlib.pyplot as plt
    
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

def linRegression(xdata, ydata, addZero):
    import numpy as np
    
    if addZero:
        xdata.insert(0, 0.0)
        ydata.insert(0, 0.0)
    
    xvec = np.array(xdata)
    yvec = np.array(ydata)
    A = np.vstack([xvec, np.ones(len(xvec))]).T
    m,c = np.linalg.lstsq(A, yvec)[0]
    return m,c

def plotRawScatter(xdata, ydata, **kwargs):
    
    import matplotlib
    import matplotlib.pyplot as plt
    
        
    fontsize = 16
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    
    if(len(xdata) != len(ydata)):
        raise Exception("X and Y series data must be of equal length")
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    for i in range(len(xdata)):
        ax.plot(xdata[i], ydata[i], 'o')
    
    if "fitLines" in kwargs:
        if kwargs["fitLines"]:
            import numpy as np
            for i in range(len(xdata)):
                m,c = linRegression(xdata[i], ydata[i], True)
                ax.plot(xdata[i], m *np.array(xdata[i]) + c)
                print "Least squares fit of data set "+str(i)+": m="+str(m)+", c="+str(c)
    
    
    if "xlabel" in kwargs:
        if kwargs["xlabel"] != "none":
            ax.set_xlabel(kwargs["xlabel"])
    if "ylabel" in kwargs:
        if kwargs["ylabel"] != "none":
            ax.set_ylabel(kwargs["ylabel"])
        
    if "yrange" in kwargs:
        if kwargs["yrange"] != "":
            try:
                yrange = kwargs["yrange"].split(",")
                ymin = float(yrange[0])
                ymax = float(yrange[1])
            except:
                raise Exception("Invalid yrange string")
            ax.set_ylim(ymin, ymax)
            
    if "xrange" in kwargs:
        if kwargs["xrange"] != "":
            try:
                xrange = kwargs["xrange"].split(",")
                xmin = float(xrange[0])
                xmax = float(xrange[1])
            except:
                raise Exception("Invalid xrange string")
            ax.set_xlim(xmin, xmax)
    
    if "legend" in kwargs:
        ax.legend(kwargs["legend"], "upper center", ncol=len(kwargs["legend"]))
        
    if "title" in kwargs:
        if kwargs["title"] != "none":
            ax.set_title(kwargs["title"])
    
    if "filename" in kwargs:
        if kwargs["filename"] != "":
            plt.savefig(kwargs["filename"], type="pdf")
        else:
            plt.show()
    else:
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
    
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.pyplot import boxplot
    
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
    plt.savefig("recent.pdf")
    if not "no-show" in parameters:
        plt.show()


def plotRawLinePlot(xvalues, ydataseries, **kwargs):
    
    import numpy as np
    import matplotlib
    
    fontsize = 12
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    
    import matplotlib.pyplot as plt
    
    fig = plt.figure(figsize=(8,3))
    ax = fig.add_subplot(111)
    
    plt.axhline(0, color='black')
    
    labels = None
    if "titles" in kwargs:
        if len(kwargs["titles"]) != len(ydataseries):
            raise Exception("The titles list must have the same length as the y-datalist list")
        
        labels = kwargs["titles"]
    
    for i in range(len(ydataseries)):
        if labels != None:
            ax.plot(xvalues, ydataseries[i], label=labels[i])
        else:
            ax.plot(xvalues, ydata[i])
            
    if labels != None:
        if "legendColumns" in kwargs:
            plt.legend(ncol=kwargs["legendColumns"], loc="upper center")
        else:
            plt.legend(ncol=2, loc="upper center")

    if "xlabel" in kwargs:
        ax.set_xlabel(kwargs["xlabel"])
    
    if "ylabel" in kwargs:
        ax.set_ylabel(kwargs["ylabel"])
    
    if "yrange" in kwargs:
        if kwargs["yrange"] != None:
            try:
                min,max = kwargs["yrange"].split(",")
                min = int(min)
                max = int(max)
            except:
                raise Exception("Could not parse yrange string "+str(kwargs["yrange"]))    
            plt.ylim(min,max)
    
    if "filename" in kwargs:
        if kwargs["filename"] != None:
            plt.savefig(kwargs["filename"], type="pdf", bbox_inches='tight')
            return
        
    plt.show()

""" Boxplot supports the following string parameters:
    - data: a list of lists containing the data ranges to be visualized

    - hideOutliers: shows/hides scatterplot of outliers
    - filename: write plot to this file
    - xlabel: x-axis label
    - ylabel: y-axis label
    - titles: A list of x-axis titles which contains the same number of elements
              as the data list
"""    
def plotRawBoxPlot(data, **kwargs):
    
    import numpy as np
    import matplotlib
    
    fontsize = 10
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    
    import matplotlib.pyplot as plt
    from matplotlib.pyplot import boxplot
    
    if "hideOutliers" in kwargs:
        if kwargs["hideOutliers"]:
            outSymbol = ""
        else:
            outSymbol = "b+"
    else:
        outSymbol = "b+"
    
    fig = plt.figure(figsize=(8,3))
    ax = fig.add_subplot(111)
    
    boxplot(data, sym=outSymbol)

    xPositions = [i for i in range(len(data)+1)[1:]] 
    averages = [np.average(d) for d in data]
    avgLine = plt.plot(xPositions, averages, 'o')

    if "titles" in kwargs:
        if len(kwargs["titles"]) != len(data):
            raise Exception("The titles list must have the same length as the data list")
  
        ax.set_xticklabels(kwargs["titles"], rotation="vertical")
    ax.set_xlim(0.5, len(data)+0.5)

    if "rotate" in kwargs:
        for label in ax.get_xticklabels():
            label.set_rotation(kwargs["rotate"])
        
    if "plotmargins" in kwargs:
        if kwargs["plotmargins"] != None:
            left,right,top,bottom = kwargs["plotmargins"] 
            plt.subplots_adjust(left=left, right=right, top=top, bottom=bottom)

    fig.legend(avgLine, ["Arithmetic Mean"], "upper center", numpoints=1)
    
    if "xlabel" in kwargs:
        ax.set_xlabel(kwargs["xlabel"])
    
    if "ylabel" in kwargs:
        ax.set_ylabel(kwargs["ylabel"])
    
    if "filename" in kwargs:
        if kwargs["filename"] != None:
            plt.savefig(kwargs["filename"], type="pdf", bbox_inches='tight')
            return
    
    plt.show()

def plot3DPoints(data, **kwargs):
    assert False, "Not implemented"
#    from enthought.mayavi import mlab
#    
#    plotData, xticLabels, legendTiles = createInvertedPlotData(data)
#    
#    if len(plotData) != 3:
#        raise Exception("3D point plots must consist of three dimensions")
#    
#    mlab.points3d(plotData[0],plotData[1],plotData[2],plotData[2], scale_mode="none", scale_factor=0.2)
#    mlab.axes(x_axis_visibility=True, xlabel=legendTiles[0],
#              y_axis_visibility=True, ylabel=legendTiles[1],
#              z_axis_visibility=True, zlabel=legendTiles[2])
#    mlab.show()
    
def plotNormalized3DPoints(data, **kwargs):
    assert False, "Not implemented"
#    from enthought.mayavi import mlab
#    
#    plotData, xticLabels, legendTiles = createInvertedPlotData(data)
#    
#    if len(plotData) != 3:
#        raise Exception("Normalized 3D point plots must consist of three dimensions")
#    
#
#    xmax = max(plotData[0])
#    xdata = [float(plotData[0][i]) / float(xmax) for i in range(len(plotData[0]))]
#    ymax = max(plotData[1])
#    ydata = [float(plotData[1][i]) / float(ymax) for i in range(len(plotData[1]))]
#    zmax = max(plotData[2])
#    zdata = [float(plotData[2][i]) / float(zmax) for i in range(len(plotData[2]))]
#    
#    mlab.points3d(xdata,ydata,zdata,zdata, scale_mode="none", scale_factor=0.2)
#    mlab.axes(x_axis_visibility=True, xlabel=legendTiles[0],
#              y_axis_visibility=True, ylabel=legendTiles[1],
#              z_axis_visibility=True, zlabel=legendTiles[2])
#    mlab.show()

""" Creates a line plot

    xvalues: a list of values to plot along the x-axis
    yvalues: a list of lists that provide the corresponing y-axis values
"""
def plotLines(xvalues, yvalues, **kwargs):
    
    import matplotlib.pyplot as plt
    
    if len(xvalues) != len(yvalues):
        raise Exception("We need a set of x values for each set of y values")
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    lines = []
    for id in range(len(xvalues)):
        line = ax.plot(xvalues[id], yvalues[id])
        lines.append(line[0])
        id += 1
    
    if "cols" in kwargs:
        cols = kwargs["cols"]
    else:
        if len(yvalues) < 4:
            cols = len(yvalues)
        else:
            cols = 4
    
    if "xlabel" in kwargs:
        if kwargs["xlabel"] != "none":
            ax.set_xlabel(kwargs["xlabel"])
    
    if "ylabel" in kwargs:
        if kwargs["ylabel"] != "none":
            ax.set_ylabel(kwargs["ylabel"])
    
    if "legendTitles" in kwargs:
        ax.legend(lines, kwargs["legendTitles"], "upper center", ncol=cols)
    
    if "xrange" in kwargs:
        if kwargs["xrange"] != "":
            
            try:
                minX,maxX = kwargs["xrange"].split(",")
            except:
                raise Exception("X range spec must be of type min,max")            
            ax.set_xlim( (float(minX), float(maxX))  )
    
    if "yrange" in kwargs:
        if kwargs["yrange"] != "":
            
            try:
                minY,maxY = kwargs["yrange"].split(",")
            except:
                raise Exception("Y range spec must be of type min,max")            
            ax.set_ylim( (float(minY), float(maxY))  )
    
    if "title" in kwargs:
        if kwargs["title"] != "none":
            ax.set_title(kwargs["title"], size="large")
    
    if "filename" in kwargs:
        if kwargs["filename"] != "":
            plt.savefig(kwargs["filename"], type="pdf")
            return
        
    plt.show()
    
def plotImage(image, **kwargs):
    
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    import numpy as np

    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    colormap = None
    if "greyscale" in kwargs:
        if kwargs["greyscale"]:
            assert False, "greyscale not implemented"
            #colormap = cm.grey
    
    plt.imshow(image, origin="lower", cmap=colormap)
    plt.grid(True)
    cbar = plt.colorbar()
    
    if "xrange" in kwargs:
        if kwargs["xrange"] != "":
            
            try:
                minX,maxX = kwargs["xrange"].split(",")
            except:
                raise Exception("X range spec must be of type min,max")            
            ax.set_xlim( (float(minX), float(maxX))  )
    
    if "yrange" in kwargs:
        if kwargs["yrange"] != "":
            
            try:
                minY,maxY = kwargs["yrange"].split(",")
            except:
                raise Exception("Y range spec must be of type min,max")            
            ax.set_ylim( (float(minY), float(maxY))  )
    
    if "zrange" in kwargs:
        if kwargs["zrange"] != "":
            try:
                minZ,maxZ = kwargs["zrange"].split(",")
            except:
                raise Exception("Z range spec must be of type min,max")            
            plt.clim(float(minZ), float(maxZ))
    
    if "xlabel" in kwargs:
        if kwargs["xlabel"] != "none":
            ax.set_xlabel(kwargs["xlabel"], size="large")
    
    if "ylabel" in kwargs:
        if kwargs["ylabel"] != "none":
            ax.set_ylabel(kwargs["ylabel"], size="large")
    
    if "zlabel" in kwargs:
        if kwargs["zlabel"] != "none":
            cbar.set_label(kwargs["zlabel"], size="large")
    
    if "xticklabels" in kwargs:
        plt.xticks(np.arange(len(kwargs["xticklabels"])), kwargs["xticklabels"])
    
    if "yticklabels" in kwargs:
        plt.yticks(np.arange(len(kwargs["yticklabels"])), kwargs["yticklabels"])
    
    if "title" in kwargs:
        ax.set_title(kwargs["title"], size="large")
        
    if "filename" in kwargs:
        if kwargs["filename"] != "":
            plt.savefig(kwargs["filename"], type="pdf")
            return
    
    plt.show()
    
def plotHistogram(data, **kwargs):
    import matplotlib.pyplot as plt
    
    fig = plt.figure()
    ax = fig.add_subplot(111)

    bins = 10
    if "bins" in kwargs:
        bins = kwargs["bins"]

    ax.hist(data, bins=bins)
    
    if "xlabel" in kwargs:
        ax.set_xlabel(kwargs["xlabel"])
    ax.set_ylabel('Frequency')
    ax.grid(True)  
    
    if "title" in kwargs:
        if kwargs["title"] != "":
            ax.set_title(kwargs["title"])
    
    if "filename" in kwargs:
        if kwargs["filename"] != "":
            plt.savefig(kwargs["filename"], type="pdf")
            return
    
    plt.show()

def plotDistribution(distribution, **kwargs):
    
    del distribution["samples"]
    del distribution["max_value"]
    del distribution["min_value"]
    
    data = []
    labels = sorted(distribution.keys())
    
    for l in labels:
        data.append(distribution[l])

    ind = range(0, len(labels))

    import matplotlib.pyplot as plt    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    ax.bar(ind, data, 1.0)
    
    centerticks = [i+0.5 for i in ind]
    ax.set_xticks(centerticks)
    ax.set_xticklabels(labels, rotation="vertical")
    
    plt.show() 

def plotBrokenBarchart(data, **kwargs):
    
    import matplotlib.pyplot as plt
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    yval = 0.5
    for list in data:        
        ax.broken_barh(list, (yval+0.1, 0.8), facecolors='blue')
        yval += 1
    
    ax.grid(True)
    
    if "xlabel" in kwargs:
        if kwargs["xlabel"] != "none":
            ax.set_xlabel(kwargs["xlabel"], size="large")
    
    if "ylabel" in kwargs:
        if kwargs["ylabel"] != "none":
            ax.set_ylabel(kwargs["ylabel"], size="large")
    
    if "title" in kwargs:
        if kwargs["title"] != "":
            ax.set_title(kwargs["title"])
    
    if "filename" in kwargs:
        if kwargs["filename"] != "":
            plt.savefig(kwargs["filename"], type="pdf")
            return
    
    plt.show()
    
def plotRawBarChart(data, **kwargs):
    import matplotlib.pyplot as plt
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    pos = 0
    cols = len(data)
    
    legendRects = []
    
    for i in range(len(data)):
        for j in range(len(data[i])):
            if j >= len(COLORLIST):
                raise Exception("Used up all the colors, aka to many bars")
            b = ax.bar(pos, data[i][j], color=COLORLIST[j])
            pos += 1
            
            if len(legendRects) < len(data[i]):
                legendRects.append(b)
    
    if "legend" in kwargs:
        assert len(kwargs["legend"]) == len(legendRects)
        if "legendcols" in kwargs:
            numcols = kwargs["legendcols"]
        else:
            numcols = 3
        
        ax.legend(legendRects, kwargs["legend"], loc="lower center", ncol = numcols)
    
    colsize = float(pos) / float(cols)
    
    if "xticklabels" in kwargs:
        ax.set_xticks([i*colsize+(colsize/2.0) for i in range(len(kwargs["xticklabels"]))])
        ax.set_xticklabels(kwargs["xticklabels"], rotation="vertical")

    if "filename" in kwargs:
        if kwargs["filename"] != "":
            plt.savefig(kwargs["filename"], type="pdf")
            return
    
    plt.show()
    
def plotDataFileBarChart(names, values, legendNames, **kwargs):
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt

    fontsize = 14
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    
    width = 16
    if "narrow" in kwargs:
        if kwargs["narrow"]:
            width = width/2

    fig = plt.figure(figsize=(width,4))
    ax = fig.add_subplot(111)
    width = 0.8

    for i in range(len(names)):
        names[i] = names[i].replace("_"," ")

    for i in range(len(legendNames)):
        legendNames[i] = legendNames[i].replace("_"," ")

    errorcols = False
    if "errorcols" in kwargs:
        errorcols = kwargs["errorcols"]
        if errorcols:
            if len(values) % 2 != 0:
                raise Exception("Columns must be a multiple of 2 to plot errorcols")

    errorrows = False
    if "errorrows" in kwargs:
        errorrows = kwargs["errorrows"]
        if errorrows:
            errordata = []
            newvalues = []
            for i in range(len(values)):
                errordata.append([])
                newvalues.append([])
                for j in range(len(values[i]))[1::2]:
                    errordata[i].append(values[i][j])
                    newvalues[i].append(values[i][j-1])
                    
            values = newvalues
                
    if errorcols:
        numSeries = len(values)/2
        localLegend = []
    else:
        numSeries = len(values)
        localLegend = legendNames
        
        if errorrows:
            newnames = names[0::2]
            names = newnames
    
    ind = np.arange(len(names))+0.1
    
    bars = []
    for i in range(numSeries):
        barwidth = width/float(numSeries)
        if errorcols:
            bars.append(ax.bar(ind+(barwidth*i), values[2*i], barwidth, yerr=values[(2*i)+1], ecolor="black", color=COLORLIST[i]))
            localLegend.append(legendNames[2*i])
        elif errorrows:
            bars.append(ax.bar(ind+(barwidth*i), values[i], barwidth, yerr=errordata[i], ecolor="black", color=COLORLIST[i]))
        else:
            bars.append(ax.bar(ind+(barwidth*i), values[i], barwidth, color=COLORLIST[i]))
    
    ax.set_xlim(0, len(names))
    ax.set_xticks(ind+(width/2.0))
    ax.set_xticklabels(names, rotation="horizontal")
    
    plt.axhline(0, color='black')
    
    if "legendColumns" in kwargs:
        if kwargs["legendColumns"] > 0:
            ax.legend(bars, localLegend, loc="upper center", ncol=kwargs["legendColumns"])
    else:
        ax.legend(bars, localLegend, loc="upper center", ncol=2)
    
    if "xlabel" in kwargs:
        ax.set_xlabel(kwargs["xlabel"])
    
    if "ylabel" in kwargs:
        ax.set_ylabel(kwargs["ylabel"])
    
    if "yrange" in kwargs:
        if kwargs["yrange"] != None:
            try:
                min,max = kwargs["yrange"].split(",")
                min = int(min)
                max = int(max)
            except:
                raise Exception("Could not parse yrange string "+str(kwargs["yrange"]))    
            plt.ylim(min,max)
    
    if "filename" in kwargs:
        if kwargs["filename"] != None:
            plt.savefig(kwargs["filename"], type="pdf", bbox_inches='tight')
            return
    plt.show()
    
def plotBenchmarkBarChart(names, values, errors, **kwargs):
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt

    fontsize = 10
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    
    fig = plt.figure(figsize=(8,3))
    ax = fig.add_subplot(111)
    width = 0.8
    
    ind = np.arange(len(names))+0.1
    
    rects = ax.bar(ind, values, width, color="r", yerr=errors)
    
    ax.set_xlim(0, len(names))
    ax.set_xticks(ind+(width/2.0))
    ax.set_xticklabels(names, rotation="vertical")
    
    if "xlabel" in kwargs:
        ax.set_xlabel(kwargs["xlabel"])
    
    if "ylabel" in kwargs:
        ax.set_ylabel(kwargs["ylabel"])
    
    
    if "filename" in kwargs:
        if kwargs["filename"] != None:
            plt.savefig(kwargs["filename"], type="pdf", bbox_inches='tight')
            return
    plt.show()