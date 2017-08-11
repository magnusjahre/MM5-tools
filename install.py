#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import re
import subprocess

from optparse import OptionParser

def parseArgs():
    program_name = os.path.basename(sys.argv[0])
    program_usage = program_name+" [options] install-path"

    # setup option parser
    parser = OptionParser(usage=program_usage)
    parser.add_option("--dry-run", dest="dryrun", action="store_true", default=False, help="Do not link files")

    # process options
    opts, args = parser.parse_args()

    if len(args) != 1:
        print "Command line error, usage: "+program_usage
        sys.exit(-1)

    return opts, args[0]

def isMainPythonFile(fname):
    f = open(fname)
    d = f.read()
    return re.search('if __name__ == ["\']__main__["\']:', d)

def installFile(filepath, dest, opts):
    fullpath = os.path.join(os.getcwd(), filepath)
    print "Creating link to", fullpath, "in directory", dest
    if not opts.dryrun:
        subprocess.call(["ln", "-s", "-f", fullpath, dest])

def main():
    opts, installpath = parseArgs()
    
    for dirname, subdirlist, files in os.walk("."):
        if not re.search("git", dirname):
            for f in files:
                root, ext = os.path.splitext(f)
                path = os.path.join(dirname, f)
                if ext == ".py" and isMainPythonFile(path):
                    installFile(path, installpath, opts)

if __name__ == "__main__":
    sys.exit(main())