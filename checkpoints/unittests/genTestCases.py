#!/usr/bin/python

def main():
    
    for i in range(1,41):
        if i < 10:
            wlname = "fair0"+str(i)
        else:
            wlname = "fair"+str(i)
            
        for simpoint in range(3):
            print "def test"+wlname+"sp"+str(simpoint)+"(self):"
            print "\tself.runWorkload('"+wlname+"',"+str(simpoint)+")"
            print
    

if __name__ == "__main__":
    main()