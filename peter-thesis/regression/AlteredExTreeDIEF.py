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
        for index, row in data.iterrows():
            x = row[common_functions.input_data]
            classification = tree_model.apply([x])
            x = x[regression_input]
            prediction = linear_regressors[classification[0]].predict([x])
            if prediction[0][0] < 0:
                prediction[0][0] = 0
            predictions[index] = prediction[0]
                
        total_stall_estimate = pd.DataFrame(data=predictions, columns=common_functions.target_data)
        
        total_stall_estimate = pd.Series(data=total_stall_estimate['Measured Sh/Pr Mem Stalls'])
        
        predictions_df = data['Estimated Private Latency'].astype('float64')
        avg_pr_latency = data['Average Shared Private Memsys Latency'].astype('float64')
        pr_latency = predictions_df.add(avg_pr_latency)
        avg_sh_latency = data['Average Shared Latency'].astype('float64')
        sh_latency = avg_sh_latency.add(avg_pr_latency)
        ratio = pr_latency.div(sh_latency)
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
        ratio = ratio.fillna(0)
        shared_store_lat = data['Shared Store Lat'].astype('float64')
        pr_store_lat = data['Estimated Alone Store Lat'].astype('float64')
        store_ratio = pr_store_lat.div(shared_store_lat)
        store_ratio = store_ratio.replace([np.inf, -np.inf], np.nan)
        store_ratio = store_ratio.fillna(0)
        target_prediction = stallToIPC(data, total_stall_estimate, ratio, store_ratio)
            
        error = rms(target_prediction, y)
        printJobAverage(filename, error)
        accumulator += error
        counter += 1
    
    #print("\nAverage RMS error for jobs: ", accumulator / counter)
    #print(accumulator / counter)
    
    #printModelError(tree_model, x_training, y_training)
    
    exportTree(tree_model)

if __name__ == '__main__':
    main()