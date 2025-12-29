#!/usr/bin/env python

# fenugrec 2025
# save a screenshot of HP 4195A
# if 'hp2xx' program is found, will invoke that to render the HPGL to a more friendly format.
#
# if running in looping mode, comment and output filename args are ignored

import pyvisa
import argparse
import sys
import shutil
import subprocess

######## configurable hp2xx invocation
hp2xx_args = ['-m', 'png', '-q', '-c651143']
hp2xx_bin = shutil.which('hp2xx')

def main():
    parser = argparse.ArgumentParser(description="HP 4195A screenshot tool")
    parser.add_argument('-i', action='store_true', help='run in looping interactive mode')
    parser.add_argument('-r', '--res', help='optional, full VISA resource string like TCPIP::x.y.z.w::5025::SOCKET')
    parser.add_argument('-c', '--cmt', help='optional, plot top comment')
    parser.add_argument('-f', '--file', help='output file basename (no extension)')
    args = parser.parse_args(sys.argv[1:])

    cmt = args.cmt
    if not args.res:
        resource = 'GPIB0::17::INSTR'
    else:
        resource=args.res

    rm = pyvisa.ResourceManager()
    hp_res = rm.open_resource(resource)

# test 'ID?' query
    idstring = hp_res.query('ID?')
    if not idstring.startswith('HP4195'):
        print("ID query doesn't match HP4195 ?")
        quit()

    if not args.i:
        #running in single shot mode, need filename
        if args.file is None:
            print("error, need filename if running non-interactively")
            quit()
        save_screenshot(hp_res, args.file, args.cmt)
    else:
        #loop
        if args.file:
            print("(note: filename arg is ignored in interactive mode")
        if args.cmt:
            print("(note: comment arg is ignored in interactive mode")
        print("Starting interactive mode. Input empty comment & file names to end.")
        while 1:
            print("*******************")
            cmt=input("Enter optional plot comment (max 26 chars)")
            fn_basic = cmt
            fn=input(f"filename, or press enter to use '{fn_basic}'")
            if (cmt =='') and (fn == ''):
                quit()
            if (fn == ''):
                fn = fn_basic
            save_screenshot(hp_res, fn, cmt)





#args : pyvisa resource, filename, optional comment
def save_screenshot(res, filename, cmt):
# don't go crazy with os.path.splitext, just check if .plt was mistakenly provided;
# don't break valid basenames like "test 1.5k" that happen to look like an extension
    if filename.endswith('.plt'):
        print("error, specify only a base filename with no extension")
        quit()

# TODO : warn if file exists before clobbering
    pltfilename = filename + ".plt"
    rfile=open(pltfilename, 'wb')

    CMT_MAXLEN = 26
    if cmt:
        if not cmt.isascii():
            print("comment can only contain ascii chars !")
            quit()
        if len(cmt) > CMT_MAXLEN:
            print(f"Warning ! max 26 chars for comment. Truncating to '{cmt}'")
            cmt = cmt[:CMT_MAXLEN+1]
        res.write(f'CMT"{cmt}"')
    res.write('CPYM1')
    res.write('PLTF1')
    res.write('SENDPS') # only for CPYM1 !
    header=res.read_raw()
    res.write('COPY')
    pltdata=res.read_raw()

    rfile.write(header)
    rfile.write(pltdata)
    rfile.close()

    if hp2xx_bin is None:
        print("optional hp2xx binary (conversion to raster image) not found")
    else:
#    hp2xx_cmd = f'{hp2xx_bin} "{pltfilename}" {hp2xx_args}'
        hp2xx_cmd = [hp2xx_bin, pltfilename, *hp2xx_args]
        print(f" running '{(hp2xx_cmd)}'")
        subprocess.run(hp2xx_cmd)

if __name__=="__main__":
   main()
