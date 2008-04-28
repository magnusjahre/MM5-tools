
IDLE = "idle"
ACTIVE = "active"
WRITTEN = "written"
READ = "read"
PRECHARGING = "precharging"

READ_CMD = "read [1]"
WRITE_CMD = "writeback [5]"
ACTIVATE_CMD = "Activate memory page [19]"
CLOSE_CMD = "Close memory page [18]"

def error(msg, tick):
    print msg+" @ "+str(tick)
    exit()

edges = {}
edges[IDLE+'->'+ACTIVE] = 0
edges[ACTIVE+'->'+WRITTEN] = 0
edges[ACTIVE+'->'+READ] = 0
edges[READ+'->'+WRITTEN] = 0
edges[READ+'->'+READ] = 0
edges[READ+'->'+IDLE] = 0
edges[WRITTEN+'->'+READ] = 0
edges[WRITTEN+'->'+WRITTEN] = 0
edges[WRITTEN+'->'+IDLE] = 0

def incEdge(fromState, toState, tick):
    key = fromState+"->"+toState
    if key not in edges:
        error("Transition does not exist", tick)
    edges[key] = edges[key] + 1
        

bankstate = []
idleAt = []
activeAt = []
readStartAt = []
writeStartAt = []
for i in range(0,8):
    bankstate.append([IDLE, 0])
    idleAt.append(0)
    activeAt.append(0)
    readStartAt.append(0)
    writeStartAt.append(0)

f = open("busAccessTrace.txt")
lines = f.readlines()

requests = []

RAS = 40
CAS = 40
dataTime = 40
prechargeTime = 40
minActiveToPrechTime = 120
readToPrecharge = 10
writeRecoveryLat = 60
minBankToBank = 30
oneBusCycle = 10
readToWrite = 60
writeToRead = 30

writeLatency = CAS-oneBusCycle

print
print "Verifying bus trace..."
print

