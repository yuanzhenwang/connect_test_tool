# coding=utf-8
from api import api
from logs import set_logger
import sys
import json
import threading
import time
import random
import csv
import os

SCANED_DEVICE = []
CONNECTED_DEVICE = []
CONNECT_TIMEOUT = 5000
STOP_SCAN = False
EXIT = False
useful_dev = {}
useful_dev_info = {}
logger = set_logger(__name__)


def get_conf():
    try:
        with open('config.json', 'r', encoding='utf8') as f:
            conf = json.load(f)
        return conf
    except Exception as e:
        print('Open config file failed! Reason:', e)


def auto_conn(dev, chip, count, path, retry=5):
    global CONNECTED_DEVICE, SCANED_DEVICE
    rssi = []
    tname = threading.current_thread().getName()
    for data in api.scan(active=1, chip=chip, filter_mac=dev):
        if data.startswith('data'):
            data = json.loads(data[5:])
            if len(rssi) < count:
                print('''The device %s is %d times have been scaned,rssi is:%d.(%s)''' % (
                    data['bdaddrs'][0]['bdaddr'],
                    len(rssi) + 1,
                    int(data['rssi']),
                    tname))
                rssi.append(int(data['rssi']))
            else:
                dev_name = data['name']
                device_info = data['bdaddrs'][0]
                print('Start connect device %s.' % dev)
                i = 0
                while i < retry:
                    code, body, duration = api.connect_device(
                        device_info['bdaddr'],
                        device_info['bdaddrType'],
                        chip=chip,
                        timeout=CONNECT_TIMEOUT)
                    time.sleep(2)
                    a, b = api.get_devices_list('connected')
                    if device_info['bdaddr'] in b:
                        msg = '''\nDevice:{0:s} all rssi are :{1:s}\n
                        All rssi average is:{2:.2f}\n
                        Connect duration is:{3:.2f}\n
                        contect times:{4:d}'''.format(dev,
                                                      str(rssi),
                                                      sum(rssi) / len(rssi),
                                                      duration, i)
                        logger.info(msg)
                        print(msg)
                        write_csv([dev, dev_name, str(rssi), sum(
                            rssi) / len(rssi), duration, i + 1], path)
                        CONNECTED_DEVICE.append(dev)
                        SCANED_DEVICE.remove(dev)
                        print('当前正在连接的设备数量为：%d' % len(SCANED_DEVICE))
                        for dev in SCANED_DEVICE:
                            print(dev)
                        print('当前成功连接的设备数量为：%d' % len(CONNECTED_DEVICE))
                        for dev in CONNECTED_DEVICE:
                            print(dev)
                        break
                    else:
                        wait = random.randint(1, 10)
                        print('设备 %s 第%d次连接失败，随机等待%d秒后重新连接' %
                              (dev, i + 1, wait))
                        logger.debug('设备 %s 第%d次连接失败，随机等待%d秒后重新连接' %
                                     (dev, i, wait))
                        time.sleep(wait)
                        i += 1
                else:
                    print('达到最大重连次数，停止重连，设备 %s 连接失败,平均rssi为%.2f' %
                          (dev, sum(rssi) / len(rssi)))
                    logger.info('达到最大重连次数，停止重连，设备 %s 连接失败.平均rssi为%.2f' %
                                (dev, sum(rssi) / len(rssi)))
                    SCANED_DEVICE.remove(dev)
                return


def conn(devs, chip=None, retry=5):
    global CONNECTED_DEVICE, SCANED_DEVICE

    SCANED_DEVICE = [i for i in devs]
    times = 0
    while times < retry:
        print('The devices will to connect:\n', devs)
        print('The devices have connected:\n', CONNECTED_DEVICE)
        for dev in SCANED_DEVICE:
            if chip:
                _, _, duration = api.connect_device(
                    dev, 'public', chip=chip, timeout=CONNECT_TIMEOUT)
            else:
                _, _, duration = api.connect_device(
                    dev, 'public', timeout=CONNECT_TIMEOUT)
            time.sleep(2)
            a, b = api.get_devices_list('connected')
            if dev in b:
                SCANED_DEVICE.remove(dev)
                CONNECTED_DEVICE.append(dev)
                print(dev, 'duration(s):', duration, '| connected success!')
            else:
                if chip:
                    _, _, duration = api.connect_device(
                        dev, 'random', chip=chip, timeout=CONNECT_TIMEOUT)
                else:
                    _, _, duration = api.connect_device(
                        dev, 'random', timeout=CONNECT_TIMEOUT)
                time.sleep(2)
                if dev in b:
                    SCANED_DEVICE.remove(dev)
                    CONNECTED_DEVICE.append(dev)
                    print(dev, 'duration(s):', duration,
                          '| connected success!')
            print('设备%s第%d次连接失败' % (dev, times + 1))
        if SCANED_DEVICE:
            times += 1
        else:
            print('All devs have been conntcted!')
            break
    else:
        print('达到最大重连次数，停止重连，设备%s连接失败' % str(SCANED_DEVICE))
        logger.debug('达到最大重连次数，停止连接，设备%s连接失败' % str(SCANED_DEVICE))


