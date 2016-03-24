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
import re
import os
import struct
import datetime
import array
import string
import bisect
import traceback
from subprocess import *
from optparse import OptionParser
from optparse import OptionGroup
from struct import unpack
from ctypes import *
from tempfile import *
from print_out import *
from parser_util import register_parser, RamParser

#struct msm_rtb_layout {
#        unsigned char sentinel[3];
#        unsigned char log_type;
#        void *caller;
#        unsigned long idx;
#        void *data;
#} __attribute__ ((__packed__));

print_table = {
    "LOGK_NONE":"print_none",
    "LOGK_READL":"print_readlwritel",
        "LOGK_WRITEL":"print_readlwritel",
        "LOGK_LOGBUF":"print_logbuf",
        "LOGK_HOTPLUG":"print_hotplug",
        "LOGK_CTXID" : "print_ctxid",
        "LOGK_TIMESTAMP" : "print_timestamp",
}

@register_parser("--print-rtb", "Print RTB (if enabled)", shortopt="-r")
class RTB(RamParser) :
    def __init__(self, *args):
        super(RTB, self).__init__(*args)
        self.name_lookup_table = []

    def get_caller(self, line_nums, line_num) :
        if line_num in line_nums :
            return line_nums[line_num]
        else :
            return "Unknown file"

    def get_fun_name(self, addr) :
        l = self.ramdump.unwind_lookup(addr)
        if l is not None :
            symname, offset = l
        else :
            symname = "Unknown function"
        return symname

    def print_none(self, rtbout, rtb_ptr, logtype, data_offset, caller_offset, line_nums) :
        rtbout.write("{0} No data\n".format(logtype).encode('ascii','ignore'))

    def print_readlwritel(self, rtbout, rtb_ptr, logtype, data_offset, caller_offset, line_nums) :
        data = self.ramdump.read_word(rtb_ptr + data_offset)
        caller = self.ramdump.read_word(rtb_ptr + caller_offset)
        func = self.get_fun_name(caller)
        line = self.get_caller(line_nums, caller)
        rtbout.write("{0} from address {1:x} called from addr {2:x} {3} {4}\n".format(logtype, data, caller, func, line).encode('ascii','ignore'))

    def print_logbuf(self, rtbout, rtb_ptr, logtype, data_offset, caller_offset, line_nums) :
        data = self.ramdump.read_word(rtb_ptr + data_offset)
        caller = self.ramdump.read_word(rtb_ptr + caller_offset)
        func = self.get_fun_name(caller)
        line = self.get_caller(line_nums, caller)
        rtbout.write("{0} log end {1:x} called from addr {2:x} {3} {4}\n".format(logtype, data, caller, func, line).encode('ascii','ignore'))

    def print_hotplug(self, rtbout, rtb_ptr, logtype, data_offset, caller_offset, line_nums) :
        data = self.ramdump.read_word(rtb_ptr + data_offset)
        caller = self.ramdump.read_word(rtb_ptr + caller_offset)
        func = self.get_fun_name(caller)
        line = self.get_caller(line_nums, caller)
        rtbout.write("{0} cpu data {1:x} called from addr {2:x} {3} {4}\n".format(logtype, data, caller, func, line).encode('ascii','ignore'))

    def print_ctxid(self, rtbout, rtb_ptr, logtype, data_offset, caller_offset, line_nums) :
        data = self.ramdump.read_word(rtb_ptr + data_offset)
        caller = self.ramdump.read_word(rtb_ptr + caller_offset)
        func = self.get_fun_name(caller)
        line = self.get_caller(line_nums, caller)
        rtbout.write("{0} context id {1:x} called from addr {2:x} {3} {4}\n".format(logtype, data, caller, func, line).encode('ascii','ignore'))


    def print_timestamp(self, rtbout, rtb_ptr, logtype, data_offset, caller_offset, line_nums) :
        data = self.ramdump.read_word(rtb_ptr + data_offset)
        caller = self.ramdump.read_word(rtb_ptr + caller_offset)
        rtbout.write("{0} Timestamp: {1:x}{2:x}\n".format(logtype, data, caller).encode('ascii','ignore'))


    def load_numbers(self) :
        if self.ramdump.addr_lookup("msm_rtb") != 0 :
            gdb_cmd = NamedTemporaryFile(mode='w+t', delete=False)
            gdb_out = NamedTemporaryFile(mode='w+t', delete=False)
            for i in range(0,32) :
                gdb_cmd.write("print ((enum logk_event_type){0})\n".format(i))
            gdb_cmd.flush()
            gdb_cmd.close()
            gdb_out.close()
            stream = os.system("{0} -x {1} --batch {2} > {3}".format(self.ramdump.gdb_path, gdb_cmd.name, self.ramdump.vmlinux, gdb_out.name))
            a = open(gdb_out.name)
            results = a.readlines()
            for r in results :
                s = r.split(' ')
                self.name_lookup_table.append(s[2].rstrip())
            a.close()
            os.remove(gdb_out.name)
            os.remove(gdb_cmd.name)

    def parse(self) :
        rtb = self.ramdump.addr_lookup("msm_rtb")
        out_dir = self.ramdump.outdir
        if rtb is None :
            print_out_str ("[!] RTB was not enabled in this build. No RTB files will be generated")
            return
        self.load_numbers()
        step_size_offset = self.ramdump.field_offset("struct msm_rtb_state", "step_size")
        nentries_offset = self.ramdump.field_offset("struct msm_rtb_state","nentries")
        rtb_entry_offset = self.ramdump.field_offset("struct msm_rtb_state", "rtb")
        idx_offset = self.ramdump.field_offset("struct msm_rtb_layout","idx")
        caller_offset = self.ramdump.field_offset("struct msm_rtb_layout","caller")
        log_type_offset = self.ramdump.field_offset("struct msm_rtb_layout", "log_type")
        data_offset = self.ramdump.field_offset("struct msm_rtb_layout","data")
        rtb_entry_size = self.ramdump.sizeof("struct msm_rtb_layout")
        step_size = self.ramdump.read_word(rtb + step_size_offset)
        total_entries = self.ramdump.read_word(rtb + nentries_offset)
        rtb_read_ptr = self.ramdump.read_word(rtb + rtb_entry_offset)
        for i in range(0,step_size) :
            rtb_out = open("{0}/msm_rtb{1}.txt".format(out_dir,i),"wb")
            gdb_cmd = NamedTemporaryFile(mode='w+t', delete=False)
            gdb_out = NamedTemporaryFile(mode='w+t', delete=False)
            mask = self.ramdump.read_word(rtb + nentries_offset) - 1
            calling_addr = []
            line_nums = {}
            if step_size == 1 :
                last = self.ramdump.read_word(self.ramdump.addr_lookup("msm_rtb_idx"))
            else :
                last = self.ramdump.read_word(self.ramdump.addr_lookup("msm_rtb_idx_cpu") + self.ramdump.read_word(self.ramdump.addr_lookup("__per_cpu_offset")+4*i))
            last = last & mask
            last_ptr = 0
            next_ptr = 0
            next_entry = 0
            while True :
                next_entry = (last + step_size) & mask
                last_ptr = rtb_read_ptr + last * rtb_entry_size + idx_offset
                next_ptr = rtb_read_ptr + next_entry * rtb_entry_size + idx_offset
                a = self.ramdump.read_word(last_ptr)
                b = self.ramdump.read_word(next_ptr)
                if a < b :
                    last = next_entry
                if next_entry != last :
                    break
            for r in range(i,total_entries,step_size) :
                caddr = self.ramdump.read_word(rtb_read_ptr + r * rtb_entry_size + caller_offset)
                calling_addr.append(caddr)
                gdb_cmd.write("info line *0x{0:x}\n".format(caddr))
            gdb_cmd.flush()
            gdb_cmd.close()
            gdb_out.close()
            stream = os.system("{0} -x {1} --batch {2} > {3}".format(self.ramdump.gdb_path, gdb_cmd.name,self.ramdump.vmlinux, gdb_out.name))
            g = open(gdb_out.name)
            results = g.readlines()
            # GDB is dumb and splits output on multiple lines
            # Fortunately the stuff we want is at the front
            # so zap the extra line
            for a in results  :
                m = re.search('^   ',a)
                if m is not None :
                    results.remove(a)

            for a,r in zip(calling_addr,results) :
                m = re.search('(Line \d+ of \".*\")',r)
                if m is not None :
                    line_nums[a] = m.group(0)

            g.close()
            os.remove(gdb_out.name)
            os.remove(gdb_cmd.name)
            stop = 0
            rtb_logtype_offset = self.ramdump.field_offset("struct msm_rtb_layout", "log_type")
            rtb_idx_offset = self.ramdump.field_offset("struct msm_rtb_layout", "idx")
            rtb_data_offset = self.ramdump.field_offset("struct msm_rtb_layout", "data")
            rtb_caller_offset = self.ramdump.field_offset("struct msm_rtb_layout", "caller")
            while True:
                ptr = rtb_read_ptr + next_entry * rtb_entry_size
                stamp = self.ramdump.read_word(ptr + rtb_idx_offset)
                rtb_out.write("{0:x} ".format(stamp).encode('ascii','ignore'))
                item = self.ramdump.read_byte(ptr + rtb_logtype_offset)
                item = item & 0x7F
                name_str = "(unknown)"
                if item >= len(self.name_lookup_table) or item < 0:
                    self.print_none(rtb_out, ptr, name_str, rtb_data_offset, rtb_caller_offset, line_nums)
                else :
                    name_str = self.name_lookup_table[item]
                    if name_str not in print_table :
                        self.print_none(rtb_out, ptr, name_str, rtb_data_offset, rtb_caller_offset, line_nums)
                    else :
                        func = print_table[name_str]
                        getattr(RTB,func)(self, rtb_out, ptr, name_str, rtb_data_offset, rtb_caller_offset, line_nums)
                if next_entry == last :
                    stop = 1
                next_entry = (next_entry + step_size) & mask
                if (stop == 1) :
                    break
            print_out_str ("Wrote RTB to {0}/msm_rtb{1}.txt".format(out_dir,i))
            rtb_out.close()
