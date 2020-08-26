#!/usr/bin/env python3
from sklearn import feature_selection
from common_functions import *

def main():
    correlation_feature = 'Total Latency'
    
    all_features = ['Tick',
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
            'Hidden Loads',
            'Table CPL',
            'Graph CPL',
            'Num Write Stalls',
            'Average Shared Latency',
            'Average Shared Private Memsys Latency',
            'Shared IPC',
            'Shared Store Lat',
            'Num Shared Stores',
            'Private LLC Hit Estimate',
            'Private LLC Access Estimate',
            'Private LLC Writeback Estimate',
            'Shared LLC Hits',
            'Shared LLC Accesses',
            'Shared LLC Writebacks',
            'LLC Miss/WBs',
            'Total LLC Miss/WBs',
            'Private Tot. Lat',
            'Measured Al. Mem. Lat']
    
    x_training, y_training = getTrainingData()
    
    training = x_training
    training[target_data] = y_training[target_data]
    
    print(training)
    training = training.astype('float64')
    
    corr_matrix = training.corr()
    
    print(corr_matrix[correlation_feature].sort_values(axis=0,ascending=False))

if __name__ == '__main__':
    main()