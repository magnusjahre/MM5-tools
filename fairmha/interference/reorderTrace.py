
import sys

if len(sys.argv) != 3:
    print "Usage: python -c 'import fairmha.reorderTrace' <filename> <seq num position>"
    sys.exit()
    
fname = sys.argv[1]
pos = int(sys.argv[2])
    
file = open(fname)

res = {}
for l in file.readlines()[1:]:
    data = l.split(";")
    key = int(data[pos])
    
    assert key not in res
    res[key] = l
    
keys = res.keys()
keys.sort()

for k in keys:
    print res[k],