# def re_conn(dev, chip=None, retry=5):
#     global CONNECTED_DEVICE
#     print('检测到设备 %s 断开连接，尝试重连该设备' % dev)
#     logger.debug('\n检测到设备 %s 断开连接，尝试重连该设备...\n' % dev)
#     i = 1
#     while 1:
#         if chip:
#             code, body, duration = api.connect_device(
#                 device_info['bdaddr'],
#                 device_info['bdaddrType'],
#                 chip=chip,
#                 timeout=CONNECT_TIMEOUT)
#         else:
#             code, body, duration = api.connect_device(
#                 device_info['bdaddr'],
#                 device_info['bdaddrType'],
#                 timeout=CONNECT_TIMEOUT)
#         time.sleep(2)
#         a, b = api.get_devices_list('connected')
#         if device_info['bdaddr'] in b:
#             msg = '设备 %s 重新连接成功' % dev
#             logger.info(msg)
#             print(msg)
#             write_csv([dev, dev_name, str(rssi), sum(
#                 rssi) / len(rssi), duration, i])
#             CONNECTED_DEVICE.append(dev)
#             print('当前成功连接的设备数量为：%d' % len(CONNECTED_DEVICE))
#             for dev in CONNECTED_DEVICE:
#                 print(dev)
#             break
#         else:
#             wait = random.randint(1, 10)
#             print('设备 %s 第%d次连接失败，随机等待%d秒后重新连接' % (dev, i, wait))
#             logger.debug('设备 %s 第%d次连接失败，随机等待%d秒后重新连接' % (dev, i, wait))
#             time.sleep(wait)
#         i += 1
#         if i > retry + 1:
#             print('达到最大重连次数，停止重连，设备%s连接失败.' % dev)
#             break


def conn_many(path):
    global useful_dev, useful_dev_info, disturb_dev
    disturb_dev = {}
    conf = get_conf()
    scan_mode = conf['scan_mode']
    chip = conf['chip']
    config_devs = eval(conf['devices'])
    duration = int(conf["scan_duration"])
    retry = int(conf['retry'])
    threading.Timer(duration, stop_scan).start()
    res = api.scan(active=scan_mode, chip=chip)
    while not STOP_SCAN:
        data = res.__next__()
        if data.startswith('data'):
            data = json.loads(data[5:])
            # print(data)
            mac = data['bdaddrs'][0]['bdaddr']
            mac_rssi = int(data['rssi'])
            if mac in config_devs:
                if mac in useful_dev:
                    useful_dev[mac].append(mac_rssi)
                    print('设备 %s 第 %d 次被扫描,rssi是:%d.' % (
                        mac,
                        len(useful_dev[mac]),
                        int(data['rssi'])))
                else:
                    useful_dev[mac] = []
                    useful_dev[mac].append(mac_rssi)
                    print('设备 %s 第 %d 次被扫描,rssi是:%d.' % (mac,
                                                         len(useful_dev[mac]),
                                                         int(data['rssi'])))
                    dev_type = data['bdaddrs'][0]['bdaddrType']
                    name = data['name']
                    useful_dev_info[mac] = ((dev_type, name))
            if mac in disturb_dev:
                disturb_dev[mac].append(mac_rssi)
            else:
                disturb_dev[mac] = []
                disturb_dev[mac].append(mac_rssi)
        else:
            print('非扫描数据：', data)
    chuli_disturb_dev(disturb_dev, path)
    conn_useful_devs(config_devs, retry, path)


