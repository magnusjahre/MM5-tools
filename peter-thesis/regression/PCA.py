#!/usr/bin/env python3
from sklearn import decomposition
from common_functions import *

def main():
    x_training, y_training = getTrainingData()
    
    pca = decomposition.PCA()
    model = pca.fit(x_training, y_training)
    
    print(pd.DataFrame(pca.components_, columns = x_training.columns))

if __name__ == '__main__':
    main()