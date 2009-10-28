
import numpy as np
import matplotlib.pyplot as plt

def plotBarChart(data):
    
    
    
    titles = data[0][1:]
    
    ind = np.arange(len(titles))
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    lines = 0
    for i in range(len(data))[1:]:
        lines += 1
    
    width = 0.8 / float(lines)
    
    for i in range(len(data))[1:]:
        name = data[i][0]
        values = data[i][1:]
    
        floatvals = []
        for v in values:
            try:
                floatvals.append(float(v))
            except:
                raise Exception("Found non-float in plot table")
            
        colorval = (1.0 / float(lines)) * i
        rgb = (colorval,colorval,colorval)
        
        ax.bar(ind+(width*(i-1)), floatvals, width, label=name, color=rgb)
        
    ax.legend(loc="upper right")
    ax.set_xticks([i+0.5 for i in range(len(titles))])
    ax.set_xticklabels(titles,rotation="vertical")
    
    plt.show()