#!/usr/bin/env python

from optparse import OptionParser

import shutil
import re
import subprocess
import sys
import os
import glob

benchmarks = [("400", "perlbench"),
              ("401", "bzip2")
              ("403", "gcc"),
              ("429", "mcf"),
              ("445", "gobmk"),
              ("456", "hmmer"),
              ("458", "sjeng"),
              ("462", "libquantum"),
              ("464", "h264ref"),
              ("471", "omnetpp"),
              ("473", "astar"),
              ("483", "xalancbmk"),
              ("999", "specrand"),
              ("410", "bwaves"),
              ("416", "gamess"),
              ("433", "milc"),
              ("434", "zeusmp"),
              ("435", "gromacs"),
              ("436", "cactusADM"),
              ("437", "leslie3d"),
              ("444", "namd"),
              ("447", "dealII"),
              ("450", "soplex"),
              ("453", "povray"),
              ("454", "calculix"),
              ("459", "GemsFDTD"),
              ("465", "tonto"),
              ("470", "lbm"),
              ("481", "wrf"),
              ("482", "sphinx3")]

def parseArgs():
    parser = OptionParser(usage="buildSpec2006.py [options] SPECDIR")

    parser.add_option("--copy", action="store_true", dest="copy", default=False, help="Only copy files, do not build")
    parser.add_option("--benchmark", action="store", dest="benchmark", type="string", default="", help="Id.name for benchmark")
    parser.add_option("--verbose", action="store_true", dest="verbose", default=False, help="Verbose output")

    opts, args = parser.parse_args()

    if len(args) != 1:
        print "FATAL: SPEC root directory must be provided"
        print parser.usage
        sys.exit()
    
    specdir = args[0]
    
    return opts, specdir
    
def buildBenchmark(specroot, name):

    print "-- Building benchmark "+name 
    
    cmdarr = [specroot+"/bin/runspec",
             "--config=alpha.cfg",
             "--action=build",
             "--tune=base",
             "--rebuild",
             name]
    
    cmd = ""
    for c in cmdarr:
        cmd += c + " "

    pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout
    
    if(re.search("Build successes", pipe.read())):
        print "-- Success!"
        return True
    
    print "-- Failed!"
    return False

def recursiveCopy(srcDir, targetDir, verbose):
    print "-- Copying from "+srcDir+" to "+targetDir 
    for f in glob.glob(srcDir):
        print "-- Processing file "+f
        if os.path.isdir(f):
            dirname = os.path.basename(f)
            print "-- Processing directory "+f+", basename "+dirname
            if not os.path.exists(targetDir+"/"+dirname):
                print "-- Creating directory "+targetDir+"/"+dirname
                os.mkdir(targetDir+"/"+dirname)
            
            print "-- Calling copy on subdir "+f+"/* with target "+targetDir+"/"+dirname
            recursiveCopy(f+"/*", targetDir+"/"+dirname, verbose)
        else:
            print "-- "+f+" --> "+targetDir
            shutil.copy(f, targetDir)

def copyFiles(specroot, number, name, opts):
    
    basedir = specroot+"/benchspec/CPU2006/"+number+"."+name+"/"
    
    print "-- Copying binary"
    shutil.copy(basedir+"build/build_base_mar31a.0000/"+name, ".")
    
    target = "input/"+number+"."+name+"/"
    
    print "-- Copying from all directory"
    recursiveCopy(basedir+"/data/all/input/*", target, opts.verbose)

    print "-- Copying from ref directory"
    recursiveCopy(basedir+"/data/ref/input/*", target, opts.verbose)


#===============================================================================
# def initSpec(specroot):
#    print os.getcwd()
#    os.chdir(specroot)
#    print os.getcwd()
#    print ". ./shrc"
#    subprocess.call(["source", "shrc"])
#    os.chdir("-")
#    print os.getcwd()
##===============================================================================

def main():

    opts,specdir = parseArgs()
    
    #initSpec(specdir)
    
    if opts.benchmark != "":
        print "Processing benchmark "+opts.benchmark
        try:
            num,name = opts.benchmark.split(".")
        except:
            print "FATAL: Benchmarks must be on the for ID.NAME"
            sys.exit()
        
        if not opts.copy:
            buildBenchmark(specdir, name)
        copyFiles(specdir, num, name, opts)
    
    else:
        
        results = {}
        
        for num, name in benchmarks:
            print
            print "Processing "+num+"."+name
            print 
            
            buildres = False
            if not opts.copy:
                buildres = buildBenchmark(specdir, name)
            if buildres:
                copyFiles(specdir, num, name, opts)
            
            results[name] = buildres
        
        if results != {}:
            print 
            print "SPEC2006 Build Summary"
            print
            keys = results.keys()
            keys.sort()
            
            for k in keys:
                if results[k]:
                    print k.ljust(15)+" Build successfull"
                else:
                    print k.ljust(15)+" Build failed"
            print

if __name__ == '__main__':
    main()