def conn_useful_devs(config_devs, retry, path):
    global EXIT
    i = 0
    no_scan_dev = []
    scaned_dev = []
    print('扫描结束，开始连接设备')
    for mac in config_devs:
        if mac not in useful_dev:
            no_scan_dev.append(mac)
        else:
            scaned_dev.append(mac)
    for dev in no_scan_dev:
        print('没有扫描到设备%s，放弃连接该设备' % dev)
    while i < int(retry):
        conn_fail_dev = []
        for mac in scaned_dev:
            rssis = useful_dev[mac]
            dev_type = useful_dev_info[mac][0]
            dev_name = useful_dev_info[mac][1]
            code, body, duration = api.connect_device(
                mac, dev_type)
            time.sleep(2)
            a, b = api.get_devices_list('connected')
            if mac in b:
                average = sum(rssis) / len(rssis)
                msg = '\nDevice:{0:s} connected success!All rssi are :{1:s}\n \
                All rssi average is:{2:.2f}\n\
                Connect duration is:{3:.2f}\n\
                contect times:{4:d}'.format(mac,
                                            str(rssis),
                                            average,
                                            duration, i)
                logger.info(msg)
                print(msg)
                write_csv([mac, dev_name, str(rssis), len(rssis),
                           average, duration, i + 1], path)
                data = json.loads(b)
                dev_count = len(data['nodes'])
                print('当前连接设备数量为：%d' % dev_count)
                for dev in data['nodes']:
                    print(dev['id'])
                config_devs.remove(mac)
            else:
                conn_fail_dev.append(mac)
                print('设备%s第%d次连接失败' % (mac, i + 1))
        scaned_dev = conn_fail_dev
        i += 1
    for fail in conn_fail_dev:
        print('达到最大重连次数，停止连接设备%s' % fail)
    EXIT = True


def stop_scan():
    global STOP_SCAN
    STOP_SCAN = True


def get_dev_list():
    a, b = api.get_devices_list('connected')
    data = json.loads(b)
    dev_count = len(data['nodes'])
    print('当前连接设备数量为：%d' % dev_count)
    for dev in data['nodes']:
        print(dev['id'])
    set_exit()


def dis_all(api):
    a, b = api.get_devices_list('connected')
    nodes = json.loads(b)
    for device in nodes['nodes']:
        mac = device['id']
        api.disconnect_device(mac)
    set_exit()


def set_exit():
    global EXIT
    EXIT = True

# def get_msg(sseclient):
#     for message in sseclient:
#         if "keep-alive" in message:
#             pass
#         elif message.startswith('data'):
#             print('Notification:' + message)
#             msg = 'Notification:' + message
#             logger.debug(msg)
#             break


def get_str_time():
    return time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())


