
import sys
import deterministic_fw_wls as fair_workloads

try:
    np = int(sys.argv[1])

    COLS = int(sys.argv[2])
    NAME = "workloads-"+str(np)+".tex"

    printStart = int(sys.argv[3])
    printEnd = int(sys.argv[4])
    idoffset = int(sys.argv[3])
except:
    print "Usage: prog np cols wlstart wlend"
    sys.exit()

print "Generating table for workloads "+str(fair_workloads.workloads[np].keys()[printStart])+" to "+str(fair_workloads.workloads[np].keys()[printEnd-1])

header = """
\\begin{table}[t]

% Autogenerated workloadfile, do not edit!

\\caption{Randomly Generated Multiprogrammed Workloads}
\\label{tab:fairWorkloads}
"""

footer= """
\\end{tabularx}
\\end{table}
"""

outfile = open(NAME, 'w')
outfile.write(header)

outfile.write("\\begin{tabularx}{\\textwidth}{")
for i in range(COLS):
    outfile.write("|>{\\scriptsize}l>{\\scriptsize\\raggedright}X")
outfile.write("|}\n")

outfile.write("\\hline\n")
for i in range(COLS-1):
    outfile.write("\\textbf{ID} & \\textbf{Benchmarks} &")
outfile.write("\\textbf{ID} & \\textbf{Benchmarks} \\tabularnewline")
outfile.write("\\hline\n")

bms_per_row = len(fair_workloads.workloads[np].keys()[printStart:printEnd]) / COLS
rowdata = {}

for num in fair_workloads.workloads[np].keys()[printStart:printEnd]:
    wl = fair_workloads.workloads[np][num][0]
    rowindex = (num-1) % bms_per_row
    if rowindex not in rowdata:
        rowdata[rowindex] = []
    rowdata[rowindex].append((num, wl))


for rowindex in rowdata:
    row = rowdata[rowindex]
    cnt = 0
    for id, bms in row:
        name = str(id-idoffset)
        outfile.write(name)

        outfile.write(" & ")
        outfile.write(bms[0])
        for bm in bms[1:]:
            outfile.write(", "+bm)
                
        if cnt != len(row)-1:
            outfile.write(" & \n")
        cnt = cnt + 1
    outfile.write("\n\\tabularnewline\n")
    outfile.write("\\hline\n")

outfile.write(footer)
outfile.flush()
outfile.close()

