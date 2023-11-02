# -*- coding: utf-8 -*-
"""
功能描述: v2ray代理服务器辅助工具，检查v2ray节点的有效性、生成v2ray的配置文件、启动v2ray监听端口以接受指定节点的代理服务器访问请求、停止v2ray代理服务器。
        配合v2rayN-v4.23使用，当前只限定这个版本。
        读取D:/V2RayTool/v2rayN-v4.23/v2rayN-Core/guiNConfig.json，获取shadowsocks类型的节点信息，
        检查这些节点的有效性，将有效的节点写入valid_node.txt文件.
        使用wv2ray.exe启动代理服务器，这是不带界面的程序，v2ray.exe是带界面的。
        wvr2ray.exe的启动方式：wv2ray.exe -config={config.json文件的完整路径}
使用方法: 1、先使用D:/V2RayTool/v2rayN-v4.23/v2rayN-Core/V2RayN.exe更新订阅，
           再选择‘测试服务器真连接延迟’，测试完后要关闭V2RayN.exe，测试的结果数据才会写入guiNConfig.json文件中。
        2、检查v2ray节点的有效性，去除重复的代理服务器IP地址，将有效的代理服务器写入valid_node.txt；
        3、从7800端口开始，按顺序生成config{listen_port}.json配置文件，
           在tw用户代理文件TwData/user_proxy.txt中分配各用户使用的端口；
        4、使用生成的特定端口配置文件启动v2ray监听指定端口；
        5、启动、停止全部的v2ray监听。
"""

import requests
import re
from Utility import *


DATA_PATH = 'd:/py/V2RayNConfig/'
V2RAY_PATH = 'D:/V2RayTool/v2rayN-v4.23/v2rayN-Core/'
GUI_CONFIG = V2RAY_PATH + 'guiNConfig.json'
VALID_NODE_FILE = DATA_PATH + 'valid_node.txt'                      # 有效的节点
CONFIG_SHADOWSOCKS = DATA_PATH + 'config-shadowsocks.json'          # shadowsocks模板文件
CONFIG_VMESS = DATA_PATH + 'config-vmess.json'                      # vmess模板文件

TW_DATA_PATH = 'd:/TwData/'                                         # tw配置数据的文件夹

tw_port_list = []                  # tw账号要使用的监听端口列表
tw_proxy_info_list = []            # tw账号使用的有效代理服务器信息


def check_node(listen_port):
    headers = {
        'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
    }

    proxy = {
        'https' : '127.0.0.1:' + listen_port,
        'http' : '127.0.0.1:' + listen_port
    }

    url = 'https://www.cip.cc/'
    try:
        resp = requests.get(url = url, headers = headers, proxies = proxy, timeout = 10)
    except Exception as e:
        print('获取代理服务器的IP地址异常.')
        return ''

    if resp.status_code != 200:
        print('获取代理服务器的IP地址通讯错误, 状态码[{}].'.format(resp.status_code))
        return ''

    ip = ''
    text = resp.text
    pos = text.find('<pre>IP')
    if pos >= 0:
        text = text[pos + len('<pre>IP') : ]
        pos = text.find('地址')
        if pos >= 0:
            ip = text[0 : pos]

    if len(ip) < 0:
        print('IP地址数据无效.')
        return ''

    ip = ip.replace('\n', '')
    ip = ip.replace('\r', '')
    ip = ip.replace(':', '')
    ip = ip.replace('\t', '')
    ip = ip.replace(' ', '')

    reg = '^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$'
    if re.match(reg, ip) is None:
        return ''

    return ip


def check_node_ex(listen_port):
    headers = {
        'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
    }

    proxy = {
        'https' : '127.0.0.1:' + listen_port,
        'http' : '127.0.0.1:' + listen_port
    }

    url = 'https://proxy6.net/en/privacy'
    try:
        resp = requests.get(url = url, headers = headers, proxies = proxy, timeout = 10)
    except Exception as e:
        print('获取代理服务器的IP地址异常.')
        return ''

    if resp.status_code != 200:
        print('获取代理服务器的IP地址通讯错误, 状态码[{}].'.format(resp.status_code))
        return ''

    ip = ''
    text = resp.text
    pos = text.find('<b class="dotd clickselect">')
    if pos >= 0:
        text = text[pos + len('<b class="dotd clickselect">') : ]
        pos = text.find('</b>')
        if pos >= 0:
            ip = text[0 : pos]

    if len(ip) < 0:
        print('IP地址数据无效.')
        return ''

    ip = ip.replace('\n', '')
    ip = ip.replace('\r', '')
    ip = ip.replace(':', '')
    ip = ip.replace('\t', '')
    ip = ip.replace(' ', '')

    reg = '^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$'
    if re.match(reg, ip) is None:
        return ''

    return ip