def write_csv(data, path):
    time = get_str_time()
    data.insert(1, time)
    if not os.path.exists(path + '/info.csv'):
        with open(path + '/info.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['device', 'time', 'device type', 'rssis',
                             'rssi count', 'average rssi',
                             'connected duration', 'connected times'])
            writer.writerow(data)
    else:
        with open(path + '/info.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)


def collect_scan_data(data, config_devs):
    global disturb_dev, useful_dev, useful_dev_info
    data = json.loads(data[5:])
    mac = data['bdaddrs'][0]['bdaddr']
    print(config_devs)
    if mac in config_devs:
        mac_rssi = int(data['rssi'])
        if mac in useful_dev:
            useful_dev[mac].append(mac_rssi)
            print('设备 %s 第 %d 次被扫描,rssi是:%d.' % (
                mac,
                len(useful_dev[mac]),
                int(data['rssi'])))
        else:
            useful_dev[mac] = []
            useful_dev[mac].append(mac_rssi)
            print('设备 %s 第 %d 次被扫描,rssi是:%d.' % (mac,
                                                 len(useful_dev[mac]),
                                                 int(data['rssi'])))
            dev_type = data['bdaddrs'][0]['bdaddrType']
            name = data['name']
            useful_dev_info.append((mac, dev_type, name))
        if mac in disturb_dev:
            disturb_dev[mac].append(mac_rssi)
        else:
            disturb_dev[mac] = []
            disturb_dev[mac].append(mac_rssi)


def chuli_disturb_dev(disturb_dev, path):
    for key, value in disturb_dev.items():
        average_rssi = sum(value) / len(value)
        str_rssi = str(value)
        count_rssi = len(value)
        time = get_str_time()
        row = [key, time, count_rssi, average_rssi, str_rssi]
        save_disturb_dev(row, path)


def save_disturb_dev(data, path):
    if not os.path.exists(path + '/disturb_dev.csv'):
        with open(path + '/disturb_dev.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['device', 'time',
                             'count', 'average rssi', 'all rssis'])
            writer.writerow(data)
    else:
        with open(path + '/disturb_dev.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data)


# def get_connect_state():
#     global CONNECTED_DEVICE
#     conf = get_conf()
#     for message in api.get_device_connect_state():
#         # message = json.loads(event)
#         message = str(message)
#         print(message)
#         if message.startswith('data'):
#             msg = json.loads(message[:6])
#             if msg['handle'] == 'disconnected':
#                 print('Device %s is disconnected,will reconnected.' %
#                       msg['handle'])
#                 CONNECTED_DEVICE.remove(msg['handle'])
#                 threading.Thread(target=scan_conn, args=(
#                     msg['handle'], conf['retry'])).start()

def scan_config_dev(path):
    conf = get_conf()
    if not os.path.exists(path + '/info.csv'):
        write_csv(['device', 'device type', 'rssis', 'average rssi',
                   'connected duration', 'connected times'], path)
    for data in api.scan(active=conf['scan_mode'], chip=conf['chip']):
        names = conf['device_type_name']
        if data.startswith('data'):
            data = json.loads(data[5:])
            for name in eval(names):
                if name in data['name']:
                    if data['bdaddrs'][0]['bdaddr'] in SCANED_DEVICE:
                        pass
                    elif data['bdaddrs'][0]['bdaddr'] in CONNECTED_DEVICE:
                        CONNECTED_DEVICE.remove(
                            data['bdaddrs'][0]['bdaddr'])
                    elif threading.active_count() < 10:
                        t = threading.Thread(target=auto_conn, args=(
                            data['bdaddrs'][0]['bdaddr'], conf[
                                'chip'], conf['rssi_count'], path,
                            conf['retry']), )
                        t.setDaemon(True)
                        t.start()
                        SCANED_DEVICE.append(data['bdaddrs'][0]['bdaddr'])
                        print('扫描到新设备 %s.' % data['bdaddrs'][0]['bdaddr'])
                    break  # 退出for name循环


def main():
    global SCANED_DEVICE, CONNECTED_DEVICE, api, PATH
    conf = get_conf()
    api = api(conf['host'], conf['ap'], conf['user'], conf['pwd'])
    # if conf['auto_reconnect'] == 'True':
    #     # 判断是否开启自动重连
    #     threading.Thread(target=get_connect_state).start()
    helps = [('commond:', "命令说明"),
             ('conn-by-name', '默认连接扫描到的配置文件中指定名称的设备,直到强制停止程序'),
             ('conn', '连接配置文件中指定的一组设备,不保存rssi等数据'),
             ('dis-one', '断连一个指定的设备'),
             ('dis-all', '断连所有设备'),
             ('get', '获取当前连接的所有设备'),
             ('auto', '''自动读取配置文件的设备，扫描指定时间后自动开始连接;
                        后面可配置日志存放文件夹，默认为logs目录；
                        example：main.py auto logs_dir'''),
             ('use example', "'python main.py conn'")]
    # 进入主程序逻辑
    if sys.argv[1] == 'conn-by-name':
        try:
            path = sys.argv[2]
        except:
            path = 'logs'
        if not os.path.exists(path):
            os.mkdir(path)
        t = threading.Thread(target=scan_config_dev, args=(path,))
        t.setDaemon(True)
        t.start()
    elif sys.argv[1] == 'dis-one':
        api.disconnect_device(sys.argv[2])
        set_exit()
    elif sys.argv[1] == 'dis-all':
        dis_all(api)
    elif sys.argv[1] == 'conn':
        devs = eval(conf['devices'])  # 转换成列表
        t = threading.Thread(target=conn, args=(
            devs, conf['chip'], conf['retry']))
        t.setDaemon(True)
        t.start()
    elif sys.argv[1] == 'get':
        get_dev_list()
    elif sys.argv[1] == 'auto':
        try:
            path = sys.argv[2]
        except:
            path = 'logs'
        if not os.path.exists(path):
            os.mkdir(path)
        t = threading.Thread(target=conn_many, args=(path,))
        t.setDaemon(True)
        t.start()
    elif sys.argv[1] == 'help' or '--help' or '-help':
        for a, b in helps:
            print('%-15s%-30s' % (a, b))
        sys.exit(0)
    else:
        for a, b in helps:
            print('%-15s%-30s' % (a, b))
        sys.exit(0)
    try:
        while not EXIT:
            # 监听程序退出
            time.sleep(1)
    except KeyboardInterrupt:
        print('检测到CTRL-C，正在保存数据，稍后退出....')


if __name__ == '__main__':
    main()
