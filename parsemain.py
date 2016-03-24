#!/usr/bin/env python
# -*- coding: utf8 -*-
#---------------------------------------------------------------------------
#    This is a windows show tool for parse crash dump for qcom family-B chip
#
#Author:youjin
#bugreport :jinrich@126.com
#---------------------------------------------------------------------------
import tkFileDialog

__author__ = 'youjin'
__version__="V0.2"


#-----------------------------------------------------
import slogy
import subprocess,os
import threading
import socket,sys
import signal
import time
from ramdump import *
import parser_util
import parsers
import parsers.cachedump
try:

    import Tkinter as tk
    import ttk
    from ScrolledText import ScrolledText
    from tkMessageBox import *
    from PIL import Image,ImageTk,ImageDraw
except:
    print 'Following module is needed:'
    print '- Tkinter: sudo apt-get install python-tk'
    print '- PIL: sudo apt-get install python-imaging-tk'
    sys.exit()



#########################global var###################
g_log = None
def get_path():
    frozen = 'not'
    if getattr(sys,'frozen',False):
        #we are runing in a bundle
        frozen = 'ever so'
        par_path = sys._MEIPASS
        print "boundle:"+par_path
    else:
        #we are run in a normal
        par_path=os.path.dirname(os.path.abspath(__file__))
        print "normal:"+ par_path
    return par_path

