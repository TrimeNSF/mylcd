#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   > Author: LaiQiMing
#   > Mail: 13536343225@139.com

import os
import sys
import time
import yaml
import socket
import logging
import datetime
import traceback
import threading
import collections
import struct, fcntl
import RPi.GPIO as GPIO


if len(sys.argv) > 1 and sys.argv[1] == "-v":
    print (
    'v2.0\n'
    ' - logger add lineno.\n'
    ' - modify speed minus 1 to set.\n'
    ' - modify video beyond the boundary to reset.\n'
    'v1.0\n'
    ' - alpha.\n'
    )
    sys.exit()

lang = {
        'Main':('Main', '主界面'),
        'Menu':('Menu', '菜单'),
        'Cycle':('Cycle', '循环'),
        'Single':('Single', '单一'),
        'HW-Sync':('HW-Sync', '硬件-同步'),
        'SW-Sync':('SW-Sync', '软件-同步'),
        'Stop':('Stop', '停止'),
        'Year':('Year', '年'),
        'Month':('Month', '月'),
        'Day':('Day', '日'),
        'Hour':('Hour', '时'),
        'Minute':('Minute', '分'),
        'Second':('Second', '秒'),
        'chinese':('chinese', '中文'),
        'english':('english', '英文'),
        'Play Mode':('Play Mode', '播放模式'),
        'File':('File', '文件'),
        'Play Speed':('Play Speed', '播放速度'),
        'Brightness':('Brightness', '亮度'),
        'Date':('Date', '日期时间'),
        'Refresh Rate':('Refresh Rate', '刷新率'),
        'IP address':('IP address', 'IP地址'),
        'MAC':('MAC', '物理地址'),
        'MAC(BCD)':('MAC(BCD)', '物理地址(BCD)'),
        'Window Position':('Window Position', '窗口位置'),
        'System State':('System State', '系统状态'),
        'System Info':('System Info', '系统信息'),
        'Language':('Language', '语言'),
        '2Adjust file and speed is invalid':('(Adjust file\nspeed is invalid.only\nsupport h264\mpeg4.)', '(调节文件和\n速度无效，只支持h264\nmpeg4)'),
        '3Adjust file and speed is invalid':('(Adjust file\nspeed is invalid.)', '(调节文件和\n速度无效)'),
        'Playing':('Playing ', '播放'),
        'Pause':('Pause', '暂停'),
        'Static IP':('Static IP', '静态IP'),
        'Obtain IP Auto':('Obtain IP Auto', '自动获取IP'),
        'ETH':('ETH', '网口'),
        'online':('[online]', '[在线]'),
        'offline':('[offline]', '[离线]'),
        'HDMI':('HDMI-input', 'HDMI输入'),
        '':('', ''),
        }

