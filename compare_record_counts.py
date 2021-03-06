#!/usr/local/bin/python3

''' # ---

compare_record_counts.py

Compares two files' full of csv-formatted lists of record counts -- files
generated by mysql_record_count.py, for example. This program generates a file
giving a list of tables with changes in the counts of their records and the
number of records added or deleted.

''' # ---


import re, os, sys, time, io

filePathA = ''
filePathB = ''


def cleanPath( pathIn ):
    sep = os.path.sep
    if sep == '\\':
        sep = '\\\\'
    newPath = re.sub( r'[\\/]', sep, pathIn )
    return newPath


def loadDict( myPath, myDict ):
    with open( myPath, encoding='utf8' ) as myFile:
        for line in myFile:
            (a, b) = line.split(",")
            myDict[a] = b.rstrip()
    return myDict


quitPattern = re.compile( r'^(quit|q|stop|exit)$' )


# Get one input file path
print()
while not os.path.isfile(filePathA):
    print( 'Path to input file 1:' )
    filePathA = cleanPath( input() )
    if quitPattern.search( filePathA.lower() ):
        print( 'exiting' )
        sys.exit()
    if not os.path.isfile( filePathA ):
        print( '\ninput file ' + filePathA + ' not found\n' )


# Get the other input file path
print()
while not os.path.isfile(filePathB):
    print( 'Path to input file 2:' )
    filePathB = cleanPath( input() )
    if quitPattern.search( filePathB.lower() ):
        print( 'exiting' )
        sys.exit()
    if not os.path.isfile( filePathB ):
        print( '\ninput file ' + filePathB + ' not found\n' )

dictA = {}
dictB = {}
diffs = {}

loadDict( filePathA, dictA )
loadDict( filePathB, dictB )

for (k,v) in dictA.items():
    if dictB[k] != v:
        if dictB[k] > v:
            diffs[k] = '+' + str(int(dictB[k]) - int(v))
        else:
            diffs[k] = '-' + str(int(v) - int(dictB[k]))


baseA = os.path.splitext(os.path.basename(filePathA))[0]
baseB = os.path.splitext(os.path.basename(filePathB))[0]

with open( 'compare____' + baseA + '____' + baseB + '.log', 'w' ) as outFile:
    for (k,v) in diffs.items():
        outFile.write( k.ljust(32) + v[0] + v[1:].rjust(6) + '\n' )
print()



# the end
# ---