class screenframe(tk.Frame):
    '''
    主要函数，用于构造界面，处理界面事件
    '''
    master = None
    _text = None
    vpath = ""
    dpath = ""
    opath = ""
    #进度条
    sprocess = None
    all_other = None
    #Int记录是否选择解析所有
    a_o_value = 1
    #tkinter 单选按钮对象
    all_r = None
    #tkinter 单选按钮对象
    split_r = None
    #字典：记录复选框对象，没有多大用处
    split_param = {}
    #字典：记录复选框是否选择key是名称，value是复选框对象接收的整形变量值，用于记录是否选择
    split_param_value = {}
    #解析按钮
    B4_parser = None
    #工具所在路径
    par_path = ""
    #列表：复选框名称表，会循环创建
    radio_names = ["checkwatchdog","t32launcher"]
        #["print-irqs","print-workqueues","check-for-watchdog","check-for-panic","t32launcher","print-rtb", \
        #"slabinfo","print-cache-dump"]

    parse_pid=0
    param_num = 0

    def __init__(self,root):
        tk.Frame.__init__(self, root, class_='screenframe')
        self.master = root

        self.all_other=tk.IntVar(self,1)
        for i in self.radio_names:
            self.split_param_value[i] = tk.IntVar(self)

        for p in parser_util.get_parsers():
            self.split_param_value[p.cls.__name__]=tk.IntVar(self)

        g_log.logi(self.split_param_value.keys())
        frozen = 'not'
        if getattr(sys,'frozen',False):
            #we are runing in a bundle
            frozen = 'ever so'
            self.par_path = sys._MEIPASS
            print "boundle"+self.par_path
        else:
            #we are run in a normal
            self.par_path=os.path.dirname(os.path.abspath(__file__))
            print "normal"+self.par_path

        self.createwindows()
        self.grid()

        pass
    def show_respon(self,strs,color=None):
        '''
        该函数用于将信息显示给用户看见，并且添加时间
        strs：将要显示的字符串
        color:字符串将以什么颜色进行显示
        '''
        if strs != "":
            strs =str(time.strftime('[%Y-%m-%d:%H:%M:%S]>',time.localtime())) + strs +"\n"
        if color is not None:
            self._text.tag_config(color,foreground=color)
            self._text.insert('end',strs,color)
        else:
            self._text.insert('end',strs)

        self._text.yview_moveto(1)
        g_log.logd(strs)


    def parse_ramparse(self):
        """
        dump = RamDump(options.vmlinux, nm_path, gdb_path, options.ram_addr,
                   options.autodump, options.phys_offset, options.outdir,
                   options.force_hardware, options.force_hardware_version)
        对死机信息解析的具体处理函数
        """
        if self.a_o_value == 1:
            print 'start 2200'
            self.sprocess.start(2200)
        else:
            print self.param_num
            self.sprocess.start(700+self.param_num*80)
        dump = RamDump(self.vpath.get(),self.par_path+"/"+"arm-none-eabi-nm.exe",self.par_path+"/"+"arm-none-eabi-gdb.exe",
                       None,self.dpath.get(),None,self.opath.get(),None,None,self)

        if not dump.print_command_line() :
            print_out_str ("!!! Error printing saved command line.")
            print_out_str ("!!! The vmlinux is probably wrong for the ramdumps")
            print_out_str ("!!! Exiting now...")
            return -2
        # if self.split_param_value["checkwatchdog"] :
        #     print_out_str ("\n--------- watchdog time -------")
        #     get_wdog_timing(dump)
        #     print_out_str ("---------- end watchdog time-----")

        if self.split_param_value["t32launcher"] or self.a_o_value :
            dump.create_t32_launcher()

        for p in parser_util.get_parsers():
            # we called parser.add_option with dest=p.cls.__name__ above,
            # so if the user passed that option then `options' will have a
            # p.cls.__name__ attribute.
            if self.sprocess['value'] > 90:
                    self.sprocess['value']=90
            if self.split_param_value[p.cls.__name__].get() == 1 or self.a_o_value == 1:
                try:
                    with print_out_section(p.cls.__name__):
                        self.show_respon("解析:>>[%s]>>>>开始......." %p.cls.__name__)
                        p.cls(dump).parse()
                        self.show_respon("解析:>>[%s]<<<<<完成 " %p.cls.__name__)
                except  Exception , e:
                    self.show_respon("Exception %s" %e,'red')
                    self.show_respon("解析:>>[%s]<<<<<异常 " %p.cls.__name__,'red')

        self.sprocess.stop()
        self.sprocess['value']=100

        print "test parse_ramparse"
        pass

    def parse_thread(self):
        """
        线程函数，用于对命令和选项的构建，然后调用真正的处理函数
        """

        args=['python','pamparse.py']
        sp = "-n "+self.par_path+"/"+"arm-none-eabi-nm.exe"
        args.append(sp)
        sp = "-g "+self.par_path+"/"+"arm-none-eabi-gdb.exe"
        args.append(sp)
        if self.a_o_value == 1:
            args.append("-x")
        else:
            for i in self.split_param_value.keys():
                if self.split_param_value[i].get() == 1:
                    pp = "--"+i
                    args.append(pp)
                    self.param_num = len(args)
            pass

        args.append("-o")
        args.append(self.opath.get())
        args.append("-v")
        args.append(self.vpath.get())
        args.append("--auto-dump")
        args.append(self.dpath.get())

        self.show_respon("".join(args))
        self.parse_ramparse()

        #self.parse_pid = subprocess.Popen(args,stdin = subprocess.PIPE,stdout = subprocess.PIPE,stderr = subprocess.PIPE)
        #print "subprocess pid:"+str(self.parse_pid.pid)
        #out = self.parse_pid.stdout.read()
        #print out,self.parse_pid.returncode
        #time.sleep(10)
        #print self.parse_pid.stderr.read()

        self.show_respon("end process threading ====================",'red')
        self.show_respon("请查看该文件：%s/dmesg_TZ.txt"%self.opath.get(),'green')
        self.B4_parser['state'] = tk.ACTIVE

        pass

    def doparse(self,event):
        """
        按钮执行函数
        该函数中将创建 处理线程
        """
        if str(self.B4_parser['state']) == 'disabled':
            #g_log.loge("disable here")
            return 1

        if None in [self.vpath.get(),self.opath,self.dpath.get()]:
            self.show_respon(">>>>error:path error<<<<<","red")
            return -1
        if not os.path.isfile(self.vpath.get()) or not os.path.isdir(self.opath.get()):
            self.show_respon("error:not a vailed path","red")
            return -2
        if not os.path.isfile(self.dpath.get()+"/"+"DDRCS0.BIN"):
            self.show_respon("error :dump file is error","red")
            return -3

        t = threading.Thread(target=self.parse_thread)
        t.start()
        self.show_respon( ">>>>>>>>>>>>do threading<<<<<<<<<<<<\n","red")
        self.B4_parser['state'] = tk.DISABLED
        pass

    def select_path(self,event):

        tn = event.widget.winfo_name()

        if tn == "vpath":
            dirname = tkFileDialog.askopenfilename(parent=self.master,initialdir="F:/8974/",title='选择Vmlinux路径')
            self.vpath.delete(0,tk.END)
            self.vpath.insert(0,dirname)

        elif tn == "dpath":
            dirname = tkFileDialog.askdirectory(parent=self.master,initialdir="C:/ProgramData/Qualcomm/QPST/Sahara/Port_COM88",title='选择dump路径')
            self.dpath.delete(0,tk.END)
            self.dpath.insert(0,dirname)
        elif tn == "opath":
            dirname = tkFileDialog.askdirectory(parent=self.master,initialdir="F:/8974/",title='选择输出路径')
            self.opath.delete(0,tk.END)
            self.opath.insert(0,dirname)

        self.show_respon(dirname)


        print dirname

        pass
    def checkbutton_deal(self):
        """
        处理复选框的选择
        """
        print self.all_other.get()

        if self.all_other.get() != self.a_o_value:
            if self.all_other.get() == 1:
                self.show_respon("All parser deal")
                for r in self.split_param.values():
                    r['state']=tk.DISABLED

            elif self.all_other.get() == 2:
                self.show_respon("select parser deal")
                for r in self.split_param.values():
                    r['state']=tk.ACTIVE

            self.a_o_value = self.all_other.get()

        pass

    def add_radio(self,f1):
        '''
        添加复选按钮函数
        '''

        self.split_r = ttk.Radiobutton(f1,text="Splitconfig",variable = self.all_other,value=2,width=14,command = self.checkbutton_deal)
        self.split_r.grid(row=0,column = 1)
        i = 1
        j = 0
        for c in self.split_param_value.keys() :
            i += 1
            if i%5 == 0:
                i = 1
                j +=1
            cc = ttk.Checkbutton(f1,text=c,width=14,variable = self.split_param_value[c],state = tk.DISABLED)
            self.split_param[c] = cc
            print c,j,i
            cc.grid(row = j,column = i)

        pass
    def createwindows(self):
        L1 = ttk.Label(self,text="vmlinux路径:")
        L2 = ttk.Label(self,text="d u m p路径:")
        L3 = ttk.Label(self,text="解析输出路径:")
        L1.grid(row=0, column=0)
        L2.grid(row=1, column=0)
        L3.grid(row=2, column=0)

        self.vpath = ttk.Entry(self,text = "",width = 50)
        self.dpath = ttk.Entry(self,text = "",width = 50)
        self.opath = ttk.Entry(self,text = "",width = 50)
        self.vpath.grid(row=0,column=1)
        self.dpath.grid(row=1,column=1)
        self.opath.grid(row=2,column=1)


        B1 = ttk.Button(self,name="vpath",text = "选择文件")
        B2 = ttk.Button(self,name="dpath",text = "选择路径")
        B3 = ttk.Button(self,name="opath",text = "选择路径")
        B1.grid(row=0,column=2)
        B2.grid(row=1,column=2)
        B3.grid(row=2,column=2)
        B1.bind('<ButtonRelease-1>', self.select_path)
        B2.bind('<ButtonRelease-1>', self.select_path)
        B3.bind('<ButtonRelease-1>', self.select_path)

        #row 3
        self.all_r = ttk.Radiobutton(self,text="All",variable = self.all_other,value=1,command = self.checkbutton_deal)
        self.all_r.grid(row=3,column = 0)

        f1=ttk.LabelFrame(self,text="选择解析",height = 100,width=200)
        self.add_radio(f1)
        f1.grid(row=3,column=1,columnspan=2)

        #row 4
        self.sprocess = ttk.Progressbar(self,length=440)
        #self.sprocess['value']=40

        self.sprocess.grid(row = 4,column =0,columnspan =2)
        #self.sprocess.start(100)


        self.B4_parser = ttk.Button(self,name="doparse",text="解析死机文件")
        self.B4_parser.grid(row=4,column=2,columnspan=1)
        self.B4_parser.bind('<ButtonRelease-1>', self.doparse)

        self._text = ScrolledText(self,width = 68,height = 20)
        self._text.grid(row = 5,column =0,columnspan =3)

        pass
    def sub_exit(self,errno):
        self.B4_parser['state']=tk.NORMAL
        self.sprocess.stop()
        self.show_respon("sub process exit with error:%d"%errno,"blue")


