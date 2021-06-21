#!/usr/bin/env python
# -*- coding: utf-8 -*-
#   > Author: LaiQiMing
#   > Mail: 13536343225@139.com

import os
import sys
import time
import socket
import logging
import datetime
import traceback
import threading
import collections
import RPi.GPIO as GPIO

lang = {
        "Main":("Main", "主界面"),
        "Menu":("Menu", "菜单"),
        "Cycle":("Cycle", "循环"),
        "Single":("Single", "单一"),
        "HW-Sync":("HW-Sync", "硬件-同步"),
        "SW-Sync":("SW-Sync", "软件-同步"),
        "Stop":("Stop", "停止"),
        "Year":("Year", "年"),
        "Month":("Month", "月"),
        "Day":("Day", "日"),
        "Hour":("Hour", "时"),
        "Minute":("Minute", "分"),
        "Second":("Second", "秒"),
        "chinese":("chinese", "中文"),
        "english":("english", "英文"),
        "Play Mode":("Play Mode", "播放模式"),
        "File":("File", "文件"),
        "Play Speed":("Play Speed", "播放速度"),
        "Brightness":("Brightness", "亮度"),
        "Date":("Date", "日期时间"),
        "Refresh Rate":("Refresh Rate", "刷新率"),
        "MAC":("MAC", "物理地址"),
        "MAC(BCD)":("MAC(BCD)", "物理地址(BCD)"),
        "Window Position":("Window Position", "窗口位置"),
        "System Info":("System Info", "系统信息"),
        "Language":("Language", "语言"),
        "":("", ""),
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

current_interface_option = 0
current_menu_option = 0
current_lang_option = 1
current_speed_option = 0
current_refresh_rate_option = 0
config_status = False
config_date_status = True
key_trigger_status = False
t_load_info_exitBit = False
logger = logging.getLogger()
logger.setLevel(logging.NOTSET)
c_h = logging.StreamHandler()
formatter = logging.Formatter('L, [%(asctime)s] %(levelname)s -- : %(message)s ')
c_h.setFormatter(formatter)
logger.addHandler(c_h)

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
        if self.name == lang["Year"]:
            return str(self.current_option + 2000)
        elif self.name == lang["Month"]:
            return str(self.current_option + 1)
        elif self.name == lang["Day"]:
            return str(self.current_option + 1)
        else:
            return str(self.current_option)

    def set_option(self):
        logger.debug("Date self.current_option : %d" %(self.current_option))
        if self.name == lang["Year"]:
            self.current_option = self.current_option % 100
        elif self.name == lang["Month"]:
            self.current_option = self.current_option % 12
        elif self.name == lang["Day"]:
            self.current_option = self.current_option % get_current_months()
        elif self.name == lang["Hour"]:
            self.current_option = self.current_option % 24
        elif self.name == lang["Minute"]:
            self.current_option = self.current_option % 60
        elif self.name == lang["Second"]:
            self.current_option = self.current_option % 60

class Language:
    def __init__(self, name):
        self.name = name

class Menu:
    def __init__(self, name, something=None, options=[], current_option=0):
        self.name = name
        self.something = something
        self.options = options
        self.current_option = current_option

    def get_option(self):
        if self.name == lang["Play Speed"]:
            return self.options[self.current_option]
            ''' Real-time speed status
            with open('/home/Ym/data/speed.data') as fd:
                 speed = int(fd.readline().split('\n')[0])
            self.current_option = speed - 1
            return self.options[self.current_option]
            '''
        elif self.name == lang["Brightness"]:
            return str(self.current_option)
            ''' Real-time brightness status
            with open('/home/Ym/data/bright.data') as fd:
                 bright = fd.readline().split('\n')[0]
            self.current_option = int(bright)
            return bright
            '''
        elif self.name == lang["Date"]:
            return time.strftime('%y/%m/%d %H:%M:%S', time.localtime())
            #return time.strftime('%y/%m/%d %H:%M:%S', time.localtime())
        elif self.name == lang["Refresh Rate"]:
            return self.options[self.current_option]
        elif self.name == lang["File"]:
            if bool(self.options):
                return self.options[self.current_option][1]
            else:
                return ''
        elif self.name == lang["MAC"]:
            with open('/home/Ym/data/MACAddr.data') as fd:
                MAC = list(fd.readline())
            MAC.insert(4,'-')
            MAC.insert(9,'-')
            return ''.join(MAC)
        elif self.name == lang["MAC(BCD)"]:
            with open('/home/Ym/data/MACAddrBCD.data') as fd:
                MAC = list(fd.readline())
            MAC.insert(4,'-')
            MAC.insert(9,'-')
            return ''.join(MAC)
        elif self.name == lang["Window Position"]:
            with open('/YM/config/xy_location.conf') as fd:
                line = fd.readline().split('\n')[0]           #!! will remove \n
            X = line.split(':')[0]
            Y = line.split(':')[1]
            W = line.split(':')[2]
            H = line.split(':')[3]
            if current_lang_option == 0:
                return '  XY: (%s, %s) \n  WH: %s, %s' % (X,Y,W,H)
            elif current_lang_option == 1:
                return '  XY: (%s, %s) \n  宽高: %s, %s' % (X,Y,W,H)
        elif self.name == lang["System Info"]:
            with open('/home/Ym/data/version.data') as fd:
                line = fd.readline().split('\n')[0]           #!! will remove \n
            SysVer = line.split(' ')[0]
            FpgaVer = line.split(' ')[1]
            if current_lang_option == 0:
                return '   System: U%s \n   Fpga: V%s' % (SysVer,FpgaVer)
            elif current_lang_option == 1:
                return '   系统: U%s \n   硬件: V%s' % (SysVer,FpgaVer)
        else:
            if type(self.options) == list:
                if bool(self.options):
                    return self.options[self.current_option].name[current_lang_option]
                else:
                    return " "
            elif type(self.options) == tuple:
                return self.options[self.current_option]

    def get_option_object(self):
        if self.name == lang["Date"]:
            return self.options[self.current_option]
        elif self.name == lang["File"]:
            if bool(self.options):
                return self.options[self.current_option]
            else:
                return ['-1', '', '']

    def set_option(self):
        #logger.debug("Menu self.current_option : %d" %(self.current_option))
        if self.name == lang["Brightness"]:
            self.current_option %= 256
        elif bool(self.options):
            self.current_option %= len(self.options)
            #logger.debug("Menu self.current_option : %d" %(self.current_option))

    def do(self):
        if bool(self.something):
            self.something(self.options, self.current_option)


def get_ip():
    pass

def switch_mode(options, current_option):
    logger.debug('current option is : %s' %(options[current_option]))
    os.system('echo %d > /home/Ym/data/mode.data' % current_option)

def switch_file(options, current_option):
    if bool(options):
        logger.debug('current option is : %s' %(options[current_option]))
    os.system('echo %d > /home/Ym/data/video.data' % current_option)

def switch_speed(options, current_option):
    logger.debug('current option is :%d %s' %(current_option, options[current_option]))
    os.system('echo %d > /home/Ym/data/speed.data' % (current_option + 1))

def switch_brightness(options, current_option):
    logger.debug('current option is : %d' %current_option)
    os.system('echo %d > /home/Ym/data/bright.data' % current_option)

def change_date(options, current_option):
    logger.debug('current option is : %d' %current_option)

def switch_refresh_rate(options, current_option):
    logger.debug('current option is : %s' %(options[current_option]))
    os.system('echo %d > /home/Ym/data/refresh.data' % current_option)

def switch_language(options, current_option):
    global current_lang_option
    current_lang_option = current_option
    logger.debug('current option is : %s %d' %(options[current_option].name[current_lang_option], current_lang_option))

interface_options = [
        Interface(lang["Main"]),
        Interface(lang["Menu"])
        ]
playmode_options = [
        PlayMode(lang["Cycle"]),
        PlayMode(lang["Single"]),
        PlayMode(lang["HW-Sync"]),
        PlayMode(lang["SW-Sync"]),
        PlayMode(lang["Stop"])
        ]
file_options = []
playspeed_options = ("0.2", "0.4", "0.6", "0.8", "1.0", "1.5", "2.0", "3.0")
date_options = [
        Date(lang["Year"]),
        Date(lang["Month"]),
        Date(lang["Day"]),
        Date(lang["Hour"]),
        Date(lang["Minute"]),
        Date(lang["Second"])
        ]
refresh_rate_options = ("60 Hz", "30 Hz", "20 Hz", "15 Hz", "12 Hz", "10 Hz")
language_options = [
        Language(lang["english"]),
        Language(lang["chinese"]),
        ]
dict_menu_options = collections.OrderedDict()
dict_menu_options["Play Mode"]          = Menu(lang["Play Mode"], switch_mode, playmode_options)
dict_menu_options["File"]               = Menu(lang["File"], switch_file, file_options)
dict_menu_options["Play Speed"]         = Menu(lang["Play Speed"], switch_speed, playspeed_options, current_speed_option)
dict_menu_options["Brightness"]         = Menu(lang["Brightness"], switch_brightness)
dict_menu_options["Date"]               = Menu(lang["Date"], change_date, date_options, 0)
dict_menu_options["Refresh Rate"]       = Menu(lang["Refresh Rate"], switch_refresh_rate, refresh_rate_options, current_refresh_rate_option)
dict_menu_options["MAC"]                = Menu(lang["MAC"],)
dict_menu_options["MAC(BCD)"]           = Menu(lang["MAC(BCD)"],)
dict_menu_options["Window Position"]    = Menu(lang["Window Position"],)
dict_menu_options["System Info"]        = Menu(lang["System Info"],)
dict_menu_options["Language"]           = Menu(lang["Language"], switch_language, language_options, current_lang_option)

#menu_options = [ v for v in dict_menu_options.keys() ] == list(dict_menu_options.keys())            not good
menu_options = list(dict_menu_options.values())
logger.debug(menu_options)

def load_info():
    mtime_1 = 0
    mtime_present = 0
    mtime_video = 0
    mtime_refresh = 0
    mtime_bright = 0
    mtime_speed = 0
    mtime_mode = 0
    lockMTime = 0
    while 1:
        time.sleep(0.09)
        '''
        if mtime_1 != os.path.getmtime("/home/Ym/data/1.data"):
            mtime_1 = os.path.getmtime("/home/Ym/data/1.data")
            fd = open('/home/Ym/data/1.data')
            Sum = int(fd(readline().split('\n')[0])
            fd.close()
        '''
        if mtime_1 != os.path.getmtime("/home/Ym/data/filelist1.txt"):
            logger.debug("file list change...")
            file_options.clear()
            mtime_1 = os.path.getmtime("/home/Ym/data/filelist1.txt")
            with open('/home/Ym/data/filelist1.txt') as fd:
                lines = fd.readlines()
            for line in lines:
                file_options.append(line.split(' '))
            #[['0', '-Loof-', '225\n'], ['1', '?????1', '46\n'], ['2', '??6', '23\n']]
            logger.debug(file_options)
            dict_menu_options['File'].set_option()

        if mtime_video != os.path.getmtime("/home/Ym/data/video.data"):
            logger.debug("video change...")
            mtime_video = os.path.getmtime("/home/Ym/data/video.data")
            with open('/home/Ym/data/video.data') as fd:
                 video = int(fd.readline().split('\n')[0])
            dict_menu_options['File'].current_option = video

        if mtime_speed != os.path.getmtime("/home/Ym/data/speed.data"):
            logger.debug("speed change...")
            mtime_speed = os.path.getmtime("/home/Ym/data/speed.data")
            with open('/home/Ym/data/speed.data') as fd:
                 speed = int(fd.readline().split('\n')[0])
            dict_menu_options['Play Speed'].current_option = speed - 1

        if mtime_bright != os.path.getmtime("/home/Ym/data/bright.data"):
            logger.debug("brightness change...")
            mtime_bright = os.path.getmtime("/home/Ym/data/bright.data")
            with open('/home/Ym/data/bright.data') as fd:
                 bright = int(fd.readline().split('\n')[0])
            dict_menu_options['Brightness'].current_option = bright

        if mtime_refresh != os.path.getmtime("/home/Ym/data/refresh.data"):
            logger.debug("refresh rate change...")
            mtime_refresh = os.path.getmtime("/home/Ym/data/refresh.data")
            with open('/home/Ym/data/refresh.data') as fd:
                 refresh = int(fd.readline().split('\n')[0])
            dict_menu_options['Refresh Rate'].current_option = refresh

        if t_load_info_exitBit:
            break
            #thread.exit()

def back_to_main():
    global current_interface_option, key_trigger_status
    i = 0
    while i < 35:
        i += 1
        if key_trigger_status:
            if current_interface_option == 0:
                break
            else:
                i = 0
                key_trigger_status = False
                continue
        time.sleep(1)
    if not key_trigger_status:
        current_interface_option = 0
    #GPIO.output(KEY_MENU, GPIO.LOW)

t_load_info = threading.Thread(target=load_info, args=())
t_load_info.start()


def main():
    global current_interface_option, current_menu_option, config_status, config_date_status, key_trigger_status, t_load_info_exitBit
    #t_key_trigger = threading.Thread(target=key_trigger, args=())
    #t_key_trigger.start()

    #serial = spi(port=0, device=0, gpio_DC=23, gpio_RST=24)
    #device = st7567(serial)
    
    logger.debug("[MT], 1, sys.argv[1:] %s" % sys.argv[1:])
    #device = get_device()

    # use custom font
    #font_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
    #    'fonts', 'Aakt.ttf'))
    #font2 = ImageFont.truetype(font_path, 16)

    '''
    term = terminal(device, font2)
    term.animate = False
    term.println("Progress bar")
    term.println("------------")
    for mill in range(0, 10001, 25):
        term.puts("\rPercent: {0:0.1f} %".format(mill / 100.0))
        term.flush()
    time.sleep(2)
    term.clear()
    '''

    parapipe = "/etc/lcdpipe"
    if not os.path.exists(parapipe):
        os.mkfifo(parapipe)
    fd_pp =  os.open(parapipe, os.O_RDONLY | os.O_NONBLOCK)

    BUFSIZE = 1024
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    logger.debug("[MT], create socket successful...")
    ip_port = ('127.0.0.1', 58471)
    client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)

    try:
        while True:
    
            
            get_s = os.read(fd_pp, 1)
            #get_s = bytes.decode(get_s)
            #logger.debug("received msg: %s" % get_s)
            if get_s == b'1':
                logger.debug("received msg: %s" % get_s)
                while get_s != b'0':
                    with canvas(device) as draw:
                        draw.text((0, 18), 'Send to TX503... ', font=font2, fill="white")
                    get_s = os.read(fd_pp, 1)
                    time.sleep(0.2)
                    #logger.debug("received msg: %s" % get_s)
                logger.debug("received msg: %s" % get_s)
                with canvas(device) as draw:
                    draw.text((0, 18), 'Send Done! ', font=font2, fill="white")
                time.sleep(2)
            elif get_s == b'C':
                logger.debug("received msg: %s" % get_s)
                t_load_info_exitBit = True
                #t_load_info.exit()s
                t_load_info.join()
                sys.exit()
                
    
                
            
            #with canvas(device) as draw:
            #client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)         //
            client.sendto(('0 0 0 0,0').encode('utf-8'), ip_port) 
            if current_interface_option == 0:
                #pass
                client.sendto(('0 0 3 '+interface_options[current_interface_option].name[current_lang_option]).encode('utf-8'), ip_port)
                #draw.text((0, 0), interface_options[current_interface_option].name[current_lang_option]+' ', font=font2, fill="white")
                #draw.text((0, 18), 'Spd:'+dict_menu_options['Play Speed'].get_option()+'   Bri:'+dict_menu_options['Brightness'].get_option()+' ', font=font2, fill="white")
                if current_lang_option == 0:
                    client.sendto(('2 0 3 '+'Spd:'+dict_menu_options['Play Speed'].get_option()+'  Bri:'+dict_menu_options['Brightness'].get_option()).encode('utf-8'), ip_port)
                    #draw.text((0, 18), 'Spd:'+dict_menu_options['Play Speed'].get_option()+'  Bri:'+dict_menu_options['Brightness'].get_option()+' ', font=font2, fill="white")
                elif current_lang_option == 1:
                    client.sendto(('2 0 3 '+'速度:'+dict_menu_options['Play Speed'].get_option()+'  亮度:'+dict_menu_options['Brightness'].get_option()).encode('utf-8'), ip_port)
                    #draw.text((0, 18), '速度:'+dict_menu_options['Play Speed'].get_option()+'  亮度:'+dict_menu_options['Brightness'].get_option()+' ', font=font2, fill="white")
                client.sendto(('6 0 3 '+dict_menu_options['Date'].get_option()).encode('utf-8'), ip_port)
                #draw.text((0, 36), dict_menu_options['Date'].get_option()+' ', font=font2, fill="white")
                #draw.text((0, 18), "Hello Displayer+-", font=font2, fill="white")
                #logger.debug(menu_options[9].get_option())
            elif current_interface_option == 1:
                try:
                    if config_status:
                        if menu_options[current_menu_option].name == lang["Date"]:
                            #pass
                            if config_date_status:
                                client.sendto(('0 0 3 '+menu_options[current_menu_option].get_option_object().name[current_lang_option]).encode('utf-8'), ip_port)
                                client.sendto(('2 0 3 '+" + - "+menu_options[current_menu_option].get_option_object().get_option()).encode('utf-8'), ip_port)
                                #draw.text((0, 0), menu_options[current_menu_option].get_option_object().name[current_lang_option]+' ', font=font2, fill="white")
                                #draw.text((0, 18), " + - "+menu_options[current_menu_option].get_option_object().get_option()+' ', font=font2, fill="white")
                            else:
                                client.sendto(('0 0 3 '+menu_options[current_menu_option].get_option_object().name[current_lang_option]).encode('utf-8'), ip_port)
                                client.sendto(('2 10 3 '+menu_options[current_menu_option].get_option_object().get_option()).encode('utf-8'), ip_port)
                                #draw.text((0, 0), menu_options[current_menu_option].get_option_object().name[current_lang_option]+' ', font=font2, fill="white")
                                #draw.text((33, 18), menu_options[current_menu_option].get_option_object().get_option()+' ', font=font2, fill="white")
                        else:
                            logger.debug(menu_options[9].get_option())
                            #pass
                            client.sendto(('0 0 3 '+menu_options[current_menu_option].name[current_lang_option]).encode('utf-8'), ip_port)
                            #draw.text((0, 0), menu_options[current_menu_option].name[current_lang_option]+' ', font=font2, fill="white")
                            if menu_options[current_menu_option].name == lang["MAC"]:
                                client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                                #draw.text((0, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                            elif menu_options[current_menu_option].name == lang["MAC(BCD)"]:
                                client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                                #draw.text((0, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                            elif menu_options[current_menu_option].name == lang["Window Position"]:
                                client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                                #draw.text((0, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                            elif menu_options[current_menu_option].name == lang["System Info"]:
                                client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                                #draw.text((0, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                            else:
                                if menu_options[current_menu_option].name == lang["File"]:
                                    client.sendto(('0 10 3 '+str(int(menu_options[current_menu_option].get_option_object()[0]) + 1)).encode('utf-8'), ip_port)
                                    #draw.text((75, 0), str(int(menu_options[current_menu_option].get_option_object()[0]) + 1) + ' ', font=font2, fill="white")
                                client.sendto(('2 0 3 '+" + - "+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                                #draw.text((0, 18), " + - "+menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
            
                    else:
                        logger.debug(menu_options[9].get_option())
                        client.sendto(('0 0 3 '+menu_options[current_menu_option].name[current_lang_option]).encode('utf-8'), ip_port)
                        #draw.text((0, 0), menu_options[current_menu_option].name[current_lang_option]+' ', font=font2, fill="white")
                        if menu_options[current_menu_option].name == lang["Date"]:
                            client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                            #draw.text((0, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                        elif menu_options[current_menu_option].name == lang["MAC"]:
                            client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                            #draw.text((0, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                        elif menu_options[current_menu_option].name == lang["MAC(BCD)"]:
                            client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                            #draw.text((0, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                        elif menu_options[current_menu_option].name == lang["Window Position"]:
                            client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                            #draw.text((0, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                        elif menu_options[current_menu_option].name == lang["System Info"]:
                            client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                            #draw.text((0, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                        else:
                            #pass
                            if menu_options[current_menu_option].name == lang["File"]:
                                client.sendto(('0 10 3 '+str(int(menu_options[current_menu_option].get_option_object()[0]) + 1)).encode('utf-8'), ip_port)
                                #draw.text((75, 0), str(int(menu_options[current_menu_option].get_option_object()[0]) + 1) + ' ', font=font2, fill="white")
                            client.sendto(('2 0 3 '+menu_options[current_menu_option].get_option()).encode('utf-8'), ip_port)
                            #draw.text((33, 18), menu_options[current_menu_option].get_option()+' ', font=font2, fill="white")
                            
                except Exception as result:
                    break
                    #print("[MT]  1 unkown error: %s" % result)
                    #raise(KeyboardInterrupt)
                    #t_load_info_exitBit = True
                    #t_load_info.join()
                    #sys.exit()
        
            if GPIO.input(KEY_UP) == GPIO.LOW:
                logger.debug("UP")
                key_trigger_status = True
                if current_interface_option == 1:
                    if config_status:
                        if menu_options[current_menu_option].name == lang["Date"] and config_date_status:
                            menu_options[current_menu_option].get_option_object().current_option += 1
                        else:
                            menu_options[current_menu_option].current_option += 1
                            logger.debug("current_menu_option: %d" %menu_options[current_menu_option].current_option)
                    else:
                        while GPIO.input(KEY_UP) == GPIO.LOW:
                            pass
                        logger.debug("2 UP 0 0 4 64,128,0")
                        client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)
                        current_menu_option += 1
            if GPIO.input(KEY_DOWN) == GPIO.LOW:
                logger.debug("DOWN")
                key_trigger_status = True
                if current_interface_option == 1:
                    if config_status:
                        if menu_options[current_menu_option].name == lang["Date"] and config_date_status:
                            menu_options[current_menu_option].get_option_object().current_option -= 1
                        else:
                            menu_options[current_menu_option].current_option -= 1
                            logger.debug("menu_options[current_menu_option].current_option: %d" %menu_options[current_menu_option].current_option)
                    else:
                        while GPIO.input(KEY_DOWN) == GPIO.LOW:
                            pass
                        logger.debug("2 DOWN 0 0 4 64,128,0")
                        client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)
                        current_menu_option -= 1
            if config_status:
                if menu_options[current_menu_option].name == lang["Date"] and config_date_status:
                    menu_options[current_menu_option].get_option_object().set_option()
                else:
                    menu_options[current_menu_option].set_option()
                    #logger.debug("current_option: %d, current_lang_option: %d" %(menu_options[current_menu_option].current_option, current_lang_option))
            else:
                current_menu_option %= len(menu_options)
            if GPIO.input(KEY_MENU) == GPIO.LOW:
                logger.debug("MENU")
                key_trigger_status = True
                while GPIO.input(KEY_MENU) == GPIO.LOW:
                    pass
                logger.debug("MENU 0 0 4 64,128,0")
                client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)
                ## current_menu_option = 0
                if menu_options[current_menu_option].name == lang["Date"] and config_status:
                    config_date_status = True
                    config_status = False
                    current_interface_option = 1
                else:
                    current_interface_option += 1
                if current_interface_option == 1:
                    key_trigger_status = False
                    threading.Thread(target=back_to_main, args=()).start()
            current_interface_option %= len(interface_options)
            if GPIO.input(KEY_CONFIG) == GPIO.LOW:
                logger.debug("CONFIG")
                key_trigger_status = True
                while GPIO.input(KEY_CONFIG) == GPIO.LOW:
                    pass
                logger.debug("CONFIG 0 0 4 64,128,0")
                client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)
                if current_interface_option == 1:
                    if menu_options[current_menu_option].name == lang["Date"]:
                        config_status = True
                        config_date_status = not config_date_status
                    elif menu_options[current_menu_option].name == lang["MAC"] or menu_options[current_menu_option].name == lang["MAC(BCD)"] or menu_options[current_menu_option].name == lang["Window Position"] or menu_options[current_menu_option].name == lang["System Info"]:
                        pass
                    else:
                        config_status = not config_status
                        if config_status == False:
                            menu_options[current_menu_option].do()
                            #logger.debug("current_lang_option: %d" %(current_lang_option))
            time.sleep(0.1)
            
        t_load_info_exitBit = True
        t_load_info.join()
        logger.debug("test ... ")

        os.system('pkill python3.5')
            

    except Exception as result:
        print("[MT] unkown error: %s" % result)
        t_load_info_exitBit = True
        t_load_info.join()
        sys.exit()
