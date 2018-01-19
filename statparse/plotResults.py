
import statparse.metrics as metrics
import math
from statparse import experimentConfiguration
from matplotlib.pyplot import xticks
from statparse.printResults import numberToString

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

def plotArea(xdata, ydata, **kwargs):
    
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    import numpy as np
    from matplotlib import cm
    
    fontsize = 16
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    
    if(len(xdata) == 1):
        raise Exception("We can only have one x series for an area plot")
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ystacked = np.row_stack(ydata)
    
    numDataSets = len(ydata)
    cls = [cm.Blues(1*(float(i)/numDataSets)) for i in range(numDataSets)]
    stacks = ax.stackplot(xdata[0], ystacked, colors=cls)
    
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
        lcols = 3
        if "cols" in kwargs:
            lcols = kwargs["cols"]
        
        proxyRects = [Rectangle((0, 0), 1, 1, fc=pc.get_facecolor()[0]) for pc in stacks]
        ax.legend(proxyRects, kwargs["legend"], ncol=lcols, loc="upper center")
        
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

def plotRawScatter(xdata, ydata, **kwargs):
    
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from matplotlib.markers import MarkerStyle
    
    fontsize = 12    
    width = 16
    height = 3.5
            
    if "figwidth" in kwargs:
        width = kwargs["figwidth"] 
        fontsize = 14
            
    if "largeFonts" in kwargs:
        if kwargs["largeFonts"]:
            fontsize += 4
    
    if "figheight" in kwargs:
        height = kwargs["figheight"] 
    
    matplotlib.rc('ps', useafm=True)
    matplotlib.rc('pdf', use14corefonts=True)
    if "notex" not in kwargs:
        matplotlib.rc('text', usetex=True)
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('legend', fontsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    
    if(len(xdata) != len(ydata)):
        raise Exception("X and Y series data must be of equal length")
    
    fig = plt.figure(figsize=(width,height))
    ax = fig.add_subplot(111)
    
    scatters = []
    assert len(xdata) == len(ydata)
    for i in range(len(xdata)):
        thisColor = cm.Paired(1*(float(i)/float(len(xdata))))
        thisMarker = MarkerStyle.filled_markers[i % len(MarkerStyle.filled_markers)]
        scatters.append(ax.scatter(xdata[i], ydata[i], marker=thisMarker, color=thisColor))
    
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
        plt.legend(scatters, kwargs["legend"], scatterpoints=1)
        
    if "title" in kwargs:
        if kwargs["title"] != "none":
            plt.text(0.5, 0.9, kwargs["title"],
                     horizontalalignment='center',
                     fontsize="large",
                     transform = ax.transAxes)
            
    if "vseparators" in kwargs:
        if kwargs["vseparators"] != "":
            coords = [float(i) for i in kwargs["vseparators"].split(",")]
            for c in coords:
                ax.axvline(x=c, linestyle="dashed")
                
    if "hseparators" in kwargs:
        if kwargs["hseparators"] != "":
            coords = [float(i) for i in kwargs["hseparators"].split(",")]
            for c in coords:
                ax.axhline(y=c, linestyle="dashed")
    
    
    if "filename" in kwargs:
        if kwargs["filename"] != None:
            plt.savefig(kwargs["filename"], type="pdf", bbox_inches='tight')
            return
    
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
    
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from matplotlib.markers import MarkerStyle
    
    fontsize = 12    
    width = 16
    height = 3.5
            
    if "figwidth" in kwargs:
        width = kwargs["figwidth"] 
        fontsize = 14
            
    if "largeFonts" in kwargs:
        if kwargs["largeFonts"]:
            fontsize += 4
    
    if "figheight" in kwargs:
        height = kwargs["figheight"] 
    
    matplotlib.rc('ps', useafm=True)
    matplotlib.rc('pdf', use14corefonts=True)
    if "notex" not in kwargs:
        matplotlib.rc('text', usetex=True)
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('legend', fontsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    
    fig = plt.figure(figsize=(width,height))
    ax = fig.add_subplot(111)
    
    plt.axhline(0, color='black')
    
    markEvery = 1
    if "markEvery" in kwargs:
        markEvery = kwargs["markEvery"]
    
    if "divFactor" in kwargs:
        for i in range(len(ydataseries)):
            for j in range(len(ydataseries[i])):
                ydataseries[i][j] = ydataseries[i][j] / kwargs["divFactor"]
    
    lines = []
    for i in range(len(ydataseries)):
        thisColor = cm.Paired(1*(float(i)/float(len(ydataseries))))
        thisMarker = MarkerStyle.filled_markers[i]
        lines += ax.plot(xvalues, ydataseries[i], color=thisColor, marker=thisMarker, markevery=markEvery)
    
    labels = None
    if "titles" in kwargs:
        if len(kwargs["titles"]) != len(ydataseries):
            raise Exception("The titles list must have the same length as the y-datalist list")
        
        labels = kwargs["titles"]
        for i in range(len(labels)):
            labels[i] = labels[i].replace("_"," ")
        
        addLegend(ax, lines, labels, kwargs)

    rotation = "horizontal"
    if "rotate" in kwargs:
        rotation = kwargs["rotate"]

    if rotation != "horizontal":
        ax.set_xticklabels([int(i) for i in ax.get_xticks()], rotation=rotation)
        ax.set_yticklabels([int(i) for i in ax.get_yticks()])

    if "xlabel" in kwargs:
        ax.set_xlabel(kwargs["xlabel"])
    
    if "ylabel" in kwargs:
        ax.set_ylabel(kwargs["ylabel"])
       
    if "yrange" in kwargs:
        if kwargs["yrange"] != None:
            try:
                minval,maxval = kwargs["yrange"].split(",")
                minval = float(minval)
                maxval = float(maxval)
            except:
                raise Exception("Could not parse yrange string "+str(kwargs["yrange"]))    
            plt.ylim(minval,maxval)
    
    if "figtitle" in kwargs:
        if kwargs["figtitle"] != "none":
            plt.text(0.5, 0.9, kwargs["figtitle"],
                     horizontalalignment='center',
                     fontsize="large",
                     transform = ax.transAxes)
            
    if "separators" in kwargs:
        if kwargs["separators"] != "":
            coords = [float(i) for i in kwargs["separators"].split(",")]
            for c in coords:
                ax.axvline(x=c, linestyle="dashed")
                
    if "labels" in kwargs:
        if kwargs["labels"] != "":
            labelstr = [i for i in kwargs["labels"].split(":")]
            for t in labelstr:
                x,y,text = t.split(",")
                ax.text(float(x),float(y),text)
    
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
        
    if "showPoints" in kwargs:
        for x,y,marker in kwargs["showPoints"]:
            ax.plot(x,y,marker)
    
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
        ax.legend(lines, kwargs["legendTitles"], loc="upper center", ncol=cols)
    
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
        if kwargs["filename"] != None:
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

def flip(items, ncol):
    tmp = [items[i::ncol] for i in range(ncol)]
    
    newitems = []
    for t in tmp:
        newitems += t
    
    return newitems

def plotViolin(names, values, **kwargs):
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import cm
    
    fontsize = 12
    width = 16
    height = 3.5
            
    if "figheight" in kwargs:
        height = kwargs["figheight"]  
    
    if "figwidth" in kwargs:
        width = kwargs["figwidth"] 
        fontsize = 14
    
    if "largeFonts" in kwargs:
        if kwargs["largeFonts"]:
            fontsize += 4
            
    matplotlib.rc('ps', useafm=True)
    matplotlib.rc('pdf', use14corefonts=True)
    matplotlib.rc('text', usetex=True)
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('legend', fontsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    
    fig = plt.figure(figsize=(width,height))
    ax = fig.add_subplot(111)
    
    violinWidth = 0.8
    edgePadding = (1-violinWidth)/2
    pos = range(len(names))
        
    violinData = ax.violinplot(values, pos, points=100, widths=violinWidth, showmeans=False,
                               showextrema=False, showmedians=True, bw_method=0.1)

    plt.setp(violinData['bodies'], facecolor=cm.Blues(0.9), edgecolor='black')
    plt.setp(violinData['cmedians'], edgecolor='black')
    # plt.setp(violinData['cmins'], edgecolor='black')
    # plt.setp(violinData['cmaxes'], edgecolor='black')
    # plt.setp(violinData['cbars'], edgecolor='black')

    ax.set_xlim((-violinWidth/2)-edgePadding, len(names)-(violinWidth/2)-edgePadding)
    ax.set_xticks(pos)
    
    rotation = "horizontal"
    if "rotate" in kwargs:
        rotation = kwargs["rotate"]
    
    ax.set_xticklabels(names, rotation=rotation)
    ax.tick_params(axis="x", direction="out", top="off")
    
    if "xlabel" in kwargs:
        ax.set_xlabel(kwargs["xlabel"])
    
    if "ylabel" in kwargs:
        ax.set_ylabel(kwargs["ylabel"], multialignment='center')
    
    if "yrange" in kwargs:
        if kwargs["yrange"] != None:
            try:
                miny,maxy = kwargs["yrange"].split(",")
                miny = float(miny)
                maxy = float(maxy)
            except:
                raise Exception("Could not parse yrange string "+str(kwargs["yrange"]))    
            plt.ylim(miny,maxy)
    
    if "labels" in kwargs:
        if kwargs["labels"] != "":
            labelstr = [i for i in kwargs["labels"].split(":")]
            for t in labelstr:
                x,y,text = t.split(",")
                ax.text(float(x),float(y),text)
    
    if "filename" in kwargs:
        if kwargs["filename"] != None:
            plt.savefig(kwargs["filename"], type="pdf", bbox_inches='tight')
            return
    plt.show()

def addLegend(ax, plottedItems, legendNames, kwargs):

    useCols = 2
    if "legendColumns" in kwargs:
        if kwargs["legendColumns"] > 0:
            useCols = kwargs["legendColumns"]
        else:
            return
    
    if "mode" in kwargs:
        lmode = kwargs["mode"]
    else:
        lmode = "expand"
    
    bboxHeight = 0.115
    numRows = float(len(legendNames)) / useCols
    if numRows > 1.0:
        legendNames = flip(legendNames, useCols)
        plottedItems = flip(plottedItems, useCols)
        bboxHeight = bboxHeight * math.ceil(numRows)
        if lmode == "expand":
            bboxHeight = 0.3
            
    ax.legend(plottedItems, legendNames, bbox_to_anchor=(0.0, 1.04, 1.0, bboxHeight), loc="center", mode=lmode, borderaxespad=0.0,
              frameon=False, ncol=useCols, handletextpad=0.3, labelspacing=0.15, columnspacing=0.5)  

def plotDataFileBarChart(names, values, legendNames, **kwargs):
    import numpy as np
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib import cm

    fontsize = 12
    width = 16
    height = 3.5
            
    if "figheight" in kwargs:
        height = kwargs["figheight"]  
    
    if "figwidth" in kwargs:
        width = kwargs["figwidth"] 
        fontsize = 14
    
    if "largeFonts" in kwargs:
        if kwargs["largeFonts"]:
            fontsize += 4
            
    matplotlib.rc('ps', useafm=True)
    matplotlib.rc('pdf', use14corefonts=True)
    matplotlib.rc('text', usetex=True)
    matplotlib.rc('xtick', labelsize=fontsize) 
    matplotlib.rc('ytick', labelsize=fontsize)
    matplotlib.rc('legend', fontsize=fontsize)
    matplotlib.rc('font', size=fontsize)
    

    fig = plt.figure(figsize=(width,height))
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
        thisColor = cm.Blues(1*(float(i)/numSeries))
        if errorcols:
            bars.append(ax.bar(ind+(barwidth*i), values[2*i], barwidth, yerr=values[(2*i)+1], ecolor="black", color=thisColor))
            localLegend.append(legendNames[2*i])
        elif errorrows:
            bars.append(ax.bar(ind+(barwidth*i), values[i], barwidth, yerr=errordata[i], ecolor="black", color=thisColor))
        else:
            bars.append(ax.bar(ind+(barwidth*i), values[i], barwidth, color=thisColor))
        
    ax.set_xlim(0, len(names))
    ax.set_xticks(ind+(width/2.0))
         
    rotation = "horizontal"
    if "rotate" in kwargs:
        rotation = kwargs["rotate"]
    
    ax.set_xticklabels(names, rotation=rotation)
    
    plt.axhline(0, color='black')
    
    addLegend(ax, bars, localLegend, kwargs)  
    
    if "xlabel" in kwargs:
        ax.set_xlabel(kwargs["xlabel"])
    
    if "ylabel" in kwargs:
        ax.set_ylabel(kwargs["ylabel"], multialignment='center')
    
    ymax = -1
    if "yrange" in kwargs:
        if kwargs["yrange"] != None:
            try:
                miny,maxy = kwargs["yrange"].split(",")
                miny = float(miny)
                maxy = float(maxy)
            except:
                raise Exception("Could not parse yrange string "+str(kwargs["yrange"]))    
            plt.ylim(miny,maxy)
            ymax = maxy
    
    if "datalabels" in kwargs:
        if kwargs["datalabels"] != "":
            for datalabel in kwargs["datalabels"].split(":"):
                try:
                    labelvalues = datalabel.split(",")
                    seriesindex = int(labelvalues[0])
                    itemindex = int(labelvalues[1])
                    decimals = int(labelvalues[2])
                except:
                    raise Exception("Could not parse datalabel string "+datalabel)
                
                yoffset = 100
                if ymax != -1:
                    yoffset = 0.02 * ymax
                
                for i in range(len(values)):
                    xcoords = ind+(barwidth*i)+(0.5*barwidth)
                    for j in range(len(xcoords)):
                        if i == seriesindex and j == itemindex:
                            plt.text(xcoords[j], yoffset, numberToString(values[i][j], decimals), rotation="vertical", ha="center", va="bottom")

    
    if "separators" in kwargs:
        if kwargs["separators"] != "":
            coords = [float(i) for i in kwargs["separators"].split(",")]
            for c in coords:
                ax.axvline(x=c, linestyle="dashed")
    
    if "linemarkers" in kwargs:
        if kwargs["linemarkers"] != "":
            coords = [float(i) for i in kwargs["linemarkers"].split(",")]
            for c in coords:
                ax.axhline(y=c)
    
    if "labels" in kwargs:
        if kwargs["labels"] != "":
            labelstr = [i for i in kwargs["labels"].split(":")]
            for t in labelstr:
                x,y,text = t.split(",")
                ax.text(float(x),float(y),text)
                
    if "fillBackground" in kwargs:
        if kwargs["fillBackground"] != "":
            labelstr = [i for i in kwargs["fillBackground"].split(":")]
            for t in labelstr:
                x1,x2 = t.split(",")
                ax.axvspan(float(x1),float(x2), alpha=0.5, color='lightgrey', linestyle=None)
    
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