class ttkDespApplication(ttk.Frame):
    """
    显示使用说明界面
    """
    _adb = None
    _entry = None
    _text = None

    def __init__(self, master=None):
        ttk.Frame.__init__(self, master, class_='ttkDespApplication')

        #Set the windows title
        title = '使用说明'
        self.master.title(title)

        self.create_test()

        #Set the pad position
        master.geometry("+%d+%d" % (300, 200))
        self.grid()

    def create_test(self):
        st = ScrolledText(self,width = 66,height = 20)
        f = open(get_path()+"/shuoming","r")
        lines = f.readlines()
        for line in lines:
            st.insert(tk.END,line.decode("gb2312").encode("utf-8"))
        f.close()
        st.grid()
        pass

class parsemain:
    """
    主类
    """
    _root_tk = None
    def __init__(self):

        pass
    def show_version_author(self,sf):

        sf.show_respon("欢迎使用死机解析工具:"+__version__)
        sf.show_respon("该工具只支持高通familyB系列芯片的解析")
        sf.show_respon("有任何问题联系：游锦 you.jin@zte.com.cn")
        sf.show_respon("          ^V^使用愉快^V^",'red')

    def parse_main(self):
        self._root = tk.Tk()
        self._root.title("死机解析工具:"+__version__)
        #self._root.
        #设置窗口无标题栏
        #self._root.overrideredirect(True)
        #设置窗口透明度
        #self._root.attributes("-alpha", 0.7)
        #窗口置顶
        #self._root.wm_attributes('-topmost',1)

        self.add_menu()
        sf=screenframe(self._root)


        self.show_version_author(sf)
        ppid = sf.parse_pid
        #self._root.iconbitmap(get_path()+'/32x32.ico')#加载时间太长，导致二次闪烁
        self._root.mainloop()

        if ppid != 0:
            os.killpg(ppid,signal.SIGUSR1)

    def show_desp(self):
        b_rootTop = tk.Toplevel()
        tkapp = ttkDespApplication(master=b_rootTop)
        #showinfo(title='使用说明',message="联系人:youjin\n联系方式:https://github.com/jinpronet/mobileco")

    def show_about(self):

        showinfo(title='问题反馈',message="联系人:youjin\n联系方式:youjin@zte.com.cn jinrich@126.com")

    def add_menu(self):
        '''
        make menu for keypad
        '''
        menu_key = tk.Menu(self._root)
        #menu_key.add_command(label="键盘",command = self.show_keypad )
        menu_key.add_command(label="说明",command = self.show_desp )
        menu_key.add_command(label="帮助",command = self.show_about )
        self._root.config(menu=menu_key)


if __name__ == "__main__":
    g_log = slogy.Slogy("parsedump")
    par = parsemain()
    par.parse_main()


    print "exit"
    sys.exit()