# 获取有效节点
def get_valid_node():
    proxy_info = {}         # { ip : proxy info }
    proxy_speed = {}        # { ip : speed}
    proxy_zone = {}         # { ip : zone name }

    stop_proxy()

    if os.path.isfile(VALID_NODE_FILE) is True:
        os.remove(VALID_NODE_FILE)

    with open(GUI_CONFIG, 'r', encoding = 'utf-8') as f:
        gui = json.load(f)
        f.close()

    # 从节点文件中获取shadowsocks、vmess的节点数据，检查这些节点是否有效。
    nodes = gui['vmess']
    for node in nodes:
        if node['configType'] == 3 or node['configType'] == 1:     # 1 : vmess节点; 3 : shadowsocks节点
            node_type = node['configType']
            address = node['address']
            port = node['port']
            password = node['id']       # 密码
            security = node['security'] # 加密方式
            remarks = node['remarks']   # ip所属地区
            remarks = remarks.replace('|', '#')     # 替换掉其中的|，因为分隔符号是|
            testResult = node['testResult']         # 连接速度(ms)
            if testResult.find('ms') < 0:           # 速度含有ms才是有效的
                continue
            testResult = testResult.replace('ms', '')
            testResult = testResult.replace(' ', '')

            # 取出地区名，每个地区一般只有一个ip地址
            list = remarks.split('#')
            if len(list) > 1:
                zone = list[1]                       # 地区
            else:
                zone = '备用'                         # 地区为备用，可以多选择一个节点

            data = ''
            for ch in zone:
                if '\u4e00' <= ch <= '\u9fff':  # 中文
                    data = data + ch
            zone = data

            speed = 0
            # 速度值为数字开始，该节点有效，否则是无效节点
            nums = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
            if testResult[0 : 1] not in nums:
                continue
            else:
                speed = int(testResult)

            out_data = ''
            file_name = ''
            if node['configType'] == 3:
                file_name = CONFIG_SHADOWSOCKS
            elif node['configType'] == 1:
                file_name = CONFIG_VMESS
            with open(file_name, 'r', encoding = 'utf-8') as f:
                while 1:
                    ss = f.readline()
                    if ss == '':
                        break

                    listen_port = '8900'
                    proxy_addr = address
                    proxy_port = str(port)
                    proxy_password = password
                    proxy_security = security

                    # 模板替换
                    ss = ss.replace('{$INBOUND_TAG}', 'http' + listen_port)
                    ss = ss.replace('{$LISTEN_PORT}', listen_port)
                    ss = ss.replace('{$OUTBOUND_TAG}', 'proxy' + listen_port)
                    ss = ss.replace('{$PROXY_ADDR}', proxy_addr)
                    ss = ss.replace('{$PROXY_PORT}', proxy_port)
                    ss = ss.replace('{$PASS_WORD}', proxy_password)
                    ss = ss.replace('{$SECURITY_METHOD}', proxy_security)

                    out_data += ss
                f.close()

            # 生成节点配置文件，使用生成的这个配置文件启动v2ray.exe，检查其中的节点是否有效
            target_config_file = DATA_PATH + 'config_chcknode' + '.json'
            if os.path.isfile(target_config_file) is True:
                os.remove(target_config_file)

            # 写入结果配置文件
            with open(target_config_file, 'w', encoding = 'utf-8') as f1 :
                f1.write(out_data)
                f1.close()

            # 执行v2ray.exe启动指定代理服务器，检查该代理服务器是否有效
            if os.path.isfile(V2RAY_PATH + 'config.json') is False:
                print('没有config.json文件, 无法启动wv2ray.exe')
                continue

            os.system('start ' + V2RAY_PATH + 'wv2ray.exe -config=' + target_config_file)
            time.sleep(3)

            os.remove(target_config_file)
            stamp = time.time()
            begin_time = int(round(stamp * 1000))
            ip = check_node_ex(listen_port)
            stamp = time.time()
            end_time = int(round(stamp * 1000))
            interval = end_time - begin_time

            # 终止v2ray.exe进程
            stop_proxy()

            if len(ip) <= 0:
                print('代理服务器[{}|{}|{}]异常.'.format(address, port, remarks))
                continue

            print('代理服务器[{}|{}|{}|{}|{}]有效.'.format(address, port, remarks, ip, interval))

            # 优先保留3倍速节点和IPLC专线节点
            if remarks.find('x3') >= 0 or remarks.find('IPLC') >= 0:
                if ip in proxy_info:
                    proxy_info.pop(ip)
                if ip in proxy_speed:
                    proxy_speed.pop(ip)
                if ip in proxy_zone:
                    proxy_zone.pop(ip)

                zone = zone + 'x3'
                proxy_info[ip] = f'{address}|{port}|{password}|{security}|{node_type}|{remarks}|{speed}|{ip}|{zone}|{speed}|{interval}'
                proxy_speed[ip] = speed             # 代理服务器的响应速度
                proxy_zone[ip] = zone
                continue

            # 检查地址是否已经存在，防止使用重复的地址，对已存在的ip，保留速度最快的节点
            is_address_existed = False
            for k, v in proxy_zone.items():    # k : ip, v : 地区名
                if k == ip:
                    if k in proxy_speed:
                        node_speed = proxy_speed[k]
                        # 同一ip，记录最快的端口，已记录的端口速度快于当前端口，则视为已存在
                        if node_speed < speed:
                            is_address_existed = True
                    break
            if is_address_existed is False:
                proxy_info[ip] = f'{address}|{port}|{password}|{security}|{node_type}|{remarks}|{speed}|{ip}|{zone}|{speed}|{interval}'
                proxy_speed[ip] = speed             # 代理服务器的响应速度
                proxy_zone[ip] = zone

    # 对节点按响应时间进行升序排序
    proxy_info_sorted = {}
    speed_sorted = sorted(proxy_speed.items(), key = lambda x:x[1], reverse = False)

    # 过滤速度过慢的节点
    limited_speed = 700                 # 节点响应速度慢于该值的节点都过滤掉
    for k, v in proxy_speed.items():
        if v >= limited_speed:
            ip = k
            zone = proxy_zone[ip]
            # 3倍速节点不做过滤，保留使用
            if zone.find('x3') >= 0 :
                continue
            if ip in proxy_info:
                proxy_info.pop(ip)
            if ip in proxy_zone:
                proxy_zone.pop(ip)

    # 将节点按指定的地区顺序排列，确保地址使用的连贯性
    new_proxy_zone = {}
    node_seq = ['香港', '新加坡', '台湾', '日本', '美国',
                '马来西亚', '韩国', '越南', '菲律宾', '泰国',
                '印度', '澳大利亚', '迪拜', '阿根廷', '加拿大',
                '墨西哥']
    for name in node_seq:
        for k, v in proxy_zone.items():
            if v.find(name) >= 0:
                new_proxy_zone[k] = v

    for k, v in proxy_zone.items():
        if v not in new_proxy_zone.values():
            new_proxy_zone[k] = v

    new_proxy_info = {}
    for k, v in new_proxy_zone.items():
        new_proxy_info[k] = proxy_info.get(k)
    proxy_info.clear()
    proxy_info = new_proxy_info

    for addr, info in proxy_info.items():
        # 记录有效的节点
        with open(VALID_NODE_FILE, 'a', encoding = 'utf-8') as f :
            f.write(info + '\n')
            f.close()

    print('获取节点完成. 共[{}]个无重复的有效节点.'.format(len(proxy_info)))
    return


