
import sys
from optparse import OptionParser

def parseArgs():
    parser = OptionParser(usage="generateBBV.py")
    parser.add_option("-k", "--search-key", action="store", dest="searchkey", default=".*", help="Only include results that matches this key")
    return parser.parse_args()


def main():

    options,args = parseArgs()

    print "Hello World"



if __name__ == "__main__":
    sys.exit(main())


