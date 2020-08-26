import sys
import numpy as np
import pandas as pd
import re
import glob
from sklearn.metrics import mean_squared_error
from sklearn import tree
from math import sqrt
import graphviz
from constants import *

inputFiles= "../training_data/res-4-t-*-b-b-cpl/globalPolicyCommittedInsts*.txt"
testFiles= "../test_data/res-4-t-*-b-b-cpl/globalPolicyCommittedInsts*.txt"
input_data = latency_no_cpl
target_data = ['Measured Al. Mem. Lat']
performance_target = ['Measured Alone IPC']
dataSet = 'all'
alteredStall = False

batch_selection = ['-7-','-8-','-9-']

new_training_set = ['-0-b','-1-b','-2-b','-3-b','-4-b','-5-b','-6-b']
new_test_set = ['-7-b','-8-b','-9-b']

def setDataSet():
    global dataSet
    try:
        set_arg = sys.argv[1]
        if set_arg == 'j':
            dataSet = 'j'
            return
        if set_arg == 'p':
            dataSet = 'p'
            return
        if set_arg == 'b':
            dataSet = 'b'
            return
        if set_arg == 'n':
            dataSet = 'n'
            return
        if set_arg == 'a':
            dataSet = 'a'
        else:
            return
    except:
        print("WARNING: Trainingset not provided as first argument, using 'all'")
        return
    
def setFeatureSet(dataset, features):
    global input_data
    if dataset == 'lat':
        if features == 'r':
            input_data = latency_no_atd_cpl
        else:
            input_data = latency_no_cpl        
    elif dataset == 'stall':
        if features == 'r':
            input_data = stall_no_atd_cpl
        else:
            input_data = stall_no_cpl
    elif dataset == 'ipc':
        if features == 'r':
            input_data = ipc_no_atd_cpl
        else:
            input_data = ipc_no_cpl
    elif dataset == 'stall-a':
        if features == 'r':
            input_data = stall_no_atd_cpl
        else:
            input_data = stall_no_cpl
    return

def setTarget(combined):
    global target_data
    global performance_target
    global alteredStall
    try:
        metric = sys.argv[2]
        features = sys.argv[3]
    except:
        sys.stderr.write("Could not read second and third argument. target data second arg (ipc, stall, lat). Feature set as second arg (a (all) , r (reduced, no ATD)")
        sys.exit(-1)
    if combined:
        target_data = ['Measured Al. Mem. Lat']
        if metric == 'stall':
            performance_target = ['Measured Sh/Pr Mem Stalls']
        elif metric == 'ipc':
            performance_target = ['Measured Alone IPC']
        else:
            performance_target = ['Measured Alone IPC']
        metric = 'lat'
    else:
        if metric == 'lat':
            target_data = ['Measured Al. Mem. Lat']
        elif metric == 'stall':
            target_data = ['Measured Sh/Pr Mem Stalls']
        elif metric == 'ipc':
            target_data = ['Measured Alone IPC']
        elif metric == 'stall-a':
            target_data = ['Measured Alone IPC']
            alteredStall = True
        else:
            print("Did not recodatasetgnize target ([lat, stall, ipc]), using lat (Measured Al. Mem. Lat)")
            target_data = ['Measured Alone IPC']
    setFeatureSet(metric, features)

def getMaxLeafNodes():
    try:
        nodes = sys.argv[4]
        return int(nodes)
    except:
        print("Did not provide max leaf nodes as fourth argument")
        sys.exit(-1)

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
            'Hidden Loads',
            'Table CPL',
            'Graph CPL',
            'Num Write Stalls',
            'Average Shared Latency',
            'Average Shared Private Memsys Latency',
            'Shared IPC',
            'Estimated Private Latency',
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
            'Shared Store Lat',
            'Estimated Alone Store Lat',
            'Measured Al. Mem. Lat',
            'Measured Sh/Pr Mem Stalls',
            'Measured Alone IPC',
            'Alone Write Stall Cycles',
            'Alone Private Blocked Stall Cycles',
            'Alone Empty ROB Stall Cycles']]
    return x

def rms(y_true, y_pred):
    return sqrt(mean_squared_error(y_true, y_pred))

def getTrainingData(combined=False):
    setDataSet()
    setTarget(combined)
    aggregated_data = pd.DataFrame()
    largest_ipc = 0.0
    for filename in sorted(glob.glob(inputFiles)):
        if skipJobTraining(filename):
            continue
        data = readFile(filename)
        aggregated_data = aggregated_data.append(data)
    if dataSet == 'p':
        aggregated_data = aggregated_data[aggregated_data.index % 4 != 0]
    x = aggregated_data[input_data]
    y = aggregated_data[target_data]
    if alteredStall:
        y = aggregated_data['Measured Sh/Pr Mem Stalls'].astype('float64').add(
            aggregated_data['Alone Write Stall Cycles'].astype('float64')).add(
            aggregated_data['Alone Private Blocked Stall Cycles'].astype('float64')).add(
            aggregated_data['Alone Empty ROB Stall Cycles'].astype('float64'))
        y = y.rename("Stall-a")
        y = pd.DataFrame(y)
    return x, y

