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
from mm import *
from parser_util import register_parser, RamParser

@register_parser("--print-pagetypeinfo", "Print the pagetypeinfo")
class Pagetypeinfo(RamParser):

    def print_pagetype_info_per_zone(self, ramdump, zone, migrate_types) :

        free_area_offset = ramdump.field_offset("struct zone","free_area")
        free_area_size = ramdump.sizeof("struct free_area")
        free_list_offset = ramdump.field_offset("struct free_area","free_list")
        migratetype_names = ramdump.addr_lookup("migratetype_names")
        zone_name_offset = ramdump.field_offset("struct zone","name")
        zname_addr = ramdump.read_word(zone + zone_name_offset)
        zname = ramdump.read_cstring(zname_addr, 12)
        is_corrupt = False
        total_bytes = 0

        for mtype in range(0, migrate_types) :
            mname_addr = ramdump.read_word(migratetype_names + mtype * 4)
            mname = ramdump.read_cstring(mname_addr, 12)
            pageinfo = ("zone {0:8} type {1:12} ".format(zname, mname))
            nums = ""
            total_type_bytes = 0
            for order in range(0, 11) :

                area = zone + free_area_offset + order * free_area_size

                orig_free_list = area + free_list_offset + 8 * mtype
                curr = orig_free_list
                pg_count = -1
                first = True
                while True :
                    pg_count = pg_count + 1
                    next_p = ramdump.read_word(curr)
                    if next_p == curr :
                        if not first :
                           is_corrupt = True
                        break
                    first = False
                    curr = next_p
                    if curr == orig_free_list :
                        break
                nums = nums+("{0:6}".format(pg_count))
                total_type_bytes = total_type_bytes + pg_count * 4096 * (2**order)
            print_out_str( pageinfo + nums + " = {0} MB".format(total_type_bytes/(1024*1024)))
            total_bytes = total_bytes + total_type_bytes

        print_out_str("Approximate total for zone {0}: {1} MB\n".format(zname, total_bytes/(1024*1024)))
        if is_corrupt :
            print_out_str ("!!! Numbers may not be accurate due to list corruption!")

    def parse(self) :
        gdb_cmd = NamedTemporaryFile(mode='w+t', delete=False)
        gdb_out = NamedTemporaryFile(mode='w+t', delete=False)
        gdb_cmd.write("print /d MIGRATE_TYPES\n")
        gdb_cmd.write("print /d __MAX_NR_ZONES\n")
        gdb_cmd.flush()
        gdb_cmd.close()
        gdb_out.close()
        stream = os.system("{0} -x {1} --batch {2} > {3}".format(self.ramdump.gdb_path, gdb_cmd.name, self.ramdump.vmlinux, gdb_out.name))
        a = open(gdb_out.name)
        results = a.readlines()
        vals = []
        for r in results :
            s = r.split(' ')
            vals.append(int(s[2].rstrip(),10))
        a.close()
        os.remove(gdb_out.name)
        os.remove(gdb_cmd.name)
        migrate_types = vals[0]
        max_nr_zones = vals[1]

        contig_page_data = self.ramdump.addr_lookup("contig_page_data")
        node_zones_offset = self.ramdump.field_offset("struct pglist_data", "node_zones")
        present_pages_offset = self.ramdump.field_offset("struct zone", "present_pages")
        sizeofzone = self.ramdump.sizeof("struct zone")
        #modify by youjin for check
        if (contig_page_data is not None) and (node_zones_offset is not None):
            zone = contig_page_data + node_zones_offset
        else:
            return

        while zone < (contig_page_data + node_zones_offset + max_nr_zones * sizeofzone)  :
             present_pages = self.ramdump.read_word(zone + present_pages_offset)
             if not not present_pages :
                 self.print_pagetype_info_per_zone(self.ramdump, zone, migrate_types)

             zone = zone + sizeofzone


