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

import os
import platform
import glob
import re
import sys

_parsers = []

class ParserConfig(object):
    """Class to encapsulate a RamParser its desired setup (command-line
    options, etc)."""
    def __init__(self, cls, longopt, desc, shortopt, optional):
        self.cls = cls
        self.longopt = longopt
        self.desc = desc
        self.shortopt = shortopt
        self.optional = optional

def register_parser(longopt, desc, shortopt=None, optional=False):
    """Decorator to register a parser class (a class that inherits from
    RamParser) with the parsing framework. By using this decorator
    your parser will automatically be hooked up to the command-line
    parsing code.

    This makes it very easy and clean to add a new parser:

      o Drop a new file in parsers that defines a class that inherits
        from RamParser

      o Decorate your class with @register_parser

      o Define a `parse' method for your class

    All of the command line argument handling and invoking the parse
    method of your parser will then be handled automatically.

    Required arguments:

    - longopt :: The longopt command line switch for this parser

    - desc :: A short description of the parser (also shown in the
      help-text associated with the longopt)

    Optional arguments:

    - shortopt :: The shortopt command line switch for this parser

    - optional :: Indicates the parser is optional and should not be run with
      --everything

    """
    def wrapper(cls):
        if cls in [p.cls for p in _parsers]:
            raise Exception(cls + " is already registered!")
        _parsers.append(ParserConfig(cls, longopt, desc, shortopt, optional))
        return cls
    return wrapper

def get_parsers():
    """Imports everyone under the `parsers' directory. It is expected that
    the parsers under the parsers directory will be a collection of
    classes that subclass RamParser and use the register_parser
    decorator to register themselves with the parser
    framework. Therefore, importing all the modules under `parsers'
    should have the side-effect of populating the (internal to
    parser_util) _parsers list with the discovered parsers.

    Returns the list of ParserConfig instances built as a side-effect
    of the importing.

    """
    frozen = 'not'
    if getattr(sys,'frozen',False):
        #we are running in a bundle
        print "in bundle"
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
        for f in hiddenimports:
            __import__(f)
    else:
        print "in normal Python"
        #we are runing in a normal Python evniromaent
        parsers_dir = os.path.join(os.path.dirname(__file__), 'parsers')
        for f in glob.glob(os.path.join(parsers_dir, '*.py')):
            modname_ext = os.path.basename(f)
            if modname_ext == "__init__.py":
                continue

            modname = "parsers." + os.path.splitext(modname_ext)[0]
            print modname
            # if the module contains a class (or classes) that are
            # decorated with `register_parser' then the following import
            # will have the side-effect of adding that class (encapsulated
            # in a ParserConfig object) to the _parsers list. Note that
            # this import is effectively a noop if the module has already
            # been imported, so there's no harm in calling get_parsers
            # multiple times.
            __import__(modname)
    return _parsers

class RamParser(object):
    """Base class for implementing ramdump parsers. New parsers should
    inherit from this class and define a `parse' method.

    Interesting properties that will be set for usage in derived
    classes:

    - ramdump :: The RamDump instance being parsed

    """
    def __init__(self, ramdump):
        self.ramdump = ramdump

    def parse(self):
        raise NotImplementedError

def which(program):
    """Just like which(1). Searches the PATH environment variable for a
    directory containing program.

    """
    for path in os.environ["PATH"].split(os.pathsep):
        exe_file = os.path.join(path, program)
        if os.access(exe_file, os.X_OK):
            return exe_file

    return None

def get_system_type():
    """Returns a "normalized" version of platform.system (transforming
    CYGWIN to Windows, for example). Returns None if not a supported
    platform.

    """
    plat = platform.system()
    if plat == 'Windows':
       return 'Windows'
    if re.search('CYGWIN', plat) is not None :
       # On certain installs, the default windows shell
       # runs cygwin. Treat cygwin as windows for this
       # purpose
       return 'Windows'
    if plat == 'Linux':
       return 'Linux'
    if plat == 'Darwin':
       return 'Darwin'
