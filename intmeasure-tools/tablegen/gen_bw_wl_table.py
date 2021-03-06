
import bw_workloads

COLS = 4
NAME = "bw_workloads.tex"

bw_intensive = ['bw04', 'bw07', 'bw10', 'bw11', 'bw15', 'bw16', 'bw18', 'bw23', 'bw31', 'bw32', 'bw37', 'bw40']

header = """
\\begin{table}[t]

% Autogenerated workloadfile, do not edit!

\\caption{Special Multiprogrammed Workloads}
\\label{tab:special_workloads}
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


bms_per_row = len(bw_workloads.bw_workloads[4]) / COLS
rowdata = {}

for num in bw_workloads.bw_workloads[4]:
    wl = bw_workloads.bw_workloads[4][num][0]
    rowindex = (num-1) % bms_per_row
    if rowindex not in rowdata:
        rowdata[rowindex] = []
    rowdata[rowindex].append((num, wl))


for rowindex in rowdata:
    row = rowdata[rowindex]
    cnt = 0
    for id, bms in row:
        if id < 10:
            name = "bw0"+str(id)            
        else:
            name = "bw"+str(id)
            
        if name in bw_intensive:
            outfile.write("\\textbf{")
        outfile.write(name)
        if name in bw_intensive:
            outfile.write("}")


        outfile.write(" & ")
        if name in bw_intensive:
            outfile.write("\\textbf{")
        outfile.write(bms[0])
        for bm in bms[1:]:
            outfile.write(", "+bm)
        if name in bw_intensive:
            outfile.write("}")
        
        if cnt != len(row)-1:
            outfile.write(" & \n")
        cnt = cnt + 1
    outfile.write("\n\\tabularnewline\n")
    outfile.write("\\hline\n")

outfile.write(footer)
outfile.flush()
outfile.close()

