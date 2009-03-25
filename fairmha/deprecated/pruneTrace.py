
import sys

filename = "adaptiveMHATrace_gpInput.txt"
outfile = "prunedMHATrace.txt"

file = open(filename)

outfile = open(outfile, "w")

first = True
last = []

for line in file.readlines():
    if first:
        outfile.write(line)
        first = False
    else:
        stuff = line.split()

        if last[1:] == stuff[1:]:
            print "Skipping "+str(stuff)
            continue

        if last != [] and int(last[0]) < int(stuff[0])-500000:
            print "Special print: "+str(last)
            outfile.write(str(int(stuff[0])-500000).ljust(30))
            for s in last[1:]:
                outfile.write(str(s).ljust(30))
            outfile.write("\n")


        print stuff

        outfile.write(str(stuff[0]).ljust(30))
        for s in stuff[1:]:
            outfile.write(str(s).ljust(30))
        outfile.write("\n")

        last = stuff