for line in lines:
    
    data = line.strip().split(",")
    
    if data[6] == "Request":
        requests.append((data[1], data[0]))
    elif data[6] == "Send":

        if data[5] == ACTIVATE_CMD:
            assert bankstate[int(data[2])][0] == IDLE
            bankstate[int(data[2])] = [ACTIVE, data[3]]
            incEdge(IDLE, ACTIVE, data[0])

        elif data[5] == READ_CMD:
            state = bankstate[int(data[2])][0]  
            assert state == ACTIVE or state == READ or state == WRITTEN

            addr, tick = requests.pop(0)
            if(addr != data[1]):
                error("Wrong addr granted access is "+data[1]+" should be "+addr, data[0])

        elif data[5] == CLOSE_CMD:
            state = bankstate[int(data[2])][0]  
            assert state == READ or state == WRITTEN

        elif data[5] == WRITE_CMD:
            state = bankstate[int(data[2])][0]  
            assert state == ACTIVE or state == WRITTEN or state == READ

            addr, tick = requests.pop(0)
            if(addr != data[1]):
                error("Wrong addr granted access is "+data[1]+" should be "+addr, data[0])

        else:
            error("Unknown memory command (send): "+data[5], data[0])
        
    elif data[6] == "Latency":

        if data[5] == ACTIVATE_CMD:
            assert int(data[4]) == 0
            newActiveAt = 0
            if idleAt[int(data[2])] < int(data[0]):
                newActiveAt = int(data[0]) + RAS
            else:
                newActiveAt = idleAt[int(data[2])] + RAS
            
            max = 0
            for i in range(len(activeAt)):
                if i != int(data[2]):
                    if max < activeAt[i]:
                        max = activeAt[i]
            
            if (max + minBankToBank) > newActiveAt:
                error("Testing minimum bank to bank delay not implemented", data[0])

            activeAt[int(data[2])] = newActiveAt

        elif data[5] == READ_CMD:
            state = bankstate[int(data[2])]
            assert state[0] == ACTIVE or state[0] == READ or state[0] == WRITTEN
            
            startOffset = 0
            if activeAt[int(data[2])] > (int(data[0]) + RAS):                
                startOffset = activeAt[int(data[2])] - (int(data[0]) + RAS)
                assert state[0] == ACTIVE

            if state[0] == ACTIVE:
                lat = startOffset + RAS + CAS + dataTime
                readStartAt[int(data[2])] = activeAt[int(data[2])] + CAS
            elif state[0] == WRITTEN:

                newLat = writeToRead + CAS
                earliestStart = writeStartAt[int(data[2])] + dataTime

                if int(data[0]) < earliestStart + newLat:
                    lat = dataTime + (earliestStart + newLat - int(data[0]))
                else:
                    lat = dataTime

                readStartAt[int(data[2])] = int(data[0]) + lat - dataTime
            else:
                lat = dataTime
                readStartAt[int(data[2])] = readStartAt[int(data[2])] + dataTime 

            if(lat != int(data[4])):
                error("Read latency should be "+str(lat)+", is "+data[4], data[0])
            
            oldState = bankstate[int(data[2])][0]
            bankstate[int(data[2])][0] = READ
            incEdge(oldState, READ, data[0])

        elif data[5] == WRITE_CMD:
            state = bankstate[int(data[2])]  
            assert state[0] == ACTIVE or state[0] == WRITTEN or state[0] == READ
            
            startOffset = 0
            if activeAt[int(data[2])] > (int(data[0]) + RAS):
                startOffset = activeAt[int(data[2])] - (int(data[0]) + RAS)
                assert state[0] == ACTIVE

            if state[0] == ACTIVE:
                lat = startOffset + RAS + writeLatency + dataTime
                writeStartAt[int(data[2])] = activeAt[int(data[2])] + writeLatency

            elif state[0] == READ:
                newLat = readToWrite  + writeLatency
                offsetToRead = int(data[0]) - readStartAt[int(data[2])]
                
                if offsetToRead < newLat:
                    lat = dataTime + (newLat - offsetToRead)
                else:
                    lat = dataTime

                writeStartAt[int(data[2])] = int(data[0]) + lat - dataTime
            else:
                lat = dataTime
                writeStartAt[int(data[2])] = writeStartAt[int(data[2])] + dataTime

            if(lat != int(data[4])):
                error("Write latency should be "+str(lat)+", is "+data[4], data[0])

            oldState = bankstate[int(data[2])][0]
            bankstate[int(data[2])][0] = WRITTEN
            incEdge(oldState, WRITTEN, data[0])

        elif data[5] == CLOSE_CMD:
            state = bankstate[int(data[2])]
            assert state[0] == WRITTEN or state[0] == READ
            assert int(data[4]) == 0
            
            earliestFin = 0
            if state[0] == WRITTEN:
                earliestFin = writeStartAt[int(data[2])] + dataTime + writeRecoveryLat
            else:
                earliestStart = readStartAt[int(data[2])] + dataTime + readToPrecharge

            if earliestFin < (activeAt[int(data[2])] + minActiveToPrechTime):
                startTime = activeAt[int(data[2])] + minActiveToPrechTime
            else:
                startTime = earliestFin
            
            idleAt[int(data[2])] = startTime + prechargeTime
            
            oldState = state[0]
            state[0] = IDLE
            incEdge(oldState, state[0], data[0])
        else:
            error("Unknown memory command (latency): "+data[5], data[0])


    else:
        error("Unknown command", data[0])

print
print "Verify finished successfully"
print
print "Edges traversed:"
fullCoverage = True
keys = edges.keys()
keys.sort()
for k in keys:
    print k.ljust(20)+str(edges[k]).rjust(10)
    if edges[k] == 0:
        fullCoverage = False

print
if fullCoverage:
    print "All state machine edges have been covered!"
else:
    print "Warning: the test does not cover all state machine edges."
print
