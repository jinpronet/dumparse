# Copyright (c) 2013, The Linux Foundation. All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 and
# only version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from parser_util import register_parser, RamParser
from print_out import print_out_str

@register_parser("--print-kconfig", "Print saved kernel configuration", shortopt="-c")
class Kconfig(RamParser):

    def parse(self) :
        out_path = self.ramdump.outdir
        saved_config = open(out_path+"/kconfig.txt","wb")

        for l in self.ramdump.config :
            saved_config.write(l+"\n")

        saved_config.close()
        print_out_str("---wrote saved kernel config to {0}/kconfig.txt".format(out_path))