def getAllData():
    aggregated_data = pd.DataFrame()
    for filename in sorted(glob.glob(inputFiles)):
        if skipJobTraining(filename):
            continue
        data = readFile(filename)
        aggregated_data = aggregated_data.append(data)
    if dataSet == 'p':
        aggregated_data = aggregated_data[aggregated_data.index % 4 != 0]
    return aggregated_data

def skipJobTraining(filename):
    if dataSet == 'j' and 'CommittedInsts3' in filename:
        return True
    if dataSet == 'b' and any(job in filename for job in batch_selection):
        return True
    if dataSet == 'n' and not any(job in filename for job in new_training_set):
        return True
    return False

def skipJobTesting(filename):
    if dataSet == 'j' and 'CommittedInsts3' not in filename:
        return True
    if dataSet == 'b' and not any(job in filename for job in batch_selection):
        return True
    if dataSet == 'n' and not any(job in filename for job in new_test_set):
        return True
    return False

def getTestData(filename):
    data = readFile(filename)
    if dataSet == 'p':
        data = data[data.index % 4 == 0]
    x = data[input_data]
    y = data[target_data]
    if alteredStall:
        y = data['Measured Sh/Pr Mem Stalls'].astype('float64').add(
            data['Alone Write Stall Cycles'].astype('float64')).add(
            data['Alone Private Blocked Stall Cycles'].astype('float64')).add(
            data['Alone Empty ROB Stall Cycles'].astype('float64'))
        y = y.rename("Stall-a")
    return x,y

def printJobAverage(filename, error):
    job = re.search('res-4-(.+?)-b-b', filename)
    core_no = re.search('CommittedInsts(.+?).txt', filename)
    print(job.group(1) + "-" + core_no.group(1) + " " + str(error))
    return

def testData(model):
    acc_count = 0
    accumulator = 0
    for filename in sorted(glob.glob(testFiles)):
        if skipJobTesting(filename):
            continue
        acc_count += 1
        x, y = getTestData(filename)
        prediction = model.predict(x)
        error = rms(prediction, y)
        accumulator += error
        printJobAverage(filename, error)
    
    #print("Average RMS error for jobs: ", accumulator / acc_count)
    #print(accumulator / acc_count)
    
def stallToIPC(data, total_stall_estimate, ratio, store_ratio):
    compute_cycles = data['Compute Cycles'].astype('float64')
    pr_blocked_stalls = data['Private Blocked Stall Cycles'].astype('float64').mul(ratio)
    mem_ind_stalls = data['Memory Independent Stalls'].astype('float64')
    empty_rob_stalls = data['Empty ROB Stall Cycles'].astype('float64').mul(ratio)
    write_stalls = data['Write Stall Cycles'].astype('float64').mul(store_ratio)
    cum_com_inst = data['Cummulative Committed Instructions'].astype('float64')
    com_inst = [cum_com_inst[0]]
    for i in range(1,len(cum_com_inst)):
        com_inst.append(cum_com_inst[i] - cum_com_inst[i - 1])
    com_inst = pd.Series(com_inst)
    total_cycles = compute_cycles.add(pr_blocked_stalls).add(mem_ind_stalls).add(empty_rob_stalls).add(total_stall_estimate).add(write_stalls)
    ipc = com_inst.div(total_cycles)
    return ipc

def evaluateMLP(latency_predictions, filename):
    data = readFile(filename)
    y = data[performance_target]
    predictions_df = pd.Series(latency_predictions).astype('float64')
    #uncomment for DIEF estimates
    #predictions_df = data['Estimated Private Latency'].astype('float64')
    private_stalls = data['Private Stall Cycles'].astype('float64')
    shared_stalls = data['Stall Cycles'].astype('float64')
    avg_sh_latency = data['Average Shared Latency'].astype('float64')
    avg_pr_latency = data['Average Shared Private Memsys Latency'].astype('float64')
    sh_latency = avg_sh_latency.add(avg_pr_latency)
    pr_latency = predictions_df.add(avg_pr_latency)
    shared_stall_estimate = shared_stalls.div(sh_latency).mul(pr_latency)
    shared_stall_estimate = shared_stall_estimate.replace([np.inf, -np.inf], np.nan)
    shared_stall_estimate = shared_stall_estimate.fillna(0)
    total_stall_estimate = private_stalls.add(shared_stall_estimate)
    if performance_target == ['Measured Alone IPC']:
        ratio = pr_latency.div(sh_latency)
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
        ratio = ratio.fillna(0)
        shared_store_lat = data['Shared Store Lat'].astype('float64')
        pr_store_lat = data['Estimated Alone Store Lat'].astype('float64')
        store_ratio = pr_store_lat.div(shared_store_lat)
        store_ratio = store_ratio.replace([np.inf, -np.inf], np.nan)
        store_ratio = store_ratio.fillna(0)
        target_prediction = stallToIPC(data, total_stall_estimate, ratio, store_ratio)
    else:
        target_prediction = total_stall_estimate
    error = rms(target_prediction, y)
    return error
    
