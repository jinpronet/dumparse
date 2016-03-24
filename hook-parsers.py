from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.compat import is_win, is_darwin

import os
import sys
datas = collect_data_files('parsers')

hiddenimports = [
"parsers.cachedump",
"parsers.cpu_state",
"parsers.debug_image",
"parsers.dmesg",
"parsers.gpuinfo",
"parsers.iommu",
"parsers.irqstate",
"parsers.kconfig",
"parsers.pagetypeinfo",
"parsers.page_table_dump",
"parsers.rtb",
"parsers.slabinfo",
"parsers.taskdump",
"parsers.vmalloc",
"parsers.watchdog",
"parsers.workqueue",
]
