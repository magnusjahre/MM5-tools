
import os
import popen2
import subprocess

latexheader = """
\documentclass[11pt,a4paper]{article}

\usepackage{graphicx}
\usepackage{subfigure}
\usepackage[left=1in,top=1in,right=1in,bottom=1in]{geometry}

\\begin{document}
"""

latexfooter = """
\end{document}
"""

# Data is a list of rows
def plotGraph(title, xlabel, ylabel, data, lineText, outfilename, printGp):

    datafile = open("tmpdata.txt", "w")

    if data == []:
        datafile.close()
        os.remove('tmpdata.txt')
        print "No data provided, quitting..."
        return ""

    assert(len(data[0])-1 == len(lineText))

    for i in range(len(data)):
        for j in range(len(data[0])):
            datafile.write(str(data[i][j]).ljust(50))
        datafile.write("\n")

    datafile.flush()
    datafile.close()

    scriptfile = open("tmpplot.g", "w")
    scriptfile.write("set title \""+title+"\"\n")
    scriptfile.write("set xlabel \""+xlabel+"\"\n")
    scriptfile.write("set ylabel \""+ylabel+"\"\n")
    #scriptfile.write("set xr["+str(mintick)+":"+str(maxtick)+"]\n");
    #scriptfile.write("set yr[0:1.2]\n");
    scriptfile.write("set key outside below\n")
    scriptfile.write("set terminal postscript eps color enhanced 26\n")
    scriptfile.write("set output \"tmpplot.eps\"\n")

    scriptfile.write("plot")

    index = 2
    for l in lineText[:len(lineText)-1]:
        scriptfile.write("\"tmpdata.txt\" using 1:"+str(index)+" title \'"+l+"\' with linespoints,")
        index += 1
    scriptfile.write("\"tmpdata.txt\" using 1:"+str(index)+" title \'"+lineText[len(lineText)-1]+"\' with linespoints\n")

    scriptfile.flush()
    scriptfile.close()

    res = popen2.popen3("gnuplot tmpplot.g")
    text = res[0].read()

    if printGp:
        print text
        print res[2].read()

    res = popen2.popen3("epstopdf tmpplot.eps")
    text = res[0].read()

    # clean up
    os.rename('tmpplot.pdf', outfilename+'.pdf')
    os.remove('tmpplot.eps')
    os.remove('tmpplot.g')
    os.remove('tmpdata.txt')

    return outfilename+'.pdf'


def plotHeatMap(data, xtitle, ytitle, maxx, maxy, ofilen):
    if data == []:
        print "No data provided, quitting..."
        return ""

    datafile = open("tmpdata.txt", "w")

    w = 25
    for x in range(maxx):
        for y in range(maxy):
            if data[x][y] != 0:
                datafile.write(str(x).ljust(w))
                datafile.write(str(y).ljust(w))
                datafile.write(str(data[x][y]).ljust(w)+"\n")
        datafile.write("\n")

    datafile.flush()
    datafile.close()

    scriptfile = open("tmpplot.g", "w")
    scriptfile.write("set terminal postscript eps color enhanced\n")
    scriptfile.write("set pm3d map\n")
    scriptfile.write("set xlabel \""+xtitle+"\"\n")
    scriptfile.write("set ylabel \""+ytitle+"\"\n")
    scriptfile.write("set xrange [0:"+str(maxx)+"]\n")
    scriptfile.write("set yrange [0:"+str(maxy)+"]\n")
    scriptfile.write("set output \"tmpplot.eps\"\n")
    scriptfile.write("splot \"tmpdata.txt\" using 1:2:3 notitle with pm3d\n")
    scriptfile.flush()
    scriptfile.close()

    res = popen2.popen3("gnuplot tmpplot.g")
    text = res[0].read()
    res = popen2.popen3("epstopdf tmpplot.eps")
    text = res[0].read()

    # clean up
    os.rename('tmpplot.pdf', ofilen+'.pdf')
    os.remove('tmpplot.eps')
    os.remove('tmpplot.g')
    os.remove('tmpdata.txt')

    return ofilen+'.pdf'

    
def createSummaryPdf(plotFiles, doctitle, figTitle, plotTitles, width, outfilename, printRubber):

    assert len(plotFiles) == len(plotTitles)

    texfile = open("plots.tex", "w")

    texfile.write(latexheader)
    if doctitle != "":
        texfile.write("\\title{"+doctitle+"}\n")
        texfile.write("\\maketitle\n")

    texfile.write("\\begin{figure*}[h!]\n")
    texfile.write("\t\\centering\n")
    
    notPrintedTitles = []
    for i in range(len(plotTitles)):
        if plotFiles[i] != "":
            texfile.write("\t\t\\subfigure["+plotTitles[i]+"]{\n")
            texfile.write("\t\t\t\\includegraphics[width="+str(width)+"\\textwidth]{"+plotFiles[i]+"}\n")
            texfile.write("\t\t}\n")
        else:
            notPrintedTitles.append(plotTitles[i])
            

    texfile.write("\\caption{"+figTitle+"}\n")
    texfile.write("\\end{figure*}\n")

    if notPrintedTitles != []:
        texfile.write("The following graphs where not found:\n")
        texfile.write("\\begin{itemize}\n")
        for t in notPrintedTitles:
            texfile.write("\\item "+t+"\n")
        texfile.write("\\end{itemize}\n")


    texfile.write(latexfooter)
    texfile.flush()
    texfile.close()
    
    res = popen2.popen3("rubber --pdf plots.tex")
    text = res[0].read()

    if printRubber:
        print text
        print res[2].read()

    os.rename("plots.pdf", outfilename+".pdf")
    os.remove("plots.aux")
    os.remove("plots.log")
    os.remove("plots.tex")

