#!/usr/bin/python

import unittest

class TestPageSerialization(unittest.TestCase):


    def testPageSerialization(self):
        prefilename = "pre-serialize-pages.txt"
        postfilename = "post-unserialize-pages.txt"
        endmarker = "--- end of file ---"
        
        prefile = open(prefilename)
        postfile = open(postfilename)

        linenum = 0
        for preline in prefile:
            preline = preline.strip()
            postline = postfile.readline().strip()
            
            if preline == endmarker:
                self.assertEqual(postline, endmarker)
                continue
            
            pretokens = preline.split(";")
            posttokens = postline.split(";")

            self.assertEqual(len(pretokens), len(posttokens))

            for i in range(len(pretokens)):
                self.assertEqual(pretokens[i], posttokens[i])
                
            if linenum % 100 == 0:
                print str(linenum)+" lines checked successfully"
            linenum += 1

        prefile.close()
        postfile.close()

if __name__ == "__main__":
    unittest.main()