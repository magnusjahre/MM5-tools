latency_no_cpl = ['Total Latency',
'Private LLC Writeback Estimate',
'Total Requests',
'Average Shared Latency',
'Total LLC Miss/WBs',
'Average Shared Private Memsys Latency',
'Private LLC Hit Estimate',
'Shared LLC Hits',
'Private LLC Access Estimate',
'Shared LLC Accesses',
'Num Shared Stores',
'Write Stall Cycles',
'Hidden Loads',
'Shared LLC Writebacks',
'Shared IPC',
'Compute Cycles',
'Num Write Stalls',
'Private Stall Cycles',
'Private Blocked Stall Cycles',
'Shared Store Lat',
'Empty ROB Stall Cycles',
'Stall Cycles',
'Memory Independent Stalls',
'LLC Miss/WBs',
'Shared+Priv Memsys Stalls']
latency_no_atd_cpl = ['Total Latency',
                  'Total Requests',
                  'Num Shared Stores',
                  'Shared Store Lat',
                  'Stall Cycles',
                  'Average Shared Private Memsys Latency',
                  'Private Blocked Stall Cycles',
                  'Shared LLC Writebacks',
                  'Average Shared Latency',
                  'Total LLC Miss/WBs',
                  'Shared LLC Accesses',
                  'Write Stall Cycles',
                  'Shared IPC',
                  'Compute Cycles',
                  'Memory Independent Stalls',
                  'LLC Miss/WBs',
                  'Num Write Stalls',
                  'Private Stall Cycles',
                  'Empty ROB Stall Cycles',
                  'Hidden Loads',
                  'Shared LLC Hits',
                  'Shared+Priv Memsys Stalls']
ipc_no_cpl = ['Shared IPC',
'Private LLC Writeback Estimate',
'Total Latency',
'Private Stall Cycles',
'Total LLC Miss/WBs',
'Compute Cycles',
'Memory Independent Stalls',
'Shared LLC Accesses',
'Private LLC Hit Estimate',
'Shared LLC Hits',
'Private LLC Access Estimate',
'Average Shared Private Memsys Latency',
'Shared Store Lat',
'Total Requests',
'Stall Cycles',
'Num Shared Stores',
'Shared LLC Writebacks',
'Write Stall Cycles',
'Hidden Loads',
'Private Blocked Stall Cycles',
'Average Shared Latency',
'Num Write Stalls',
'Empty ROB Stall Cycles',
'Shared+Priv Memsys Stalls',
'LLC Miss/WBs']
ipc_no_cpl_n = ['Shared IPC',
'Private LLC Writeback Estimate',
'Private Stall Cycles',
'Total Latency',
'Average Shared Latency',
'Compute Cycles',
'Memory Independent Stalls',
'Average Shared Private Memsys Latency',
'Shared LLC Accesses',
'Private LLC Hit Estimate',
'Shared LLC Hits',
'Private LLC Access Estimate',
'Total LLC Miss/WBs',
'Shared LLC Writebacks',
'Total Requests',
'Hidden Loads',
'Num Shared Stores',
'Shared Store Lat',
'Private Blocked Stall Cycles',
'Write Stall Cycles',
'Empty ROB Stall Cycles',
'Stall Cycles',
'Num Write Stalls',
'LLC Miss/WBs',
'Shared+Priv Memsys Stalls']
ipc_no_atd_cpl = ['Shared IPC',
'LLC Miss/WBs',
'Total Latency',
'Private Stall Cycles',
'Private Blocked Stall Cycles',
'Shared LLC Hits',
'Memory Independent Stalls',
'Compute Cycles',
'Total LLC Miss/WBs',
'Empty ROB Stall Cycles',
'Hidden Loads',
'Average Shared Latency',
'Total Requests',
'Num Shared Stores',
'Shared LLC Accesses',
'Shared Store Lat',
'Write Stall Cycles',
'Stall Cycles',
'Num Write Stalls',
'Average Shared Private Memsys Latency',
'Shared LLC Writebacks',
'Shared+Priv Memsys Stalls']