def testMLP(model):
    acc_count = 0
    accumulator = 0
    for filename in sorted(glob.glob(testFiles)):
        if skipJobTesting(filename):
            continue
        acc_count += 1
        x, y = getTestData(filename)
        latency_predictions = model.predict(x)
        error = evaluateMLP(latency_predictions, filename)
        accumulator += error
        #printJobAverage(filename, error)
    
    #print("\nAverage RMS error for jobs: ", accumulator / acc_count)
    print(accumulator / acc_count)
    
# Filter out part of GDP evaluation to be used by Extended Tree Regression
def evaluateGDP(latency_predictions, filename):
    data = readFile(filename)
    y = data[performance_target]
    private_stalls = data['Private Stall Cycles'].astype('float64')
    avg_pr_latency = data['Average Shared Private Memsys Latency'].astype('float64')
    cpl = data['Table CPL'].astype('float64')
    predictions_df = pd.Series(latency_predictions).astype('float64')
    #uncomment for DIEF estimates
    #predictions_df = data['Estimated Private Latency'].astype('float64')
    pr_latency = predictions_df.add(avg_pr_latency)
    shared_stall_estimate = cpl.mul(pr_latency)
    total_stall_estimate = private_stalls.add(shared_stall_estimate)
    if performance_target == ['Measured Alone IPC']:
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
    else:
        target_prediction = total_stall_estimate
    error = rms(target_prediction, y)
    return error
    
def testGDP(model):
    acc_count = 0
    accumulator = 0
    for filename in sorted(glob.glob(testFiles)):
        if skipJobTesting(filename):
            continue
        acc_count += 1
        x, y = getTestData(filename)
        latency_predictions = model.predict(x)
        error = evaluateGDP(latency_predictions, filename)
        accumulator += error
        printJobAverage(filename, error)
    
    #print("\nAverage RMS error for jobs: ", accumulator / acc_count)
    #print(accumulator / acc_count)

def printModelError(model, data, target):
    print("\nAverage RMS error for data points: ", rms(model.predict(data), target))
    print("Trained using dataset: ", dataSet)
    
def exportTree(tm):
    dot_data = tree.export_graphviz(tm, out_file=None, 
                                    feature_names=input_data,
                                    class_names=target_data,
                                    rounded=True,
                                    filled=True,
                                    special_characters=True)
    graph = graphviz.Source(dot_data)
    graph.render("tree")

def printNode(index, connections, evaluations, intendation, lm, input_mapping):
    if "mse" in evaluations[index]:
        print(intendation, "aloneIPCEstimate = 0.0")
        for i in range(len(input_mapping)):
            print(intendation, "+", cpp_mapping[input_mapping[i]], "*", end=" ")
            number = float(lm[index].coef_[0][i])
            output = f"{number:.20f}"
            print(output)
        print(intendation, "+", float(lm[index].intercept_[0]), ";")
    else:
        first = True
        left_child = None
        right_child = None
        for i in range(1,len(connections)+1):
            if first and index == connections[i]:
                left_child = i
                first = False
            elif index == connections[i]:
                right_child = i
        metric = evaluations[index].split("<=")[0].rstrip()
        comparison = "<=" + evaluations[index].split("<=")[1]
        print(intendation, "if (", cpp_mapping[metric], comparison, ") {")
        printNode(left_child, connections, evaluations, intendation + "    ", lm, input_mapping)
        print(intendation, "} else {")
        printNode(right_child, connections, evaluations, intendation + "    ", lm, input_mapping)
        print(intendation, "}")
    
def printCpp(tm, lm, input_mapping):
    print("C++ model:")
    data = tree.export_graphviz(tm, out_file=None, 
                                    feature_names=input_data)
    data = data.split("\n")
    connections = {}
    for point in data[2:]:
        if "->" in point:
            test = point.replace(" ","")
            test = test.replace(";", "")
            test = re.sub("\[.*?\]", "", test)
            test = test.split("->")
            child = int(test[1])
            parent = int(test[0])
            connections[child] = parent
            print(parent , "to" , child)
    print(connections)
    evaluations = {}
    for point in data[2:]:
        if "->" in point:
            continue
        parts = point.split(" ")
        metric = point.split("label=\"")
        try:
            index = int(parts[0].replace(" ",""))
            metric = metric[1]
            metric = metric.split("\\nmse")[0]
            evaluations[index] = metric
        except:
            continue
    for index in range(len(evaluations)):
        print(index, evaluations[index])
        first = True
        for connection in connections.keys():
            if index == connections[connection]:
                if first:
                    first = False
                    print("IF", end=" ")
                else:
                    print("ELSE", end=" ")
                print(index, "to", connection)
    printNode(0, connections, evaluations, "", lm, input_mapping)
    
    
    