"""

#t_load_info = 0



def main():
    global t_load_info, t_load_info_exitBit

    #while 1:
        #parapipe = "/etc/lcdpipe"
        #if not os.path.exists(parapipe):
            #os.mkfifo(parapipe)
        #fd_pp =  os.open(parapipe, os.O_RDONLY | os.O_NONBLOCK)
        #BUFSIZE = 1024
        #client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #logger.debug("[MT], create socket successful...")
        #ip_port = ('127.0.0.1', 58471)
        #client.sendto(('0 0 4 64,128,0').encode('utf-8'), ip_port)
    logger.debug(menu_options[9].get_option())
        #time.sleep(0.1)
    #t_load_info = threading.Thread(target=load_info, args=())
    #t_load_info.start()
    #t_load_info_exitBit = True
    #t_load_info.exit()
"""
    

    


if __name__ == "__main__":
    global t_load_info_exitBit
    try:
        main()
        logger.debug("will next ...")
        t_load_info_exitBit = True
        t_load_info.join()
        raise(KeyboardInterrupt)
    #except Exception as e:
    #    traceback.print_exc()
    #    t_load_info_exitBit = True
    #    t_load_info.join()
    #    sys.exit()
    except Exception as result:
        print(" 2 unkown error: %s" % result)
        t_load_info_exitBit = True
        t_load_info.join()
        sys.exit()
    #except IndexError as e:
    #    traceback.print_exc()
    #    pass
    #except SystemExit:
    #    pass
    #except KeyboardInterrupt:
    #    pass
else:
    logger.debug('come from another module')

