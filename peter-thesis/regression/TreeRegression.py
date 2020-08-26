#!/usr/bin/env python3
from sklearn import tree
import graphviz
from common_functions import *

def main():
    x_training, y_training = getTrainingData()
    tm = tree.DecisionTreeRegressor(max_leaf_nodes=getMaxLeafNodes())
    model = tm.fit(x_training, y_training)
    
    print("DATA")
    
    testData(tm)
    
    #printModelError(tm, x_training, y_training)
    
    exportTree(model)

if __name__ == '__main__':
    main()