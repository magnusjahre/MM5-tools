#!/usr/bin/env python3
from sklearn import linear_model
from common_functions import *
import common_functions
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

exportTreeCpp = False


def main():
    x_training, y_training = getTrainingData()
    
    print("DATA")
    
    #cci_input = [4221634,7657072,10257940,14106097,18347081,21278032,24551344,24784876,25014877,25249902,25551032,25893097,28058211,31241154,31368729,31488153,31632385,31794297,31963705,32119769,32280249,32492329,32712137,32924177,33145277,36389875,40072112,41854723,44075147,46246563,47864473,50713444,54851245,59588851,63742946,67792230,73373379,78910977,84381154,89719183,93771062,94576799,94733183,94936727,95156943,95391135,98838568,102788283,106146539,109353261,113560838,117872783,121726383,124632366,124964641,125386763,126192060,130137138,131383378,131580106,131882810,132192346,132521258,132873426,134108156,138519047,141059647,143573975,145574670]
    
    if len(input_data) <= 120:
        regression_input = common_functions.input_data
    else:
        regression_input = common_functions.input_data[:12]
        
    tree_model = tree.DecisionTreeRegressor(max_leaf_nodes=getMaxLeafNodes(), min_samples_leaf=10)
    pca = PCA(n_components=6)
    scaler = StandardScaler()
    scaler.fit(x_training)
    x_scaled = scaler.transform(x_training)
    pca.fit(x_scaled)
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
            scaled_x = scaler.transform(x)
            new_x = pca.transform(scaled_x)
            y = node[common_functions.target_data]
            linear_regressors[i].fit(new_x,y)
    
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
        y = data[common_functions.target_data]
        for index, row in data.iterrows():
            x = row[common_functions.input_data]
            classification = tree_model.apply([x])
            x = x[regression_input]
            x = pd.Series.to_numpy(x)
            x = x.reshape(1,-1)
            x_scaled = scaler.transform(x)
            new_x = pca.transform(x_scaled)
            prediction = linear_regressors[classification[0]].predict(new_x)
            predictions[index] = prediction[0]
        prediction_df = pd.DataFrame(data=predictions, columns=common_functions.target_data)
        prediction_df[prediction_df < 0] = 0
        #for index,row in prediction_df.iterrows():
            #print(cci_input[index], end=';')
            #print(row[0])
        error = rms(prediction_df, y)
        printJobAverage(filename, error)
        accumulator += error
        counter += 1
    
    #print("\nAverage RMS error for jobs: ", accumulator / counter)
    #print(accumulator / counter)
    
    #printModelError(tree_model, x_training, y_training)
    
    if exportTreeCpp:
        printCpp(tree_model, linear_regressors, regression_input)
    
    exportTree(tree_model)

if __name__ == '__main__':
    main()