#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Thermal Rule POS by @paulrickards June 2, 2019
# Tested with an Epson TM-T88III thermal POS printer
# connected with serial and TCP to serial adapter.
#
# Typical usage for serial (adjust port and baud below)
# ./thermalrule.py printer=true rule=126 lines=60 interface=serial
#
# Requires Python-ESCPOS. Install with
# pip install python-escpos

import sys
import time
import random
import datetime
from escpos.printer import Serial, Network

host         = 'micros.local'
tcpport      = 6400
port         = '/dev/tty.usbserial-FT9AJ3YT'
baud         = 38400
printer      = False
linesperpage = 80
linelength   = 56 # font 'b'
rulenum      = 30
interface    = 'serial'
lf           = '\x0a' # '\n'
cr           = '\x0d' # '\r'
ret          = cr + lf

def output(txt, lf=False):
    global currentline
    if lf is True: txt += ret
    if printer: Epson._raw(txt)
    sys.stdout.write(txt)
    sys.stdout.flush()

# Adapted from https://gist.github.com/zmwangx/77c168e90b4321ee7eea
def rule30(rule=30):
    MAX_TIME = linelength+20
    HALF_SIZE = MAX_TIME
    indices = range(-HALF_SIZE, HALF_SIZE+1)

    # initial condition
    #cells = {i: '0' for i in indices} # all 0 start
    cells = {i: str(random.randint(0,1)) for i in indices} # random start
    cells[0] = '1'
    # padding on both ends
    cells[-HALF_SIZE-1] = '0'
    cells[ HALF_SIZE+1] = '0'
    
    c = "{0:08b}".format(rule)
    new_state = {"111": c[0], "110": c[1], "101": c[2], "100": c[3],
                 "011": c[4], "010": c[5], "001": c[6], "000": c[7]}

    for time in range(0, linesperpage):
        for i in indices:
            if i>20:
                if cells[i] == '1':
                    output('\xdb', False) # square block character
                else:
                    output(' ', False) # space
        output('', True)
        # evolve
        patterns = {i: cells[i-1] + cells[i] + cells[i+1] for i in indices}
        cells = {i: new_state[patterns[i]] for i in indices}
        cells[-HALF_SIZE-1] = '0'
        cells[ HALF_SIZE+1] = '0'

## Main
print 'Thermal Rule POS by @paulrickards Jun 2, 2019'
if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        if sys.argv[i].startswith('printer') or sys.argv[i].startswith('print'):
            a = sys.argv[i].split('=')
            if a[1] in ['true', 'True', 'yes', '1', 'on']:
                printer = True
                print 'Printer output on.'
        if sys.argv[i].startswith('rule'):
            a = sys.argv[i].split('=')
            rulenum = int(a[1])
            if rulenum > 255 or rulenum < 0:
                rulenum = 30
            print 'Rule number', rulenum
        if sys.argv[i].startswith('int'):
            a = sys.argv[i].split('=')
            if a[1].lower().startswith('wifi') or a[1].lower().startswith('tcp'):
                interface = 'tcp'
        if sys.argv[i].startswith('lines'):
            a = sys.argv[i].split('=')
            linesperpage = int(a[1])
            print 'Lines per page', linesperpage
else:
    print 'Usage: thermalrule.py printer=true/false rule=[0-255] lines=80 interface=tcp/serial'
    exit()

if printer:
    if interface == 'tcp':
        print 'Using TCP interface', host, tcpport
        Epson = Network(host=host, port=tcpport, timeout=60)
        time.sleep(2) # wait for network
    else:
        print 'Using serial interface', devfile, baud
        Epson = Serial(devfile=port, baudrate=baud, dsrdtr=True)
    ret = '\r\n'
else:
    ret = '\n'

Epson.image('rulemart.gif', impl='bitImageColumn')
Epson.set(font='a')
Epson.text('Rule  : ' + str(rulenum) + '\n')
Epson.text('Lines : ' + str(linesperpage) + '\n')
Epson.text(datetime.datetime.now().strftime('Date  : %Y/%m/%d %H:%M:%S\n'))
output('\x1b\x21\x01', lf=False) # font 'b', 56 chars wide
output('\x1b\x33\x20', lf=False) # line spacing
output(ret * 3, lf=False)
rule30(rule=rulenum)
output(ret * 3, lf=False)
Epson.barcode(code=datetime.datetime.now().strftime("%Y%m%d%H%M%S"), bc='CODE93', function_type='B')
output(ret * 2, lf=False)
Epson.set(align='center', font='a')
Epson.text('Thank you! Please rule again.')
Epson.set(align='left')
output(ret * 8, lf=True)
Epson.cut()

