
import sys

lines = sys.stdin.readlines()

for i in range(len(lines)-1):
    if lines[i] == '\n' and lines[i+1] == '\n':
        continue
    
    if lines[i+1] == '\n':
        print lines[i].strip()
        print
    else:
        print lines[i].strip().replace("\t",""),
    
