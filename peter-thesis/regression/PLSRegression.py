#!/usr/bin/env python3
import numpy as np
import pandas as pd
import re
from sklearn import cross_decomposition
import glob
from sklearn.metrics import mean_squared_error
from math import sqrt

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
    inputFiles= "res-4-t-*-b-b-cpl/globalPolicyCommittedInsts3.txt"
    testFiles= "res-4-t-*-b-b-cpl/globalPolicyCommittedInsts0.txt"
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
    lm = cross_decomposition.PLSRegression()
    model = lm.fit(x_training, y_training)
    
    counter = 0
    accumulator = 0
    for filename in sorted(glob.glob(testFiles)):
        counter += 1
        job = re.search('res-4-(.+?)-b-b', filename)
        core_no = re.search('CommittedInsts(.+?).txt', filename)
        data = readFile(filename)
        x = data[input_data]
        y = data[target_data]
        prediction = lm.predict(x)
        #print("Score: ", lm.score(x, y))
        error = rms(prediction, y)
        accumulator += error
        #print(job.group(1) + "-" + core_no.group(1) + ": " + str(error))
    
    print("\nAverage RMS error for jobs: ", accumulator / counter)
    print("\nAverage RMS error for data points: ", rms(lm.predict(x_training), y_training))
    
    print("Coefficients: ", lm.coef_)
    
    #predictions = lm.predict(x_training)
    
    #num_requests = aggregated_data['Total Requests'].to_numpy()
    
    #num_requests = num_requests.reshape(74524,1)
    
    #num_requests = num_requests.astype('float')
    
    #avg_lat = np.divide(predictions, num_requests, where=num_requests!=0)
    
    #sh_avg_lat = np.subtract(avg_lat, 36)
    
    

if __name__ == '__main__':
    main()