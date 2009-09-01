
def getCheckpointDirectory(np, memsys, bm, simpoint = -1):
    serializeBase = "cpt-"+str(np)+"-"+str(memsys)+"-"+str(bm)
    if simpoint != -1:
        return serializeBase+"-sp"+str(simpoint)
    return serializeBase+"-nosp"
