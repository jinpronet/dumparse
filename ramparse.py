#!/usr/bin/python

# Copyright (c) 2012-2013, The Linux Foundation. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 and
# only version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import sys
import os
import struct
import datetime
import array
import string
import bisect
import traceback
from print_out import *
from subprocess import *
from optparse import OptionParser
from optparse import OptionGroup
from struct import unpack
from ctypes import *
from optparse import *
from ramdump import *
from ramdump import *
import parser_util

#Please update version when something is changed!'
VERSION = '2.0'

def parse_ram_file(option, opt_str, value, parser) :
    a = getattr(parser.values,option.dest)
    if a is None:
        a = []
    temp = []
    for arg in parser.rargs:
        if arg[:2] == "--":
            break
        if arg[:1] == "-" and len(arg) > 1:
            break
        temp.append(arg)

    if len(temp) is not 3:
        raise OptionValueError("Ram files must be specified in 'name, start, end' format")

    a.append((temp[0],int(temp[1],16),int(temp[2],16)))
    setattr(parser.values,option.dest, a)

if __name__ == "__main__":
    usage = "usage: %prog [options to print]. Run with --help for more details"
    parser = OptionParser(usage)
    parser.add_option("", "--print-watchdog-time", action="store_true", dest="watchdog_time", help="Print watchdog timing information", default = False)
    parser.add_option("-e", "--ram-file", dest="ram_addr", help="List of ram files (name, start, end)", action="callback", callback=parse_ram_file)
    parser.add_option("-v", "--vmlinux", dest="vmlinux", help="vmlinux path")
    parser.add_option("-n", "--nm-path", dest="nm", help="nm path")
    parser.add_option("-g", "--gdb-path", dest="gdb", help="gdb path")
    parser.add_option("-a", "--auto-dump", dest="autodump", help="Auto find ram dumps from the path")
    parser.add_option("-o", "--outdir", dest="outdir", help="Output directory")
    parser.add_option("-s", "--t32launcher", action="store_true", dest="t32launcher", help="Create T32 simulator launcher", default=False)
    parser.add_option("-x", "--everything", action="store_true", dest="everything", help="Output everything (may be slow")
    parser.add_option("-f", "--output-file", dest="outfile", help="Name of file to save output")
    parser.add_option("", "--stdout", action="store_true", dest="stdout", help="Dump to stdout instead of the file")
    parser.add_option("", "--phys-offset", type="int", dest="phys_offset", help="use custom phys offset")
    parser.add_option("", "--force-hardware", type="int", dest="force_hardware", help="Force the hardware detection")
    parser.add_option("", "--force-version", type="int", dest="force_hardware_version", help="Force the hardware detection to a specific hardware version")
    parser.add_option("", "--parse-qdss", action="store_true", dest="qdss", help="Parse QDSS (deprecated)")

    for p in parser_util.get_parsers():
        parser.add_option(p.shortopt or "",
                          p.longopt,
                          dest=p.cls.__name__,
                          help=p.desc,
                          action="store_true")

    (options, args) = parser.parse_args()

    if options.outdir :
        if not os.path.exists(options.outdir) :
            print ("!!! Out directory does not exist. Create it first.")
            sys.exit(1)
    else :
        options.outdir = "."

    if options.outfile is None :
        # dmesg_TZ is a very non-descriptive name and should be changed sometime in the future
        options.outfile = "dmesg_TZ.txt"

    if not options.stdout :
        set_outfile(options.outdir+"/"+options.outfile)

    print_out_str ("Linux Ram Dump Parser Version %s" % VERSION)
    if options.vmlinux is None :
        print_out_str ("No vmlinux given. I can't proceed!")
        parser.print_usage()
        sys.exit(1)

    args = ""
    for arg in sys.argv:
      args = args + arg + " "

    print_out_str ("Arguments: {0}".format(args))

    system_type = parser_util.get_system_type()

    if not os.path.exists(options.vmlinux) :
        print_out_str ("{0} does not exist. Cannot proceed without vmlinux. Exiting...".format(options.vmlinux))
        sys.exit(1)
    else :
        print_out_str ("using vmlinx file {0}".format(options.vmlinux))

    if options.ram_addr is None and options.autodump is None :
        print_out_str ("Need one of --auto-dump or at least one --ram-file")
        sys.exit(1)

    if options.ram_addr is not None :
        for a in options.ram_addr :
            if os.path.exists(a[0]) :
                print_out_str ("Loading Ram file {0} from {1:x}--{2:x}".format(a[0],a[1],a[2]))
            else :
                print_out_str ("Ram file {0} does not exist. Exiting...".format(a[0]))
                sys.exit(1)

    if options.autodump is not None :
        if os.path.exists(options.autodump) :
            print_out_str ("Looking for Ram dumps in {0}".format(options.autodump))
        else :
            print_out_str ("Path {0} does not exist for Ram dumps. Exiting...".format(options.autodump))
            sys.exit(1)


    if not options.gdb :
        gdb_candidates = ['arm-none-eabi-gdb.exe',
                          'arm-none-linux-gnueabi-gdb',
                          'arm-eabi-gdb',
                          'arm-linux-androideabi-gdb']
        for c in gdb_candidates:
            gdb_path = parser_util.which(c)
            if gdb_path is not None:
                break

        if gdb_path is None:
            if system_type is 'Windows' :
                gdb_path = "\\\\freeze\\l4linux\\users\\vmulukut\\arm-none-eabi-gdb.exe"
            elif system_type is 'Linux':
                gdb_path = "arm-eabi-gdb"
                p = parser_util.which(gdb_path)
                if p is None:
                    gdb_path = "/pkg/asw/compilers/codesourcery/arm-2010q1/bin/arm-none-linux-gnueabi-gdb"

            elif system_type is 'Darwin':
                gdb_path = "arm-linux-androideabi-gdb"
            else :
                print_out_str ("This is not a recognized system type! Exiting...")
                sys.exit(1)
        print_out_str ("No gdb path given, using {0}".format(gdb_path))
    else :
        gdb_path = options.gdb
        print_out_str ("gdb path = "+gdb_path)

    if not options.nm :
        nm_candidates = ['arm-none-eabi-nm.exe',
                         'arm-none-linux-gnueabi-nm',
                         'arm-eabi-nm',
                         'arm-linux-androideabi-nm']
        for c in nm_candidates:
            nm_path = parser_util.which(c)
            if nm_path is not None:
                break

        if nm_path is None:
            if system_type is 'Windows' :
                nm_path =  "\\\\freeze\\l4linux\\users\\vmulukut\\arm-none-eabi-nm.exe"
            elif system_type is 'Linux' :
                nm_path = "arm-eabi-nm"
                p = parser_util.which(nm_path)
                if p is None:
                    nm_path = "/pkg/asw/compilers/codesourcery/arm-2010q1/bin/arm-none-linux-gnueabi-nm"
            elif system_type is 'Darwin':
                nm_path = "arm-linux-androideabi-nm"
            else :
                print_out_str ("This is not a recognized system type! Exiting...")
                sys.exit(1)
        print_out_str ("No nm path given, using {0}".format(nm_path))
    else :
        nm_path = options.nm
        print_out_str ("nm path + "+nm_path)

    dump = RamDump(options.vmlinux, nm_path, gdb_path, options.ram_addr,
                   options.autodump, options.phys_offset, options.outdir,
                   options.force_hardware, options.force_hardware_version)

    if not dump.print_command_line() :
        print_out_str ("!!! Error printing saved command line.")
        print_out_str ("!!! The vmlinux is probably wrong for the ramdumps")
        print_out_str ("!!! Exiting now...")
        sys.exit(1)

    if options.qdss :
        print_out_str("!!! --parse-qdss is now deprecated")
        print_out_str("!!! Please just use --parse-debug-image to get QDSS information")

    if options.watchdog_time :
        print_out_str ("\n--------- watchdog time -------")
        get_wdog_timing(dump)
        print_out_str ("---------- end watchdog time-----")

    if options.t32launcher or options.everything :
        dump.create_t32_launcher()

    for p in parser_util.get_parsers():
        # we called parser.add_option with dest=p.cls.__name__ above,
        # so if the user passed that option then `options' will have a
        # p.cls.__name__ attribute.
        if getattr(options, p.cls.__name__) or (options.everything and not p.optional):
            with print_out_section(p.cls.__name__):
                p.cls(dump).parse()