stall_no_cpl = ['Private LLC Writeback Estimate',
'Private Stall Cycles',
'Total Latency',
'Average Shared Latency',
'Stall Cycles',
'Total LLC Miss/WBs',
'Average Shared Private Memsys Latency',
'Shared IPC',
'Compute Cycles',
'LLC Miss/WBs',
'Shared LLC Writebacks',
'Total Requests',
'Private LLC Hit Estimate',
'Private LLC Access Estimate',
'Hidden Loads',
'Num Write Stalls',
'Shared LLC Accesses',
'Memory Independent Stalls',
'Write Stall Cycles',
'Shared Store Lat',
'Num Shared Stores',
'Private Blocked Stall Cycles',
'Empty ROB Stall Cycles',
'Shared+Priv Memsys Stalls',
'Shared LLC Hits']
stall_no_atd_cpl = ['Total Latency',
                    'Average Shared Latency',
                    'LLC Miss/WBs',
                    'Private Stall Cycles',
                    'Stall Cycles',
                    'Shared IPC',
                    'Total Requests',
                    'Shared LLC Writebacks',
                    'Total LLC Miss/WBs',
                    'Private Blocked Stall Cycles',
                    'Shared Store Lat',
                    'Average Shared Private Memsys Latency',
                    'Num Write Stalls',
                    'Compute Cycles',
                    'Hidden Loads',
                    'Empty ROB Stall Cycles',
                    'Shared LLC Accesses',
                    'Write Stall Cycles',
                    'Num Shared Stores',
                    'Memory Independent Stalls',
                    'Shared+Priv Memsys Stalls',
                    'Shared LLC Hits']

cpp_mapping = {
            'Cummulative Committed Instructions': 'comInstModelTraceCummulativeInst[cpuID]',
            'Total Cycles': 'cyclesInSample',
            'Stall Cycles': 'stallCycles',
            'Private Stall Cycles': 'privateStallCycles',
            'Shared+Priv Memsys Stalls': 'stallCycles + privateStallCycles',
            'Write Stall Cycles': 'writeStall',
            'Private Blocked Stall Cycles': 'privateBlockedStall',
            'Compute Cycles': 'commitCycles',
            'Memory Independent Stalls': 'memoryIndependentStallCycles',
            'Empty ROB Stall Cycles': 'emptyROBStallCycles',
            'Total Requests': 'reqs',
            'Total Latency': 'reqs*(avgSharedLat+avgPrivateMemsysLat)',
            'Hidden Loads': 'hiddenLoads',
            'Table CPL': 'ols.tableCPL',
            'Num Write Stalls': 'numWriteStalls',
            'Average Shared Latency': 'avgSharedLat',
            'Average Shared Private Memsys Latency': 'avgPrivateMemsysLat',
            'Shared IPC': 'sharedIPC',
            'Num Shared Stores': 'numStores',
            'Shared Store Lat': 'avgSharedStoreLat',
            'Private LLC Hit Estimate': 'privateLLCEstimates.hits',
            'Private LLC Access Estimate': 'privateLLCEstimates.accesses',
            'Private LLC Writeback Estimate': 'privateLLCEstimates.writebacks',
            'Shared LLC Hits': 'sharedLLCMeasurements.hits',
            'Shared LLC Accesses': 'sharedLLCMeasurements.accesses',
            'Shared LLC Writebacks': 'sharedLLCMeasurements.writebacks',
            'LLC Miss/WBs': '(sharedLLCMeasurements.accesses - sharedLLCMeasurements.hits + sharedLLCMeasurements.writebacks)',
            'Total LLC Miss/WBs': 'MANGLER'}

target_data = ['Measured Al. Mem. Lat']
dataSet = 'all'

batch_selection = ['-6-','-7-','-8-','-9-']

new_training_set = ['-0-b','-1-b','-2-b','-3-b','-4-b','-5-b','-6-b']
new_test_set = ['-7-b','-8-b','-9-b']