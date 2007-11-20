
import popen2
import re
import os

def writeFile(benchmark, suffix,ic, ylabel, maxtick, maxread, input):
    scriptfile = open(benchmark+suffix+".g", "w")
    scriptfile.write("set title \""+benchmark+" Communication Behaviour - "+ic+"\"\n")
    scriptfile.write("set xlabel \"Million Clock Cycles\"\n")
    scriptfile.write("set ylabel \"Number of "+ylabel+" per 250000 Clock Cycles\"\n")
    scriptfile.write("set xr[0:"+str(maxtick)+"]\n");
    scriptfile.write("set yr[0:"+str(maxread)+"]\n");

    scriptfile.write("set key outside below\n")

    scriptfile.write("set terminal postscript eps color enhanced 18\n")
    scriptfile.write("set output \""+benchmark+suffix+".eps\"\n")
  
    scriptfile.write("plot \""+input+"\" using 1:2 title \'Data Sends\' with lines, \\\n")
    scriptfile.write("\""+input+"\" using 1:3 title \'Instruction Sends\' with lines, \\\n")
    scriptfile.write("\""+input+"\" using 1:4 title \'Coherence Sends\' with lines\n")

    scriptfile.flush()
    scriptfile.close()

    res = popen2.popen3("gnuplot "+benchmark+suffix+".g")
    text = res[0].read()

    res = popen2.popen3("epstopdf "+benchmark+suffix+".eps")
    text = res[0].read()

import pbsconfig

nps = [2,4,8]

results = {}

for np in nps:
    for benchmark in pbsconfig.benchmarks:
        for protocol in pbsconfig.protocols:
            for interconnect in pbsconfig.interconnects:
                resID = pbsconfig.get_unique_id(np, benchmark, protocol, interconnect)

                print "Processing experiment " + resID

                os.chdir(resID)

                statsfile = open("interconnectSendProfile.txt")

                gpReadable = open("interconnectSendProfile_gpRead.txt", 'w')

                first = True

                for line in statsfile.readlines():
                    if first:
                        fields = line.split(';')
                        for field in fields:
                            gpReadable.write(field.strip().ljust(30))
                        first = False
              
                    else:
                        fields = line.split(';')
                        gpReadable.write(str(int(fields[0].strip())/1000000).ljust(30))
                        for field in fields[1:]:
                            gpReadable.write(field.strip().ljust(30))
                    gpReadable.write("\n")

                gpReadable.flush()
                gpReadable.close()
      
                statsfile.close()

                statsfile = open("interconnectSendProfile.txt")
                maxtick = 0
                maxy = 0
                for line in statsfile.readlines()[1:]:
                    fields = line.split(';')
                    if(int(fields[0]) > maxtick):
                        maxtick = int(fields[0]);

                    for f in fields[1:]:
                        if int(f) > maxy:
                            maxy = int(f)

                maxtick = maxtick / 1000000

                offset = 50
                if maxtick < 200:
                    offset = 10

                if maxy >= 1000000:
                    maxy = maxy + 1000000
                elif maxy >= 100000:
                    maxy = maxy + 100000
                else:
                    maxy = maxy + 10000
    
                writeFile(benchmark,
                          "_"+str(np)+"_"+interconnect,
                          interconnect,
                          "Interconnect Sends",
                          maxtick+offset,
                          maxy,
                          "interconnectSendProfile_gpRead.txt")

                os.chdir('..')



