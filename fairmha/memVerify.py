
IDLE = "idle"
ACTIVE = "active"
WRITTEN = "written"
READ = "read"
PRECHARGING = "precharging"

READ_CMD = "read [1]"
WRITE_CMD = "writeback [1]"
ACTIVATE_CMD = "Activate memory page [19]"
CLOSE_CMD = "Close memory page [18]"

def error(msg, tick):
    print msg+" @ "+str(tick)
    exit()

bankstate = []
for i in range(0,8):
    bankstate.append((0, IDLE, 0))

f = open("busAccessTrace.txt")
lines = f.readlines()

requests = []

c = 0
for line in lines:
    
    data = line.strip().split(",")
    
    if data[6] == "Request":
        requests.append((data[1], data[0]))
    elif data[6] == "Send":

        if data[5] == ACTIVATE_CMD:
            assert bankstate[int(data[2])][1] == IDLE
            bankstate[int(data[2])] = (int(data[0])+40, ACTIVE, data[3])
        elif data[5] == READ_CMD:
            state = bankstate[int(data[2])][1]  
            assert state == ACTIVE or state == READ
            
        else:
            error("Unknown memory command (send): "+data[5], data[0])
            
        #addr, tick = requests.pop(0)

        
        #assert addr == data[1] 
        #error(sweet, data[0])

    elif data[6] == "Latency":

        if data[5] == ACTIVATE_CMD:
            assert int(data[4]) == 0
            assert int(data[0]) <= bankstate[int(data[2])][0]
            bankstate[int(data[2])] = int(data[0]), ACTIVE, data[3]

        else:
            error("Unknown memory command (latency): "+data[5], data[0])


    else:
        error("Unknown command", data[0])

    c = c +1
    if c > 10:
        exit()
