# -*- coding: utf-8 -*-
"""
功能描述：公共功能函数定义。
"""

import os
import time
import json
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import sys


YES = 1
NO = 0

# 是否删除数据后面的回车、换行
DEL_ENTER_YES = 1
DEL_ENTER_NO = 0

# 日志路径
LOG_PATH = './log'

# log日志级别
LOG_INFO = 0        # 信息日志
LOG_ERR = 1         # 错误日志
LOG_WARN = 2        # 警告日志


# 读取文件，按行返回读取的数据(del_enter : 1 - 去掉数据后面的回车、换行; 0 - 不进行任何处理)
def read_file(file_name, del_enter = DEL_ENTER_YES) :
    read_list = []
    if os.path.isfile(file_name) is False:
        return read_list

    with open(file_name, 'r', encoding = 'utf-8') as f :
        while 1 :
            ss = f.readline()
            if ss == '' :
                break
            if ss[0 : 1] == '#' :
                continue
            if del_enter == DEL_ENTER_YES:
                ss = ss.replace('\n', '')
                ss = ss.replace('\r', '')
                if ss != '':
                    read_list.append(ss)
        f.close()

    return read_list


def set_log_path(log_path):
    LOG_PATH = log_path


# 按日期记录日志
def write_log(log_level, log_data):
    log_date = time.strftime('%Y-%m-%d', time.localtime())
    file_name = LOG_PATH + log_date + '.log'
    write_logex(file_name, log_level, log_data)


# 指定文件名记录日志
def write_logex(file_name, log_level, log_data):
    if os.path.isdir(LOG_PATH) is False:
        os.mkdir(LOG_PATH)

    log_date = time.strftime('%Y-%m-%d', time.localtime())
    log_time = time.strftime('%H:%M:%S', time.localtime())
    if log_level == LOG_INFO:
        data = '[INF]' + log_data
    elif log_level == LOG_ERR:
        data = '[ERR]' + log_data
    elif log_level == LOG_WARN:
        data = '[WRN]' + log_data
    else:
        data = '[DBG]' + log_data

    print(f'[{log_time}]{data}')
    with open(file_name, 'at', encoding = 'UTF-8') as f:
        f.write(f'[{log_time}]{data}' + '\n')
        f.close()
    return


# 在标准输出打印日志
def print_log(log_data):
    log_time = time.strftime("%H:%M:%S", time.localtime())
    print(f'[{log_time}]{log_data}')


# 获取日期(YYYY-MM-DD)
def get_log_date():
    log_date = time.strftime("%Y-%m-%d", time.localtime())
    return log_date


# 获取时间(HH:MM:SS)
def get_log_time():
    log_time = time.strftime("%H:%M:%S", time.localtime())
    return log_time


# 根据特征值获取指定的数据,data - 要分析的数据, target_list : 特征数据列表，返回找到的特征数据
def get_target_data(data, target_list):
    i = 0
    data_found = ''
    list_len = len(target_list)
    while (i <= list_len):
        target_data = target_list[i]
        target_data_len = len(target_data)
        index = data.find(target_data)
        if index < 0:
            break
        elif (index >= 0) and (i == list_len - 1):
            data_found = target_data[0 : index]
        else:
            data = data[index + target_data_len : ]
        i += 1
    return data_found


def split_string(data, filter):
    pos = 0
    data_list = []
    while (1):
        pos = data.find(filter)
        if (pos >= 0):
            data_list.append(data[0 : pos])
            data = data[pos + len(filter) : ]
        else:
            data_list.append(data)
            break

    return data_list