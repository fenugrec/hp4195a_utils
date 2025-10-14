#!/usr/bin/env python

# fenugrec 2025
# save a screenshot of HP 4195A

import pyvisa
import argparse
import sys

parser = argparse.ArgumentParser(description="HP 4195A screenshot tool")
parser.add_argument('-r', '--res', help='optional, full VISA resource string like TCPIP::x.y.z.w::5025::SOCKET')
parser.add_argument('-f', '--file', required=True, type=argparse.FileType('w'), help='output filename')
args = parser.parse_args(sys.argv[1:])

if not args.res:
    resource = 'GPIB0::17::INSTR'
else:
    resource=args.res

rfile=args.file

rm = pyvisa.ResourceManager()
h4 = rm.open_resource(resource)

# test 'ID?' query
idstring = h4.query('ID?')
if not idstring.startswith('HP4195'):
    print("ID query doesn't match HP4195 ?")
    exit


res = h4
res.write('CPYM1')
res.write('PLTF1')
header=res.query('SENDPS') # only for CPYM1 !
pltdata=res.query('COPY')
rfile.write(header + pltdata)


# try to set extension automagically based on contents
def save_scrn(imgdata, basename=None):
    if not basename:
        basename = time.strftime('%Y%m%d_%H%M%S')
    if imgdata.startswith(b'%!PS'):
        filename = basename + '.eps'
    elif imgdata.startswith(b'\x0a\x05\x01\x08'):
        filename = basename + '.pcx'
    else:
        filename = basename + '.plt'

    with open(filename,"wb") as f:
        f.write(imgdata)

