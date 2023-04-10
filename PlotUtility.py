
import matplotlib.pyplot as plt


class ScatterData:
    def __init__(self,x,y,color,label,marker,alpha):
        self.x = x
        self.y = y
        self.color = color
        self.label = label
        self.marker = marker
        self.alpha = alpha
class PlotData:
    def __init__(self,x,y,color,label,alpha):
        self.x = x
        self.y = y
        self.color = color
        self.label = label
        self.alpha = alpha
class HistogramData:
    def __init__(self,data,numBins):
        self.data = data
        self.numBins = numBins


def PlotHelper(title, xLabel, yLabel, scatterData = None, plotData = None, histogramData = None):
    fig = plt.figure()
    ax= plt.axes()
    ax.set_xlabel(xLabel)
    ax.set_ylabel(yLabel)
    ax.set_title(title, loc='left')
    
    #(self,x,y,color,label,marker,alpha):
    if scatterData is not None:
        for data in scatterData:
            if data.color == None:
                ax.scatter(data.x,data.y, label = data.label, alpha = data.alpha, marker =data.marker)
            else:
                ax.scatter(data.x,data.y, label = data.label, color=data.color, alpha = data.alpha, marker =data.marker)
    
    if plotData is not None:
        for data in plotData:
            if data.color == None:
                ax.plot(data.x,data.y, label = data.label, alpha = data.alpha)
            else:
                ax.plot(data.x,data.y, label = data.label, color=data.color, alpha = data.alpha)
    
    if histogramData is not None:
        plt.hist(histogramData.data, bins=histogramData.numBins)
            
    plt.legend()
    plt.show()