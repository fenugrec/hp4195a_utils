#!/usr/bin/env python

# fenugrec 2025
# save a screenshot of HP 4195A

import pyvisa
import argparse
import sys

parser = argparse.ArgumentParser(description="HP 4195A screenshot tool")
parser.add_argument('-r', '--res', help='optional, full VISA resource string like TCPIP::x.y.z.w::5025::SOCKET')
parser.add_argument('-c', '--cmt', help='optional, plot top comment')
parser.add_argument('-f', '--file', required=True, help='output file basename (no extension)')
args = parser.parse_args(sys.argv[1:])

cmt = args.cmt
if not args.res:
    resource = 'GPIB0::17::INSTR'
else:
    resource=args.res

# don't go crazy with os.path.splitext, just check if .plt was mistakenly provided;
# don't break valid basenames like "test 1.5k" that happen to look like an extension
if args.file.endswith('.plt'):
    print("error, specify only a base filename with no extension")
    quit()

rfile=open(args.file + ".plt", 'w')

rm = pyvisa.ResourceManager()
h4 = rm.open_resource(resource)

# test 'ID?' query
idstring = h4.query('ID?')
if not idstring.startswith('HP4195'):
    print("ID query doesn't match HP4195 ?")
    exit


res = h4
CMT_MAXLEN = 26
if cmt:
    if not cmt.isascii():
        print("comment can only contain ascii chars !")
        quit()
    cmt = cmt.encode(encoding='ascii')
    if len(cmt) > CMT_MAXLEN:
        print(f"Warning ! max 26 chars for comment. Truncating to '{cmt}'")
        cmt = cmt[:CMT_MAXLEN+1]
    res.write(f'CMT"{cmt}"')
res.write('CPYM1')
res.write('PLTF1')
header=res.query('SENDPS') # only for CPYM1 !
pltdata=res.query('COPY')
rfile.write(header + pltdata)