KEY_UP     = 13
KEY_DOWN   = 5
KEY_MENU   = 6
KEY_CONFIG = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(KEY_UP,     GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY_DOWN,   GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY_MENU,   GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(KEY_CONFIG, GPIO.IN, pull_up_down=GPIO.PUD_UP)

present_interface = 0
present_menu = 0
present_ip_address = 0
present_lang = 1
present_video = 0
present_netstatus = 0
present_hdmistatus = 0
present_locationstatus = 0
present_mode = 0
present_speed = 0
present_bright = 0
config_status = False
config_date_status = True
config_file = '/home/Ym/data/config.yaml'

#log...
logger = logging.getLogger()
logger.setLevel(logging.NOTSET)
c_h = logging.StreamHandler()
formatter = logging.Formatter('[%(asctime)s] %(levelname)s lcdclient:%(lineno)s -- : %(message)s ')
c_h.setFormatter(formatter)
logger.addHandler(c_h)

key_trigger_status = False
t_load_info_exitBit = False

send_par_status = 0
exit_status = 0
net_status = 'offline'

client1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
logger.debug('[MT], create client1 socket successful...')
ip_port1 = ('127.0.0.1', 60001)

def get_current_months():
    nowtime = datetime.datetime.now()
    current_year = nowtime.year
    current_month = nowtime.month
    next_year = current_year
    next_month = current_month + 1
    if current_month == 12:
        next_year = current_year + 1
        next_month = 1
    return (datetime.datetime(next_year, next_month, 1) - datetime.datetime(current_year, current_month, 1)).days
    
def get_ip():
    get = os.popen("lcd_ctrl eth_ip")
    eth_ip = get.read().split('\n')[0]
    get.close()
    get = os.popen("lcd_ctrl module_ip")
    module_ip = get.read().split('\n')[0]
    get.close()
    return lang['ETH'][present_lang]+': %s\n4G: %s' % (eth_ip,module_ip)

class Interface:
    def __init__(self, name, options=[]):
        self.name = name
        self.options = options

class PlayMode:
    def __init__(self, name):
        self.name = name

class Date:
    def __init__(self, name, current_option=0):
        self.name = name
        self.current_option = current_option

    def get_option(self):
        if self.name == lang['Year']:
            return str(self.current_option + 2000)
        elif self.name == lang['Month']:
            return str(self.current_option + 1)
        elif self.name == lang['Day']:
            return str(self.current_option + 1)
        else:
            return str(self.current_option)

    def set_option(self):
        logger.debug('Date self.current_option : %d' %(self.current_option))
        if self.name == lang['Year']:
            self.current_option = self.current_option % 100
        elif self.name == lang['Month']:
            self.current_option = self.current_option % 12
        elif self.name == lang['Day']:
            self.current_option = self.current_option % get_current_months()
        elif self.name == lang['Hour']:
            self.current_option = self.current_option % 24
        elif self.name == lang['Minute']:
            self.current_option = self.current_option % 60
        elif self.name == lang['Second']:
            self.current_option = self.current_option % 60

class IP_address:
    def __init__(self, name, current_option=0):
        self.name = name
        self.current_option = current_option

    def get_option(self):
        pass

    def set_option(self):
        logger.debug('Date self.current_option : %d' %(self.current_option))

class Language:
    def __init__(self, name):
        self.name = name

class Menu:
    def __init__(self, name, something=None, options=[], current_option=0):
        self.name = name
        self.something = something
        self.options = options
        self.current_option = current_option

    def get_option(self, present_option=None):
        #logger.debug('[MT], Menu get_option ...')
        if self.name == lang['Brightness']:
            if present_option == None:
                return str(self.current_option)
            else:
                return str(present_option)
            ''' Real-time brightness status
            with open('/home/Ym/data/bright.data') as fd:
                 bright = fd.readline().split('\n')[0]
            self.current_option = int(bright)
            return bright
            '''
        elif self.name == lang['Date']:
            return time.strftime('20%y/%m/%d\n %H:%M:%S', time.localtime())
            #return time.strftime('%y/%m/%d %H:%M:%S', time.localtime())
        elif self.name == lang['Refresh Rate']:
            return self.options[self.current_option]
        elif self.name == lang['File']:
            #logger.debug('[MT], self.name is : %s' %(self.name[present_lang]))
            if bool(self.options):
                #logger.debug('[MT], self.option is ture.')
                if present_option == None:
                    logger.debug('[MT], File - self.current_option = %d.' %self.current_option)
                    if self.current_option < len(self.options):
                        return self.options[self.current_option][1].split('/')[-1]
                    else:
                        return ' '
                else:
                    #logger.debug('[MT], File - present_option = %d.' %present_option)
                    if present_option < len(self.options):
                        return self.options[present_option][1].split('/')[-1]
                    else:
                        return ' '
            else:
                #logger.debug('[MT], self.option is false.')
                return ' '
        elif self.name == lang['MAC']:
            with open('/home/Ym/data/MACAddr.data') as fd:
                MAC = list(fd.readline())
            MAC.insert(4,'-')
            MAC.insert(9,'-')
            return ''.join(MAC)
        elif self.name == lang['MAC(BCD)']:
            with open('/home/Ym/data/MACAddrBCD.data') as fd:
                MAC = list(fd.readline())
            MAC.insert(4,'-')
            MAC.insert(9,'-')
            return ''.join(MAC)
        elif self.name == lang['Window Position']:
            with open('/home/Ym/data/xy_location.conf') as fd:
                line = fd.readline().split('\n')[0]           #!! will remove \n
            X = line.split(':')[0]
            Y = line.split(':')[1]
            W = line.split(':')[2]
            H = line.split(':')[3]
            if present_lang == 0:
                return '  XY: (%s, %s) \n  WH: %s, %s' % (X,Y,W,H)
            elif present_lang == 1:
                return '  XY: (%s, %s) \n  宽高: %s, %s' % (X,Y,W,H)
        elif self.name == lang['System State']:
            get = os.popen("lcd_ctrl cpu")
            cpu = get.read().split('\n')[0]
            get.close()
            get = os.popen("lcd_ctrl mem")
            mem = get.read().split('\n')[0]
            get.close()
            get = os.popen("lcd_ctrl space")
            space = get.read().split('\n')[0]
            get.close()
            get = os.popen("lcd_ctrl udisk")
            udisk = get.read().split('\n')[0]
            get.close()
            if present_lang == 0:
                return 'CPU:%s  MEM:%s\nSPACE:%s\nUdisk:%s' % (cpu,mem,space,udisk)
            elif present_lang == 1:
                return 'CPU:%s  内存:%s\n空间:%s\nU盘:%s' % (cpu,mem,space,udisk)
        elif self.name == lang['System Info']:
            with open('/home/Ym/data/version.data') as fd:
                SysVer = fd.readline().split('\n')[0]
            with open('/home/Ym/data/version_fpga.data') as fd:
                FpgaVer = fd.readline().split('\n')[0]
            with open('/home/Ym/data/version_mcu.data') as fd:
                McuVer = fd.readline().split('\n')[0]
            if present_lang == 0:
                return '   System: U%s\n   Fpga: V%s\n   Mcu: V%s' % (SysVer,FpgaVer,McuVer)
            elif present_lang == 1:
                return '   系统: U%s\n   硬件: V%s\n   单片机: V%s' % (SysVer,FpgaVer,McuVer)
        else:
            if type(self.options) == list:
                #logger.debug('[MT], current name is : %s' %(self.name[present_lang]))
                if bool(self.options):
                    #logger.debug('[MT], current option is : %s' %(self.options[self.current_option]))
                    if present_option == None:
                        return self.options[self.current_option].name[present_lang]
                    else:
                        return self.options[present_option].name[present_lang]
                else:
                    #logger.debug('[MT], current option is null.')
                    return ' '
            elif type(self.options) == tuple:
                if present_option == None:
                    return self.options[self.current_option]
                else:
                    return self.options[present_option]

    def get_option_object(self):
        if self.name == lang['Date']:
            return self.options[self.current_option]
        elif self.name == lang['IP address']:
            return self.options[self.current_option]
        elif self.name == lang['File']:
            if bool(self.options):
                return self.options[self.current_option]
            else:
                return ['-1', '', '']

    def set_option(self):
        #logger.debug('Menu self.current_option : %d' %(self.current_option))
        if self.name == lang['Brightness']:
            self.current_option %= 256
        else:
            if bool(self.options):
                self.current_option %= len(self.options)
                logger.debug('Menu self.current_option : %d' %(self.current_option))
            else:
                self.current_option = 0

    def do(self):
        if bool(self.something):
            self.something(self.options, self.current_option)


def switch_mode(options, current_option):
    logger.debug('[switch_mode], current option is : %s' %(options[current_option].name[present_lang]))
    cmd = 'mode %d'%current_option
    logger.debug('[switch_mode], cmd : %s' % cmd)
    client1.sendto((cmd).encode('utf-8'), ip_port1)

def switch_file(options, current_option):
    if bool(options):
        logger.debug('[switch_file], current option is : %s' %(options[current_option]))
    cmd = 'file %d'%current_option
    logger.debug('[switch_file], cmd : %s' % cmd)
    client1.sendto((cmd).encode('utf-8'), ip_port1)

def switch_speed(options, current_option):
    logger.debug('[switch_speed], current option is :%d %s' %(current_option, options[current_option]))
    cmd = 'speed %d'%(current_option+1)
    logger.debug('[switch_speed], cmd : %s' % cmd)
    client1.sendto((cmd).encode('utf-8'), ip_port1)

def switch_brightness(options, current_option):
    logger.debug('[switch_brightness], current option is : %d' %current_option)
    cmd = 'bright %d'%current_option
    logger.debug('[switch_brightness], cmd : %s' % cmd)
    client1.sendto((cmd).encode('utf-8'), ip_port1)

def change_date(options, current_option):
    logger.debug('[change_date], current option is : %d' %current_option)
    cmd = 'date --set="20%02d-%02d-%02d %02d:%02d:%02d.000"'%(options[0].current_option, 
    options[1].current_option+1,
    options[2].current_option+1,
    options[3].current_option,
    options[4].current_option,
    options[5].current_option)
    logger.debug('[change_date], cmd : %s' %cmd)
    os.system(cmd)
    
def switch_ip_address(options, current_option):
    global present_ip_address
    logger.debug('[switch_ip_address], current option is : %s' %(options[current_option].name[present_lang]))
    if present_ip_address != current_option:
        present_ip_address = current_option
        if options[current_option].name == lang['Static IP']:
            logger.debug('[switch_ip_address], Static IP ...')
            os.system("lcd_ctrl static &")
        else:
            logger.debug('[switch_ip_address], Obtain IP Auto ...')
            os.system("lcd_ctrl dynamic &")

def switch_refresh_rate(options, current_option):
    logger.debug('[switch_refresh_rate], current option is : %s' %(options[current_option]))
    cmd = 'refresh %d'%current_option
    logger.debug('[switch_refresh_rate], cmd : %s' % cmd)
    client1.sendto((cmd).encode('utf-8'), ip_port1)

def switch_language(options, current_option):
    global present_lang
    present_lang = current_option
    logger.debug('[switch_language], current option is : %s %d' %(options[current_option].name[present_lang], present_lang))
    #os.system('echo %d > /home/Ym/data/lang.data' % current_option)
    cmd = 'lang %d'%current_option
    logger.debug('[switch_language], cmd : %s' % cmd)
    client1.sendto((cmd).encode('utf-8'), ip_port1)

interface_options = [
        Interface(lang['Main']),
        Interface(lang['Menu'])
        ]
playmode_options = [
        PlayMode(lang['Cycle']),
        PlayMode(lang['Single']),
        PlayMode(lang['HW-Sync']),
        PlayMode(lang['SW-Sync']),
        PlayMode(lang['Stop'])
        ]
file_options = []
playspeed_options = ('0.2', '0.4', '0.6', '0.8', '1.0', '1.5', '2.0', '3.0')
date_options = [
        Date(lang['Year']),
        Date(lang['Month']),
        Date(lang['Day']),
        Date(lang['Hour']),
        Date(lang['Minute']),
        Date(lang['Second'])
        ]
refresh_rate_options = ('60 Hz', '30 Hz', '20 Hz', '15 Hz', '12 Hz', '10 Hz')
ip_address_options = [
        IP_address(lang['Static IP']),
        IP_address(lang['Obtain IP Auto'])
        ]
language_options = [
        Language(lang['english']),
        Language(lang['chinese']),
        ]
dict_menu_options = collections.OrderedDict()   #index 0
dict_menu_options['Play Mode']          = Menu(lang['Play Mode'], switch_mode, playmode_options)
dict_menu_options['File']               = Menu(lang['File'], switch_file, file_options)
dict_menu_options['Play Speed']         = Menu(lang['Play Speed'], switch_speed, playspeed_options)
dict_menu_options['Brightness']         = Menu(lang['Brightness'], switch_brightness)
dict_menu_options['Date']               = Menu(lang['Date'], change_date, date_options, 0)
dict_menu_options['IP address']         = Menu(lang['IP address'], switch_ip_address, ip_address_options)
dict_menu_options['Refresh Rate']       = Menu(lang['Refresh Rate'], switch_refresh_rate, refresh_rate_options)
dict_menu_options['MAC']                = Menu(lang['MAC'],)
dict_menu_options['MAC(BCD)']           = Menu(lang['MAC(BCD)'],)
dict_menu_options['Window Position']    = Menu(lang['Window Position'],)
dict_menu_options['System State']       = Menu(lang['System State'],)
dict_menu_options['System Info']        = Menu(lang['System Info'],)
dict_menu_options['Language']           = Menu(lang['Language'], switch_language, language_options, present_lang)

#menu_options = [ v for v in dict_menu_options.keys() ] == list(dict_menu_options.keys())            not good
menu_options = list(dict_menu_options.values())
logger.debug(dict_menu_options)
#logger.debug(menu_options)

def load_info():
    try:
        global present_video, present_netstatus, present_hdmistatus, present_locationstatus
        global present_mode, present_speed, present_bright, present_lang, present_ip_address
        global send_par_status, exit_status
        tmp_s = ''
        present_lang = 0
        present_video = 0
        mtime_1 = 0
        mtime_present = 0
        mtime_netstatus = 0
        mtime_hdmistatus = 0
        mtime_locationstatus = os.path.getmtime('/home/Ym/data/xy_location.conf')
        mtime_refresh = 0
        mtime_bright = 0
        mtime_config = 0
        lockMTime = 0
        
        lcdpipe = '/etc/lcdpipe'
        if not os.path.exists(lcdpipe):
            os.mkfifo(lcdpipe)
        fd_pp =  os.open(lcdpipe, os.O_RDONLY | os.O_NONBLOCK)
        f_pp = open(fd_pp, 'r')

        #fd_pp = f_pp.fileno()
        #fcntl.fcntl(fd_pp, fcntl.F_SETFL, flag | os.O_NONBLOCK)
        
        get_time = time.localtime()
        dict_menu_options['Date'].options[0].current_option = get_time.tm_year%2000
        dict_menu_options['Date'].options[1].current_option = get_time.tm_mon
        dict_menu_options['Date'].options[2].current_option = get_time.tm_mday
        dict_menu_options['Date'].options[3].current_option = get_time.tm_hour
        dict_menu_options['Date'].options[4].current_option = get_time.tm_min

        with open('/home/Ym/data/lang.data') as fd:
            tmp_s = fd.readline().split('\n')[0]
            if tmp_s.isdigit():
                present_lang = int(tmp_s)
        dict_menu_options['Language'].current_option = present_lang

        with open('/etc/network/interfaces') as fd:
            lines = fd.readlines()
        for line in lines:
            if 'iface eth0 inet dhcp' in line:
                present_ip_address = 1
        dict_menu_options['IP address'].current_option = present_ip_address

        while 1:
            time.sleep(0.09)
            get_s = f_pp.read()
            if get_s.rfind('1') > get_s.rfind('0'):
                logger.debug('get_s = %s, will set send_par_status = 1 ... '%get_s)
                send_par_status = 1
            if get_s.rfind('0') > get_s.rfind('1'):
                logger.debug('get_s = %s, will set send_par_status = 0 ... '%get_s)
                send_par_status = 0
            if 'C' in get_s:
                logger.debug('get_s = %s, will set exit_status = 1 ... '%get_s)
                exit_status = 1
            
            '''
            if mtime_1 != os.path.getmtime('/home/Ym/data/1.data'):
                mtime_1 = os.path.getmtime('/home/Ym/data/1.data')
                fd = open('/home/Ym/data/1.data')
                Sum = int(fd(readline().split('\n')[0])
                fd.close()
            '''
    
            if mtime_1 != os.path.getmtime('/home/Ym/data/filelist1.txt'):
                logger.debug('filelist1 change...')
                file_options.clear()
                mtime_1 = os.path.getmtime('/home/Ym/data/filelist1.txt')
                with open('/home/Ym/data/filelist1.txt') as fd:
                    lines = fd.readlines()
                for line in lines:
                    file_options.append(line.split(' '))
                #[['0', '-Loof-', '225\n'], ['1', '?????1', '46\n'], ['2', '??6', '23\n']]
                logger.debug(file_options)
                dict_menu_options['File'].set_option()
            
            if mtime_present != os.path.getmtime('/home/Ym/data/present.data'):
                logger.debug('present video change...')
                mtime_present = os.path.getmtime('/home/Ym/data/present.data')
                with open('/home/Ym/data/present.data') as fd:
                    tmp_s = fd.readline().split('\n')[0]
                if tmp_s.isdigit():
                    present_video = int(tmp_s)
                logger.debug('present video is %d ...' %(present_video))
                
            if mtime_netstatus != os.path.getmtime('/home/Ym/data/netstatus.data'):
                logger.debug('present netstatus change...')
                mtime_netstatus = os.path.getmtime('/home/Ym/data/netstatus.data')
                with open('/home/Ym/data/netstatus.data') as fd:
                    tmp_s = fd.readline().split('\n')[0]
                if tmp_s.isdigit():
                    present_netstatus = int(tmp_s)
                logger.debug('present_netstatus is %d ...' %(present_netstatus))

            if mtime_hdmistatus != os.path.getmtime('/home/Ym/data/hdmistatus.data'):
                logger.debug('present hdmistatus change...')
                mtime_hdmistatus = os.path.getmtime('/home/Ym/data/hdmistatus.data')
                with open('/home/Ym/data/hdmistatus.data') as fd:
                    tmp_s = fd.readline().split('\n')[0]
                if tmp_s.isdigit():
                    present_hdmistatus = int(tmp_s)
                logger.debug('present_hdmistatus is %d ...' %(present_hdmistatus))
    
            if mtime_locationstatus != os.path.getmtime('/home/Ym/data/xy_location.conf'):
                logger.debug('present locationstatus change...')
                mtime_locationstatus = os.path.getmtime('/home/Ym/data/xy_location.conf')
                present_locationstatus = 1
    
            if mtime_bright != os.path.getmtime('/home/Ym/data/bright.data'):
                logger.debug('brightness change...')
                mtime_bright = os.path.getmtime('/home/Ym/data/bright.data')
                with open('/home/Ym/data/bright.data') as fd:
                    tmp_s = fd.readline().split('\n')[0]
                if tmp_s.isdigit():
                    bright = int(tmp_s)
                logger.debug('bright is %d ...' %(bright))
                dict_menu_options['Brightness'].current_option = bright
                present_bright = bright
    
            if mtime_refresh != os.path.getmtime('/home/Ym/data/refresh.data'):
                logger.debug('refresh rate change...')
                mtime_refresh = os.path.getmtime('/home/Ym/data/refresh.data')
                with open('/home/Ym/data/refresh.data') as fd:
                    tmp_s = fd.readline().split('\n')[0]
                if tmp_s.isdigit():
                    refresh = int(tmp_s)
                logger.debug('refresh is %d ...' %(refresh))
                dict_menu_options['Refresh Rate'].current_option = refresh
            
            if mtime_config != os.path.getmtime(config_file):
                logger.debug('config.yaml change...')
                fd = os.open(config_file, os.O_RDONLY)
                logger.debug('[load_info], may block in acquire rlock ...')  
                rlock = struct.pack('hhillqq', fcntl.F_RDLCK, 0, 0, 0, 0, 0, 0)
                fcntl.fcntl(fd, fcntl.F_SETLKW, rlock)
                logger.debug('[load_info], have rlock ...')  
                f = open(config_file)
                config = yaml.load(f, Loader=yaml.FullLoader)
                logger.debug('[load_info], may ulock ...')  
                ulock = struct.pack('hhillqq', fcntl.F_UNLCK, 0, 0, 0, 0, 0, 0)
                fcntl.fcntl(fd, fcntl.F_SETLKW, ulock)
                logger.debug('[load_info], have ulock ...')  
                os.close(fd)

                logger.debug("config = %s" %(config))
                speed = config['speed']
                logger.debug('speed is %d ...' %(speed))       
                dict_menu_options['Play Speed'].current_option = speed - 1
                present_speed = speed - 1
                video = config['fileNo']
                logger.debug('video is %d ...' %(video))       
                # reset beyond the boundary
                if video >= len(file_options):
                    logger.debug('video is %d, beyond the boundary, reset  ...' %(video))       
                    dict_menu_options['File'].current_option = 0
                    dict_menu_options['File'].do()
                else:
                    dict_menu_options['File'].current_option = video

                mode = config['status']
                logger.debug('mode is %d ...' %(mode))
                dict_menu_options['Play Mode'].current_option = mode
                present_mode = mode
                mtime_config = os.path.getmtime(config_file)
                
            if t_load_info_exitBit:
                os.close(fd_pp)
                break
                #thread.exit()
                
    except Exception as result:
        traceback.print_exc()
        logger.debug('[MT], thread1 exit ... ')
        os.system('ps aux | grep lcd_client | grep -v grep | awk \'{print $2}\' | xargs kill -9')

def back_to_main():
    global present_interface, key_trigger_status
    i = 0
    while i < 35:
        i += 1
        if key_trigger_status:
            if present_interface == 0:
                break
            else:
                i = 0
                key_trigger_status = False
                continue
        time.sleep(1)
    if not key_trigger_status:
        present_interface = 0
    #GPIO.output(KEY_MENU, GPIO.LOW)


def main():

    
    global present_interface, present_menu, config_status, config_date_status, key_trigger_status, t_load_info_exitBit
    global present_locationstatus
    filtrate_string_bak = ''
    tmp_s = ''
    s_n_existflag = 0
    b_g_existflag = 0
    net_signal = 0
    gps_satel = 0
    file_name_len_i = 0
    sleep_i = 0

    #t_key_trigger = threading.Thread(target=key_trigger, args=())
    #t_key_trigger.start()
    t_load_info = threading.Thread(target=load_info, args=())
    t_load_info.start()

    #serial = spi(port=0, device=0, gpio_DC=23, gpio_RST=24)
    #device = st7567(serial)
    
    logger.debug('[MT], 1, sys.argv[1:] %s' % sys.argv[1:])
    #device = get_device()

    # use custom font
    #font_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
    #    'fonts', 'Aakt.ttf'))
    #font2 = ImageFont.truetype(font_path, 16)

    '''
    term = terminal(device, font2)
    term.animate = False
    term.println('Progress bar')
    term.println('------------')
    for mill in range(0, 10001, 25):
        term.puts('\rPercent: {0:0.1f} %'.format(mill / 100.0))
        term.flush()
    time.sleep(2)
    term.clear()
    '''

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    logger.debug('[MT], create socket successful...')
    ip_port = ('127.0.0.1', 58471)
    client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)

    while True:
        #client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)         //
        client.sendto(('0 0 0 0,0').encode('utf-8'), ip_port) 
        #client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)

        if present_locationstatus == 1:
            client.sendto(('0 0 3 '+'Set windows... ').encode('utf-8'), ip_port)
            time.sleep(2)
            present_locationstatus = 0

        if send_par_status == 1:
            while send_par_status != 0:
                #with canvas(device) as draw:
                #    draw.text((0, 18), 'Send to TX503... ', font=font2, fill='white')
                client.sendto(('0 0 3 '+'Send to TX503... ').encode('utf-8'), ip_port)
                time.sleep(0.2)
            #with canvas(device) as draw:
            #    draw.text((0, 18), 'Send Done! ', font=font2, fill='white')
            client.sendto(('0 0 0 0,0').encode('utf-8'), ip_port) 
            client.sendto(('0 0 3 '+'Send Done! ').encode('utf-8'), ip_port)
            time.sleep(3)
        if exit_status == 1:
            logger.debug('exit_status is 1, will exit...')
            t_load_info_exitBit = True
            #t_load_info.exit()
            t_load_info.join()
            sys.exit()
        
        if present_interface == 0:
            #pass
            #logger.debug('[MT], In main interface ... ')
            #client.sendto(('0 0 3 '+interface_options[present_interface].name[present_lang]).encode('utf-8'), ip_port)         #Main
            if present_hdmistatus == 0:
                client.sendto(('0 0 3 '+dict_menu_options['Play Mode'].get_option(present_mode)).encode('utf-8'), ip_port)
            else:
                client.sendto(('0 0 3 '+lang['HDMI'][present_lang]).encode('utf-8'), ip_port)
            
            with open('/home/Ym/data/extern.data') as fd:
                tmp_s = fd.readline().split('\n')[0]
            if tmp_s.isdigit():
                s_n_existflag = int(tmp_s)
            if s_n_existflag == 2:
                with open('/home/Ym/data/4Gsignal.data') as fd:
                    tmp_s = fd.readline().split('\n')[0]
                if tmp_s.isdigit():
                    net_signal = int(tmp_s)
                logger.debug('net signal is %d ...' %(net_signal))
                if net_signal <= 0 or net_signal > 31:
                    net_signal = 1
                else:
                    net_signal *= 0.2
                if net_signal == 0:
                    net_signal = 1
                client.sendto(('0 16 1 4G:').encode('utf-8'), ip_port)
                client.sendto(('0 19 5 0,%d'%net_signal).encode('utf-8'), ip_port)

            with open('/home/Ym/data/gettime.data') as fd:
                tmp_s = fd.readline().split('\n')[0]
            if tmp_s.isdigit():
                b_g_existflag = int(tmp_s)
            if b_g_existflag == 2:
                with open('/home/Ym/data/satel.data') as fd:
                    tmp_s = fd.readline().split('\n')[0]
                if tmp_s.isdigit():
                    gps_satel = int(tmp_s)
                logger.debug('gps satel is %d ...' %(gps_satel))
                client.sendto(('1 15 1 GPS:%d'%gps_satel).encode('utf-8'), ip_port)

            file_name_len = len(dict_menu_options['File'].get_option(present_video))
            #logger.debug('[MT], file_name_len = %d.' %(file_name_len))
            client.sendto(('2 0 3 '+lang['Playing'][present_lang]+':'+dict_menu_options['File'].get_option(present_video)[file_name_len_i:]).encode('utf-8'), ip_port)       
            filtrate_string = '[MT], %d %d/%d %s ... ' %(present_video, file_name_len_i, file_name_len, dict_menu_options['File'].get_option(present_video)[file_name_len_i:])
            if filtrate_string != filtrate_string_bak:
              filtrate_string_bak = filtrate_string
              logger.debug(filtrate_string)
            if sleep_i == 10:
                sleep_i = 0
                if file_name_len != 0:
                    file_name_len_i %= file_name_len
                    file_name_len_i += 1
                if file_name_len_i == file_name_len:
                    file_name_len_i = 0
            sleep_i += 1
            #draw.text((0, 0), interface_options[present_interface].name[present_lang]+' ', font=font2, fill='white')
            #draw.text((0, 18), 'Spd:'+dict_menu_options['Play Speed'].get_option()+'   Bri:'+dict_menu_options['Brightness'].get_option()+' ', font=font2, fill='white')
            if present_lang == 0:
                client.sendto(('4 0 3 '+'Spd:'+dict_menu_options['Play Speed'].get_option(present_speed)+'  Bri:'+dict_menu_options['Brightness'].get_option(present_bright)).encode('utf-8'), ip_port)
                #draw.text((0, 18), 'Spd:'+dict_menu_options['Play Speed'].get_option()+'  Bri:'+dict_menu_options['Brightness'].get_option()+' ', font=font2, fill='white')
            elif present_lang == 1:
                client.sendto(('4 0 3 '+'速度:'+dict_menu_options['Play Speed'].get_option(present_speed)+'  亮度:'+dict_menu_options['Brightness'].get_option(present_bright)).encode('utf-8'), ip_port)
                #draw.text((0, 18), '速度:'+dict_menu_options['Play Speed'].get_option()+'  亮度:'+dict_menu_options['Brightness'].get_option()+' ', font=font2, fill='white')

            if present_netstatus == 1:
                client.sendto(('6 0 3 '+lang['online'][present_lang]).encode('utf-8'), ip_port)

            client.sendto(('6 11 1 '+dict_menu_options['Date'].get_option()).encode('utf-8'), ip_port)
            #draw.text((0, 36), dict_menu_options['Date'].get_option()+' ', font=font2, fill='white')
            #draw.text((0, 18), 'Hello Displayer+-', font=font2, fill='white')
            #logger.debug(menu_options[9].get_option())
        elif present_interface == 1:
            if config_status:
                if menu_options[present_menu].name == lang['Date']:
                    #pass
                    if config_date_status:
                        client.sendto(('0 0 3 '+menu_options[present_menu].get_option_object().name[present_lang]).encode('utf-8'), ip_port)
                        client.sendto(('2 0 3 '+'↑↓ '+menu_options[present_menu].get_option_object().get_option()).encode('utf-8'), ip_port)
                        #draw.text((0, 0), menu_options[present_menu].get_option_object().name[present_lang]+' ', font=font2, fill='white')
                        #draw.text((0, 18), ' + - '+menu_options[present_menu].get_option_object().get_option()+' ', font=font2, fill='white')
                    else:
                        client.sendto(('0 0 3 '+menu_options[present_menu].get_option_object().name[present_lang]).encode('utf-8'), ip_port)
                        client.sendto(('2 10 3 '+menu_options[present_menu].get_option_object().get_option()).encode('utf-8'), ip_port)
                        #draw.text((0, 0), menu_options[present_menu].get_option_object().name[present_lang]+' ', font=font2, fill='white')
                        #draw.text((33, 18), menu_options[present_menu].get_option_object().get_option()+' ', font=font2, fill='white')
                else:
                    #logger.debug(menu_options[9].get_option())     #MT error no exit
                    #pass
                    client.sendto(('0 0 3 '+menu_options[present_menu].name[present_lang]).encode('utf-8'), ip_port)
                    #draw.text((0, 0), menu_options[present_menu].name[present_lang]+' ', font=font2, fill='white')
                    if menu_options[present_menu].name == lang['Play Mode']:
                        if menu_options[present_menu].current_option == 2:
                            client.sendto(('2 0 3 '+'↑↓ '+menu_options[present_menu].get_option()+lang['2Adjust file and speed is invalid'][present_lang]).encode('utf-8'), ip_port)
                        elif menu_options[present_menu].current_option == 3:
                            client.sendto(('2 0 3 '+'↑↓ '+menu_options[present_menu].get_option()+lang['3Adjust file and speed is invalid'][present_lang]).encode('utf-8'), ip_port)
                        else:
                            client.sendto(('2 0 3 '+'↑↓ '+menu_options[present_menu].get_option()).encode('utf-8'), ip_port)
                            #draw.text((0, 18), menu_options[present_menu].get_option()+' ', font=font2, fill='white')
                    if menu_options[present_menu].name == lang['IP address']:
                        client.sendto(('2 0 3 '+'↑↓ '+lang['ETH'][present_lang]+":"+menu_options[present_menu].get_option()).encode('utf-8'), ip_port)                
                    else:
                        if menu_options[present_menu].name == lang['File']:
                            client.sendto(('0 10 3 '+str(int(menu_options[present_menu].get_option_object()[0]) + 1)).encode('utf-8'), ip_port)
                            #draw.text((75, 0), str(int(menu_options[present_menu].get_option_object()[0]) + 1) + ' ', font=font2, fill='white')
                        client.sendto(('2 0 3 '+'↑↓ '+menu_options[present_menu].get_option()).encode('utf-8'), ip_port)

                        #draw.text((0, 18), ' + - '+menu_options[present_menu].get_option()+' ', font=font2, fill='white')
    
            else:
                #logger.debug(menu_options[9].get_option())    #MT error no exit
                client.sendto(('0 0 3 '+menu_options[present_menu].name[present_lang]).encode('utf-8'), ip_port)
                #draw.text((0, 0), menu_options[present_menu].name[present_lang]+' ', font=font2, fill='white')
                if menu_options[present_menu].name == lang['Play Mode']:
                    if menu_options[present_menu].current_option == 2:
                        client.sendto(('2 0 3 '+menu_options[present_menu].get_option()+lang['2Adjust file and speed is invalid'][present_lang]).encode('utf-8'), ip_port)
                    elif menu_options[present_menu].current_option == 3:
                        client.sendto(('2 0 3 '+menu_options[present_menu].get_option()+lang['3Adjust file and speed is invalid'][present_lang]).encode('utf-8'), ip_port)
                    else:
                        client.sendto(('2 0 3 '+menu_options[present_menu].get_option()).encode('utf-8'), ip_port)
                        #draw.text((0, 18), menu_options[present_menu].get_option()+' ', font=font2, fill='white')
                if menu_options[present_menu].name == lang['IP address']:
                    client.sendto(('2 0 3 '+get_ip()).encode('utf-8'), ip_port)    
                else:
                    #pass
                    if menu_options[present_menu].name == lang['File']:
                        client.sendto(('0 10 3 '+str(int(menu_options[present_menu].get_option_object()[0]) + 1)).encode('utf-8'), ip_port)
                        #draw.text((75, 0), str(int(menu_options[present_menu].get_option_object()[0]) + 1) + ' ', font=font2, fill='white')
                    client.sendto(('2 0 3 '+menu_options[present_menu].get_option()).encode('utf-8'), ip_port)
                    #draw.text((33, 18), menu_options[present_menu].get_option()+' ', font=font2, fill='white')

    
        if GPIO.input(KEY_UP) == GPIO.LOW:
            logger.debug('UP')
            key_trigger_status = True
            if present_interface == 1:
                if config_status:
                    if menu_options[present_menu].name == lang['Date'] and config_date_status:
                        menu_options[present_menu].get_option_object().current_option += 1
                    else:
                        menu_options[present_menu].current_option += 1
                        logger.debug('present_menu: %d' %menu_options[present_menu].current_option)
                else:
                    while GPIO.input(KEY_UP) == GPIO.LOW:
                        pass
                    present_menu += 1
        if GPIO.input(KEY_DOWN) == GPIO.LOW:
            logger.debug('DOWN')
            key_trigger_status = True
            if present_interface == 1:
                if config_status:
                    if menu_options[present_menu].name == lang['Date'] and config_date_status:
                        menu_options[present_menu].get_option_object().current_option -= 1
                    else:
                        menu_options[present_menu].current_option -= 1
                        logger.debug('menu_options[present_menu].current_option: %d' %menu_options[present_menu].current_option)
                else:
                    while GPIO.input(KEY_DOWN) == GPIO.LOW:
                        pass
                    present_menu -= 1
        if config_status:
            if menu_options[present_menu].name == lang['Date'] and config_date_status:
                menu_options[present_menu].get_option_object().set_option()
            else:
                menu_options[present_menu].set_option()
                #logger.debug('current_option: %d, present_lang: %d' %(menu_options[present_menu].current_option, present_lang))
        else:
            present_menu %= len(menu_options)
        if GPIO.input(KEY_MENU) == GPIO.LOW:
            logger.debug('MENU')
            key_trigger_status = True
            while GPIO.input(KEY_MENU) == GPIO.LOW:
                pass
            ## present_menu = 0
            if menu_options[present_menu].name == lang['Date'] and config_status:
                config_date_status = True
                config_status = False
                present_interface = 1
                if config_status == False:
                    menu_options[present_menu].do()
            else:
                present_interface += 1
            if present_interface == 1:
                key_trigger_status = False
                threading.Thread(target=back_to_main, args=()).start()
        present_interface %= len(interface_options)
        if GPIO.input(KEY_CONFIG) == GPIO.LOW:
            logger.debug('CONFIG')
            key_trigger_status = True
            while GPIO.input(KEY_CONFIG) == GPIO.LOW:
                pass
            if present_interface == 1:
                if menu_options[present_menu].name == lang['Date']:
                    config_status = True
                    config_date_status = not config_date_status
                elif menu_options[present_menu].name == lang['MAC'] or menu_options[present_menu].name == lang['MAC(BCD)'] or menu_options[present_menu].name == lang['Window Position'] or menu_options[present_menu].name == lang['System Info']:
                    pass
                else:
                    config_status = not config_status
                    if config_status == False:
                        menu_options[present_menu].do()
                        #logger.debug('present_lang: %d' %(present_lang))
        time.sleep(0.16)
        

            
