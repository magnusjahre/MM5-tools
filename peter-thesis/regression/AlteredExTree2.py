#!/usr/bin/env python3
from sklearn import linear_model
from common_functions import *
import common_functions


def main():
    x_training, y_training = getTrainingData()
    
    print("DATA")
    if len(input_data) <= 12:
        regression_input = common_functions.input_data
    else:
        regression_input = common_functions.input_data[:12]
        
    tree_model = tree.DecisionTreeRegressor(max_leaf_nodes=getMaxLeafNodes(), min_samples_leaf=10)
    model = tree_model.fit(x_training, y_training)
    
    # Makes a dataframe with data points of each leaf node
    data_classification = [pd.DataFrame(columns=input_data)] * (tree_model.max_leaf_nodes * 2)
    for index in range(x_training.shape[0]):
        row_index = tree_model.apply([x_training.iloc[index]])
        row = pd.concat([x_training.iloc[index], y_training.iloc[index]])
        data_classification[row_index[0]] = data_classification[row_index[0]].append(row)
            
    # Makes a linear regressor in each leaf node
    linear_regressors = []
    for i in range(len(data_classification)):
        linear_regressors.append(linear_model.LinearRegression())
    for i in range(len(data_classification)):
        node = data_classification[i]
        if not node.empty:
            x = node[regression_input]
            y = node[common_functions.target_data]
            linear_regressors[i].fit(x,y)
            
    stalls = getAllData()
    
    lin_model = linear_model.LinearRegression()
    stalls_x = stalls[regression_input]
    stalls_y = stalls['Alone Write Stall Cycles'].astype('float64').add(
        stalls['Alone Private Blocked Stall Cycles'].astype('float64')).add(
        stalls['Alone Empty ROB Stall Cycles'].astype('float64'))
    stalls_y = stalls_y.rename("Stall-a")
    stalls_y = pd.DataFrame(stalls_y)
    lin_model = lin_model.fit(stalls_x, stalls_y)
    
    # Custom evaluation using both the Tree and Linear Regressors 
    counter = 0
    accumulator = 0
    for filename in sorted(glob.glob(testFiles)):
        if skipJobTesting(filename):
            continue
        data = readFile(filename)
        if dataSet == 'p':
            data = data[data.index % 4 == 0]
        predictions = np.ndarray(shape=(len(data),1), dtype=float)
        y = data['Measured Alone IPC'].astype('float64')
        previous_committed_insts = 0
        for index, row in data.iterrows():
            x = row[common_functions.input_data]
            classification = tree_model.apply([x])
            x = x[regression_input]
            prediction = linear_regressors[classification[0]].predict([x])
            stalls = lin_model.predict([x])
            mem_ind_stalls = float(row['Memory Independent Stalls'])
            compute_cycles = float(row['Compute Cycles'])
            comm_insts = float(row['Cummulative Committed Instructions']) - previous_committed_insts
            previous_committed_insts = float(row['Cummulative Committed Instructions'])
            predictions[index] = comm_insts / (prediction[0] + stalls[0] + mem_ind_stalls + compute_cycles)
        prediction_df = pd.DataFrame(data=predictions, columns=common_functions.target_data)
        error = rms(prediction_df, y)
        printJobAverage(filename, error)
        accumulator += error
        counter += 1
    
    print("\nAverage RMS error for jobs: ", accumulator / counter)
    #print(accumulator / counter)
    
    printModelError(tree_model, x_training, y_training)
    
    exportTree(tree_model)

if __name__ == '__main__':
    main()