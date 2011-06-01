
import os
import shutil

class Subfigure():
    
    def __init__(self, outfilename):
        self.outfilename = outfilename
        self.figures = []
        self.legends = []
        self.figuredir = "figures"
        
        if os.path.exists(self.figuredir):
            raise Exception("Figures directory exists")
        os.mkdir(self.figuredir)
        
    def addFigure(self, figname, legend):
        
        if not os.path.exists(figname):
            raise Exception("File "+figname+" not found")
        
        shutil.copy(figname, self.figuredir)
        
        basename = os.path.basename(figname)
        self.figures.append(self.figuredir+"/"+basename)
        self.legends.append(legend)
        
    def writeLatex(self, caption, label, width, cols):
        outfile = open(self.outfilename, "w")
    
        print >> outfile, "\\begin{figure*}[tp]"
        print >> outfile, "\\centering"
        
        assert len(self.figures) == len(self.legends)
        for i in range(len(self.figures)):
            if i % cols == 0 and i > 0:
                print >> outfile, "\\\\"
            
            print >> outfile, "\\subfloat["+self.legends[i]+"]{\\includegraphics[width="+str(width)+"\\textwidth]{"+self.figures[i]+"}}"
            
                
        print >> outfile, "\\caption{"+caption+"}"
        print >> outfile, "\\label{"+label+"}"
        print >> outfile, "\\end{figure*}"
    
        outfile.close()
        