# 获取tw账号的代理服务器配置
# 1、从TwData/user_info.txt中获取当前可用的tw账号；
# 2、从TwData/user_proxy.txt中获取各tw账号连接的v2ray地址、端口；
# 3、将可用的tw账号使用的v2ray端口写入tw_port_list。
def get_tw_proxy_config():
    global tw_port_list
    global tw_proxy_info_list
    tw_proxy_info_list.clear()
    tw_port_list.clear()

    tw_proxy_info_list = read_file(VALID_NODE_FILE, DEL_ENTER_YES)
    if len(tw_proxy_info_list) < 1:
        print('没有代理服务器数据, 请先获取有效的节点数据。')
        return 1

    tw_user_info_list = []
    tw_user_info_list = read_file(TW_DATA_PATH + 'user_info.txt', DEL_ENTER_YES)
    if len(tw_user_info_list) < 1:
        print('没有需要配合使用的tw账号数据.')
        return 1

    tw_proxy_list = []
    tw_proxy_list = read_file(TW_DATA_PATH + 'user_proxy.txt', DEL_ENTER_YES)
    if len(tw_proxy_list) < 1:
        print('没有需要配合使用的tw代理服务器数据.')
        return 1

    tw_port_list = []
    for user in tw_user_info_list:
        list = user.split(':')
        if len(list) < 1:
            print('配置的tw账号数据无效[{}].'.format(user))
            continue

        user = list[0]
        list.clear()
        list = user.split('@')
        if len(list) < 2:
            print('tw账号数据无效[{}].'.format(user))
            continue
        user = list[0]

        for p in tw_proxy_list:
            list = p.split('=')                 # list[0] - eg: kathyrnsanflippotpd25；list[1] - eg: 127.0.0.1:7800
            if len(list) < 2:
                print('tw账号的代理服务器配置数据无效.[{}]'.format(p))
                continue

            user_name = list[0]
            if user == user_name:
                ip_port = list[1]               # eg: 127.0.0.1:7800
                ll = ip_port.split(':')
                if len(ll) < 2:
                    print('tw账号的代理服务器数据无效.[{}]'.format(ip_port))
                    continue

                port = ll[1]                    # tw账号需要连接的监听端口, eg : 7800
                tw_port_list.append(port)       # 需要使用的端口号

    if len(tw_port_list) < 1:
        print('没有需要连接的tw端口号.')
        return 1

    return 0


