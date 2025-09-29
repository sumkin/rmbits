import glob
import sys
from StateMachine import *

OUTPUT_FILE_NAME = 'output.txt'

if 2 != len(sys.argv):
    exit('Wrong number of arguments...')

file_out = sys.argv[1]

fpout_leg = open('leg_' + file_out, 'w')
fpout_seg = open('seg_' + file_out, 'w')

def process_leg(fname, fpout):
    fp = open(fname,'r')
    sm = StateMachine()
    for line in fp:
        ret = sm.move(line)
        if FLUSH == ret:
            for strng in sm.get_leg_str():
                fpout.write(strng + '\n')
            sm.move(line) 
    for strng in sm.get_leg_str():
        fpout.write(strng + '\n')
    fp.close()

def process_seg(fname, fpout):
    fp = open(fname,'r')
    sm = StateMachine()
    for line in fp: 
        ret = sm.move(line)
        if FLUSH == ret:
            for strng in sm.get_seg_str(): 
                fpout.write(strng + '\n')
            sm.move(line)  
    for strng in sm.get_seg_str():
        fpout.write(strng + '\n')
    fp.close()


for fname in glob.glob('*.LEG'):
    process_leg(fname, fpout_leg)
fpout_leg.close()

for fname in glob.glob('*.SEG'):
    process_seg(fname, fpout_seg)

fpout_leg.close()
fpout_seg.close()




