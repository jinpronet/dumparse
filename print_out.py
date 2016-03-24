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

from contextlib import contextmanager

out_file = None

def set_outfile(path) :
    global out_file
    out_file = open(path,"wb")

def print_out_str(string) :
    if out_file is None :
        print (string)
    else :
        out_file.write((string+"\n").encode('ascii','ignore'))

@contextmanager
def print_out_section(header):
    begin_header_string = "{0}begin {1}{0}".format(
        10 * '-', header
    )
    end_header_string = "{0}end {1}{2}".format(
        12 * '-',
        header,
        10 * '-',
    )
    print_out_str("\n" + begin_header_string)
    yield
    print_out_str(end_header_string + "\n")
