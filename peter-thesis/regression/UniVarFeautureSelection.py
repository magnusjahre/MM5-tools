#!/usr/bin/env python3
from sklearn import feature_selection
from common_functions import *
from numpy import select

def main():
    x_training, y_training = getTrainingData()
    
    selector = feature_selection.SelectKBest(feature_selection.chi2, k=3)
    selector = selector.fit(x_training, y_training)

    selector.columns = input_data
    
    print(selector.scores_)
    
    for i in range(len(selector.scores_)):
        print(selector.columns[i] , ": " , selector.scores_[i])

if __name__ == '__main__':
    main()