def plotScatter(name, plotname, xtitle, ytitle, seriesTitles, datafile):
    scriptfile = open(name+".g", "w")
    scriptfile.write("set title \""+plotname+"\"\n")
    scriptfile.write("set xlabel \""+xtitle+"\"\n")
    scriptfile.write("set ylabel \""+ytitle+"\"\n")
    scriptfile.write("set key outside below\n")
    scriptfile.write("set terminal postscript eps color enhanced 26\n")
    scriptfile.write("set output \""+name+".eps\"\n")

    scriptfile.write("plot ")

    index = 2
    for l in seriesTitles[:len(seriesTitles)-1]:
        scriptfile.write("\""+datafile+"\" using 1:"+str(index)+" title \'"+l+"\' with points, \\\n")
        index += 1
    scriptfile.write("\""+datafile+"\" using 1:"+str(index)+" title \'"+seriesTitles[len(seriesTitles)-1]+"\' with points\n")

    scriptfile.flush()
    scriptfile.close()

    subprocess.call(["gnuplot", name+".g"])
    subprocess.call(["epstopdf", name+".eps"])


def writeHistogramDatafile(filename, data, width, titles):
    datafile = open(filename+".dat","w")
    w = width

    if titles != []:
        datafile.write("Key".ljust(w))
        for t in titles:
            datafile.write(t.ljust(w))
        datafile.write("\n")

    for k,vals in data:
        datafile.write(str(k).ljust(w))
        for v in vals:
            datafile.write(str(v).ljust(w))
        datafile.write("\n")
    datafile.flush()
    datafile.close()


def plotHistogram(data, filename, headers, seriesheaders, view, rowstacked):
    writeHistogramDatafile(filename,data,40,[])

    plotfile = open(filename+".g","w")

    if not view:
        plotfile.write("set terminal postscript eps enhanced color size 10,5 26\n")
        plotfile.write("set output \""+filename+".eps\"\n")

    plotfile.write("set title '"+filename+"'\n")
    plotfile.write("set ylabel '"+headers[0]+"'\n")
    plotfile.write("set xlabel '"+headers[1]+"'\n")
    plotfile.write("set style data histogram\n")
    if rowstacked:
        plotfile.write("set style histogram rowstacked\n")
    plotfile.write("set style fill pattern 1  border -1\n")
    plotfile.write("set xtics nomirror rotate by -45\n")
    plotfile.write("set key outside above\n")
    
    plotfile.write("plot '"+filename+".dat' u 2:xtic(1) t '"+seriesheaders[0]+"'")
    if len(seriesheaders) == 1:
        plotfile.write("\n")
    else:
        plotfile.write(",\\\n")

    dindex = 3
    for t in seriesheaders[1:]:
        plotfile.write("'"+filename+".dat' u "+str(dindex)+" t \""+t+"\"")
        if dindex != len(seriesheaders)+1:
            plotfile.write(",\\\n")
        else:
            plotfile.write("\n")
        dindex += 1
    
    
    if view:
        plotfile.write("pause -1")

    plotfile.flush()
    plotfile.close()

    subprocess.call(["gnuplot", filename+".g"])
    if not view:
        subprocess.call(["epstopdf", filename+".eps"])
    

def plotClusteredHistogram(filename, data, clustertitles, headers):
    writeHistogramDatafile(filename,data,50,clustertitles)

    plotfile = open(filename+".g","w")

    
    plotfile.write("set terminal postscript eps enhanced color size 10,5 26\n")
    plotfile.write("set output \""+filename+".eps\"\n")
    plotfile.write("set title '"+filename+"'\n")
    plotfile.write("set ylabel '"+headers[0]+"'\n")
    plotfile.write("set xlabel '"+headers[1]+"'\n")
    plotfile.write("set style data histogram\n")
    plotfile.write("set style histogram clustered gap 0\n")
    plotfile.write("set style fill pattern 1 border -1\n")
    plotfile.write("set xtics nomirror rotate by -90\n")
    plotfile.write("set key outside above\n")

    plotfile.write("plot \\\n")
    for i in range(len(clustertitles)):
        plotfile.write("newhistogram '"+clustertitles[i]+"', '"+filename+".dat' u "+str(i+2)+":xtic(1) notitle")
        if i == len(clustertitles)-1:
            plotfile.write("\n")
        else:
            plotfile.write(",\\\n")

    plotfile.flush()
    plotfile.close()

    subprocess.call(["gnuplot", filename+".g"])
    subprocess.call(["epstopdf", filename+".eps"])

