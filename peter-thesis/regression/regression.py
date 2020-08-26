#!/usr/bin/env python3
from sklearn import linear_model
from common_functions import *

def main():
    x_training, y_training = getTrainingData()
    
    lm = linear_model.LinearRegression()
    model = lm.fit(x_training, y_training)
    
    testData(lm)
    
    printModelError(lm, x_training, y_training)

if __name__ == '__main__':
    main()