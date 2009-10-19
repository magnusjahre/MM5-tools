
def stringToType(value):
    """ Converts a string to either an int, a float or leaves it as a string"""
    
    
    val = value
    success = False
    try:
        val = int(value)
        success = True
    except:
        pass
    
    if not success:
        try:
            val = float(value)
        except:
            pass
        
    return val