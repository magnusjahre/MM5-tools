#!/usr/bin/env python3
from sklearn import linear_model
from common_functions import *
import common_functions

def main():
    selected_features = []
    
    x_training, y_training = getTrainingData()
    
    print("Coefficients of determination: ")
    for i in range(len(common_functions.input_data)):
        coefficients = {}
        for feature in common_functions.input_data:
            if feature in selected_features:
                continue
            lm = linear_model.LinearRegression()
            selection_list = selected_features + [feature]
            training = x_training[selection_list]
            lm.fit(training, y_training)
            coefficients[feature] = lm.score(training, y_training)
    
        for feature in sorted(coefficients, key=coefficients.get, reverse=True):
            print(i, feature , "&" , round(coefficients[feature],5) , "\\\\")
            selected_features.append(feature)
            break
    
    #print(selected_features)
if __name__ == '__main__':
    main()