# 根据TwData/user_proxy.txt中的配置生成节点的配置文件，一个监听端口一个配置文件，生成的配置文件d:/V2RayTool/V2RayNConfig/config{listen_port}.json
def gen_config():
    global tw_proxy_info_list
    global tw_port_list

    if get_tw_proxy_config() != 0:
        print('获取tw账号的代理服务器数据错误.')
        return 1

    index = 0
    for info in tw_proxy_info_list:
        list = info.split('|')
        if len(list) < 4:
            print('代理服务器数据无效[{}].'.format(info))
            continue

        address = list[0]
        port = int(list[1])
        password = list[2]
        security = list[3]

        out_data = ''
        listen_port = ''
        with open(CONFIG_SHADOWSOCKS, 'r', encoding = 'utf-8') as f:
            while 1:
                ss = f.readline()
                if ss == '':
                    break

                listen_port = tw_port_list[index]
                proxy_addr = address
                proxy_port = str(port)
                proxy_password = password
                proxy_security = security

                # 模板替换
                ss = ss.replace('{$INBOUND_TAG}', 'http' + listen_port)
                ss = ss.replace('{$LISTEN_PORT}', listen_port)
                ss = ss.replace('{$OUTBOUND_TAG}', 'proxy' + listen_port)
                ss = ss.replace('{$PROXY_ADDR}', proxy_addr)
                ss = ss.replace('{$PROXY_PORT}', proxy_port)
                ss = ss.replace('{$PASS_WORD}', proxy_password)
                ss = ss.replace('{$SECURITY_METHOD}', proxy_security)

                out_data += ss
            f.close()

        target_config_file = DATA_PATH + 'config' + listen_port + '.json'
        if os.path.isfile(target_config_file) is True:
            os.remove(target_config_file)

        # 写入结果配置文件
        with open(target_config_file, 'w', encoding='utf-8') as f1:
            f1.write(out_data)
            f1.close()

        print('已生成配置文件[{}].'.format(target_config_file))

        index += 1
        if index >= len(tw_port_list):
            print('tw账号需要监听的端口全部启动完成.')
            return 0

    if len(tw_proxy_info_list) < len(tw_port_list):
        print('可用的代理服务器地址数量少于tw账号需要监听的端口数量.')

    return 0


# 启动所有监听端口，开始接受请求
def start_proxy():
    stop_proxy()

    global tw_proxy_info_list
    global tw_port_list

    if get_tw_proxy_config() != 0:
        print('启动代理服务时, 获取tw账号的代理服务器数据错误.')
        return

    for port in tw_port_list:
        config_file = DATA_PATH + 'config' + port + '.json'
        if os.path.isfile(config_file) is False:
            print('节点配置文件不存在[{}].'.format(config_file))
            continue

        cmd = 'start ' + V2RAY_PATH + 'wv2ray.exe -config=' + config_file
        print('启动监听[{}].'.format(cmd))
        os.system(cmd)
        time.sleep(3)

    print('启动监听端口全部完成.')


# 停止所有的监听端口
def stop_proxy():
    # 先停止现有的wv2ray.exe进程
    os.system('taskkill /F /FI "imagename eq wv2ray.exe"')


