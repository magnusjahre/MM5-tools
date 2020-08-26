#!/usr/bin/env python3
import numpy as np
import pandas as pd
import re
from sklearn import tree
from sklearn import linear_model
import glob
from sklearn.metrics import mean_squared_error
from math import sqrt
import graphviz

def readFile(filename):
    seperator = ";"
    file = open(filename, "r")
    
    first = True
    data = []
    for line in file.read().split('\n'):
        if first:
            first = False
            columns = line.split(seperator)
        else:
            data.append(line.split(seperator))
    
    file.close()
    
    data = np.array(data)
    
    df = pd.DataFrame(data, columns=columns)
    
    x = df[['Tick',
            'Cummulative Committed Instructions',
            'Total Cycles',
            'Stall Cycles',
            'Private Stall Cycles',
            'Shared+Priv Memsys Stalls',
            'Write Stall Cycles',
            'Private Blocked Stall Cycles',
            'Compute Cycles',
            'Memory Independent Stalls',
            'Empty ROB Stall Cycles',
            'Total Requests',
            'Total Latency',
            'Num Write Stalls',
            'Average Shared Latency',
            'Shared Store Lat',
            'Private LLC Hit Estimate',
            'Private LLC Access Estimate',
            'Private LLC Writeback Estimate',
            'Shared LLC Hits',
            'Shared LLC Accesses',
            'Shared LLC Writebacks',
            'LLC Miss/WBs',
            'Total LLC Miss/WBs',
            'Private Tot. Lat',
            'Measured Al. Mem. Lat']]
    
    return x

def rms(y_true, y_pred):
    return sqrt(mean_squared_error(y_true, y_pred))

def main():
    inputFiles= "res-4-t-*-b-b-cpl/globalPolicyCommittedInsts*.txt"
    testFiles= "res-4-t-*-b-b-cpl/globalPolicyCommittedInsts*.txt"
    input_data = [
            'Total Requests',
            'Total Latency',
            'Average Shared Latency',
            'Private LLC Hit Estimate',
            'Private LLC Access Estimate',
            'Private LLC Writeback Estimate',
            'Shared LLC Hits',
            'LLC Miss/WBs',
            'Total LLC Miss/WBs']
    target_data = ['Measured Al. Mem. Lat']
    aggregated_data = pd.DataFrame()
    for filename in glob.glob(inputFiles):
        data = readFile(filename)
        aggregated_data = aggregated_data.append(data)
    
    x_training = aggregated_data[input_data]
    y_training = aggregated_data[target_data]
    tree_model = tree.DecisionTreeRegressor(max_leaf_nodes=100)
    model = tree_model.fit(x_training, y_training)
        
    data_classification = [pd.DataFrame(columns=input_data)] * (tree_model.max_leaf_nodes * 2)
    for filename in glob.glob(inputFiles):
        data = readFile(filename)
        for index, row in data.iterrows():
            row_input = row[input_data]
            row_index = tree_model.apply([row_input])
            data_classification[row_index[0]] = data_classification[row_index[0]].append(row)
            
    linear_regressors = []
    for i in range(len(data_classification)):
        linear_regressors.append(linear_model.LinearRegression())
    
    for i in range(len(data_classification)):
        node = data_classification[i]
        if not node.empty:
            x = node[input_data]
            y = node[target_data]
            linear_regressors[i].fit(x,y)
    
    counter = 0
    accumulator = 0
    for filename in sorted(glob.glob(testFiles)):
        job = re.search('res-4-(.+?)-b-b', filename)
        core_no = re.search('CommittedInsts(.+?).txt', filename)
        data = readFile(filename)
        predictions = np.ndarray(shape=(len(data),1), dtype=float)
        y = data[target_data]
        for index, row in data.iterrows():
            x = row[input_data]
            classification = tree_model.apply([x])
            prediction = linear_regressors[classification[0]].predict([x])
            predictions[index] = prediction[0]
        prediction_df = pd.DataFrame(data=predictions, columns=target_data)
        error = rms(prediction_df, y)
        print(job.group(1) + "-" + core_no.group(1) + ": " , error)
        accumulator += error
        counter += 1
    
    print("\nAverage RMS error for jobs: ", accumulator / counter)
    print("\nAverage RMS error for data points: ", rms(tree_model.predict(x_training), y_training))
    
    dot_data = tree.export_graphviz(model, out_file=None, 
                                    feature_names=input_data,
                                    class_names=target_data,
                                    rounded=True,
                                    filled=True,
                                    special_characters=True)
    graph = graphviz.Source(dot_data)
    graph.render("tree")
    
    

if __name__ == '__main__':
    main()