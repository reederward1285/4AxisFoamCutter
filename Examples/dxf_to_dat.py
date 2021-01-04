#!/usr/bin/env python

from fileinput import input

def printpoint(b):
  obj = dict(zip(b[0::2], b[1::2]))
  if obj['0'] == 'VERTEX':
    print '{},{},{}'.format(obj['10'], obj['20'], obj['30'])

print 'x,y,z'             # header line
buffer = ['0', 'fake']    # give first pass through loop something to process
for line in input():
  line = line.rstrip()
  if line == '0':         # we've started a new section, so
    printpoint(buffer)      # handle the captured section
    buffer = []             # and start a new one
  buffer.append(line)

printpoint(buffer)        # buffer left over from last pass through loop