'''
def main():
    global t_load_info, t_load_info_exitBit

    #while 1:
        #lcdpipe = '/etc/lcdpipe'
        #if not os.path.exists(lcdpipe):
            #os.mkfifo(lcdpipe)
        #fd_pp =  os.open(lcdpipe, os.O_RDONLY | os.O_NONBLOCK)
        #client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #logger.debug('[MT], create socket successful...')
        #ip_port = ('127.0.0.1', 58471)
        #client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)
    logger.debug(menu_options[9].get_option())
        #time.sleep(0.1)
    #t_load_info = threading.Thread(target=load_info, args=())
    #t_load_info.start()
    #t_load_info_exitBit = True
    #t_load_info.exit()
'''


if __name__ == '__main__':
    try:
        logger.debug('------------------------------------------------------------------')
        main()
        #raise(KeyboardInterrupt)
    #except Exception as e:
    #    traceback.print_exc()
    #    t_load_info_exitBit = True
    #    t_load_info.join()
    #    sys.exit()
    except Exception as result:
        traceback.print_exc()
        #logger.debug(' 2 unkown error: %s' % result)
        logger.debug('[MT], exit ... ')
        os.system('ps aux | grep lcd_client | grep -v grep | awk \'{print $2}\' | xargs kill -9')
        #sys.exit()
    #except IndexError as e:
    #    traceback.print_exc()
    #    pass
    #except SystemExit:
    #    pass
    #except KeyboardInterrupt:
    #    pass
else:
    logger.debug('come from another module')
    
    
    
    

