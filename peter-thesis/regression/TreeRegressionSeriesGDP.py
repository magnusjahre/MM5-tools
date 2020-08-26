#!/usr/bin/env python3
from sklearn import tree
import graphviz
from common_functions import *

def main():
    x_training, y_training = getTrainingData(True)
    print("Average_RMS_error")
    for i in range(0,101,5):
        max_leafnodes = i
        if i == 0:
            max_leafnodes = 2
        print(max_leafnodes, end = ' ')
        update = str(i) + "\n"
        sys.stderr.write(update)
        tm = tree.DecisionTreeRegressor(max_leaf_nodes=max_leafnodes)
        model = tm.fit(x_training, y_training)
        testGDP(tm)

if __name__ == '__main__':
    main()