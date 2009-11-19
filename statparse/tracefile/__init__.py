
def isInt(valStr):
    try:
        int(valStr)
        return True
    except ValueError:
        return False
    
def isFloat(valStr):
    try:
        float(valStr)
        return True
    except ValueError:
        return False