# 通用的config.json文件生成，本地监听端口从7800开始顺序递增，只到匹配完有效的ip地址，调用者根据需要使用指定的端口即可。
def gen_general_config():
    if os.path.isfile(CONFIG_SHADOWSOCKS) is False:
        print('模板配置文件[{}]不存在.'.format(CONFIG_SHADOWSOCKS))
        return 1

    if os.path.isfile(CONFIG_VMESS) is False:
        print('模板配置文件[{}]不存在.'.format(CONFIG_VMESS))
        return 1

    proxyinfo_list = []
    proxyinfo_list = read_file(VALID_NODE_FILE, DEL_ENTER_YES)
    if len(proxyinfo_list) < 1 or proxyinfo_list is None:
        print('代理服务器数据文件[{}]无效.'.format(VALID_NODE_FILE))
        return 1

    file_names = os.listdir(DATA_PATH)
    for file in file_names:
        # 模板文件和有效节点文件不能删除
        if file.find('config-shadowsocks.json') >= 0 or \
           file.find('valid_node.txt') >= 0 or \
           file.find('config-vmess.json') >=0:
            pass
        else:
            os.remove(DATA_PATH + file)

    listen_port_start = 7800                           # 起始监听端口
    index = 0
    for info in proxyinfo_list:
        list = info.split('|')
        # list[0] : 代理服务器地址(域名); list[2] : 代理服务器端口
        if len(list) < 4:
            print('代理服务器数据无效[{}].'.format(info))
            continue

        listen_port = str(listen_port_start + index)    # 监听端口
        proxy_addr = list[0]                            # 代理服务器地址(域名)
        proxy_port = list[1]                            # 代理服务器端口
        proxy_password = list[2]
        proxy_security = list[3]
        node_type = list[4]                             # 节点类型：1 - vmess；3 - shadeshock

        index += 1
        out_data = ''
        file_name = ''

        # 根据节点类型选择模板文件
        if node_type == '3':
            file_name = CONFIG_SHADOWSOCKS
        elif node_type == '1':
            file_name = CONFIG_VMESS

        with open(file_name, 'r', encoding = 'utf-8') as f:
            while 1:
                ss = f.readline()
                if ss == '':
                    break

                # 模板替换
                ss = ss.replace('{$INBOUND_TAG}', 'http' + listen_port)
                ss = ss.replace('{$LISTEN_PORT}', listen_port)
                ss = ss.replace('{$OUTBOUND_TAG}', 'proxy' + listen_port)
                ss = ss.replace('{$PROXY_ADDR}', proxy_addr)
                ss = ss.replace('{$PROXY_PORT}', proxy_port)
                ss = ss.replace('{$PASS_WORD}', proxy_password)
                ss = ss.replace('{$SECURITY_METHOD}', proxy_security)

                out_data += ss
            f.close()

        target_config_file = DATA_PATH + 'config' + listen_port + '.json'
        if os.path.isfile(target_config_file) is True:
            os.remove(target_config_file)

        # 写入结果配置文件
        with open(target_config_file, 'w', encoding = 'utf-8') as f1 :
            f1.write(out_data)
            f1.close()

        print('V2RayN配置文件[{}]生成完成.'.format(target_config_file))

    print('配置文件已全部生成, 共[{}]个有效端口!'.format(index))
    return 0


# 启动所有监听端口，开始接受请求
def start_general_proxy():
    stop_proxy()

    port_list = []
    for i in range(7800, 7900):
        port_list.append(str(i))

    for port in port_list:
        config_file = DATA_PATH + 'config' + port + '.json'
        if os.path.isfile(config_file) is False:
            continue

        cmd = 'start ' + V2RAY_PATH + 'wv2ray.exe -config=' + config_file
        print('启动监听[{}].'.format(cmd))
        os.system(cmd)
        time.sleep(1)

    print('启动监听端口全部完成.')


# 删除已存在的config.json文件
def delete_general_config():
    for port in range(7800, 7900):
        file_name = DATA_PATH + f'config{port}.json'
        if os.path.isfile(file_name) is True:
            os.remove(file_name)


if __name__ == '__main__':
    while 1:
        os.system('cls')

        print('V2RayN代理服务器管理菜单')
        print('1、获取有效的服务器节点.')
        print('2、生成有效服务器节点的config{port}.json文件.')
        print('3、启动代理服务器.')
        print('4、停止代理服务器.')
        print('9、退出.')
        print('')

        key = input('请按数字键选择: ')

        if key == '1':
            get_valid_node()
        elif key == '2':
            delete_general_config()
            gen_general_config()
        elif key == '3':
            start_general_proxy()
        elif key == '4':
            stop_proxy()
        elif key == '9':
            break
        else:
            key = input('无效选项, 按回车键请重新选择. ')
            continue

        key = input('按回车键继续. ')