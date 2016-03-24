#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
from datetime import *
import logging
class a:
    def __init__(self):
        print "a"
    pass


class Slogy:
    '''
    save log,and extern for save we need result
    '''

    name_fd = None
    lg = None

    def __init__(self,Name="",debug=logging.INFO):

        curDate = date.today() - timedelta(days=0)
        if Name == "" :
            Name = "_"+str(curDate)+".log"
        else:
            Name = Name+"_"+str(curDate)+".log"

        LOG_FILE = "log/"+Name

        if not os.path.exists("log"):
            os.mkdir("log")

        #logging class 使用
        handler = logging.FileHandler(LOG_FILE) # 实例化handler
        fmt = '%(asctime)s - %(message)s'

        formatter = logging.Formatter(fmt)   # 实例化formatter
        handler.setFormatter(formatter)      # 为handler添加formatter

        logger = logging.getLogger('tst')    # 获取名为tst的logger
        logger.addHandler(handler)           # 为logger添加handler
        logger.setLevel(debug)

        handler = logging.StreamHandler()
        logger.addHandler(handler)
        self.lg = logger

    def logd(self,str):
        self.lg.debug(str)
        pass
    def loge(self,str):
        self.lg.error(str)
        pass
    def logi(self,str):
        self.lg.info(str)
        pass

    def outp(self,str):
        pass

