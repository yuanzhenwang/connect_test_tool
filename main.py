# coding=utf-8
from api import api
from logs import set_logger
import sys, json, threading, time
import random, csv, os

try:
    import sseclient
except:
    os.system("pip install sseclient")

SCANED_DEVICE = []
CONNECTED_DEVICE = []
CONNECT_TIMEOUT = 5000
CHIP_FULL = False
logger = set_logger(__name__)


def get_conf():
    try:
        with open('config.json', 'r', encoding='utf8') as f:
            conf = json.load(f)
        return conf
    except Exception as e:
        print('Open config file failed! Reason:', e)


def auto_conn(dev, chip, count, retry=5):
    global CONNECTED_DEVICE, SCANED_DEVICE, CHIP_FULL
    rssi = []
    tname = threading.current_thread().getName()
    for data in api.scan(active=1, chip=chip, filter_mac=dev):
        if data.startswith('data'):
            data = json.loads(data[5:])
            if len(rssi) < count:
                print('The device %s is %d times have been scaned,rssi is:%d.(%s)' % (
                    data['bdaddrs'][0]['bdaddr'], len(rssi) + 1, int(data['rssi']), tname))
                rssi.append(int(data['rssi']))
            else:
                dev_name = data['name']
                device_info = data['bdaddrs'][0]
                print('Start connect device %s.' % dev)
                i = 0
                while i < retry:
                    code, body, duration = api.connect_device(device_info['bdaddr'], device_info['bdaddrType'],
                                                              chip=chip, timeout=CONNECT_TIMEOUT)
                    time.sleep(2)
                    a, b = api.get_devices_list('connected')
                    if device_info['bdaddr'] in b:
                        msg = '\nDevice:{0:s} all rssi are :{1:s}\nAll rssi average is:{2:.2f}\nConnect duration is:{3:.2f}\ncontect times:{4:d}'.format(
                            dev, str(rssi), sum(rssi) / len(rssi), duration, i)
                        logger.info(msg)
                        print(msg)
                        write_csv([dev, dev_name, str(rssi), sum(rssi) / len(rssi), duration, i + 1])
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
                        print('设备 %s 第%d次连接失败，随机等待%d秒后重新连接' % (dev, i + 1, wait))
                        logger.debug('设备 %s 第%d次连接失败，随机等待%d秒后重新连接' % (dev, i, wait))
                        time.sleep(wait)
                        i += 1
                else:
                    print('达到最大重连次数，停止重连，设备 %s 连接失败,平均rssi为%.2f' % (dev, sum(rssi) / len(rssi)))
                    logger.info('达到最大重连次数，停止重连，设备 %s 连接失败.平均rssi为%.2f' % (dev, sum(rssi) / len(rssi)))
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
                _, _, duration = api.connect_device(dev, 'public', chip=chip, timeout=CONNECT_TIMEOUT)
            else:
                _, _, duration = api.connect_device(dev, 'public', timeout=CONNECT_TIMEOUT)
            time.sleep(2)
            a, b = api.get_devices_list('connected')
            if dev in b:
                SCANED_DEVICE.remove(dev)
                CONNECTED_DEVICE.append(dev)
                print(dev, 'duration(s):', duration, '| connected success!')
            else:
                if chip:
                    _, _, duration = api.connect_device(dev, 'random', chip=chip, timeout=CONNECT_TIMEOUT)
                else:
                    _, _, duration = api.connect_device(dev, 'random', timeout=CONNECT_TIMEOUT)
                time.sleep(2)
                if dev in b:
                    SCANED_DEVICE.remove(dev)
                    CONNECTED_DEVICE.append(dev)
                    print(dev, 'duration(s):', duration, '| connected success!')
            print('设备%s第%d次连接失败' % (dev, times + 1))
        if SCANED_DEVICE:
            times += 1
        else:
            print('All devs have been conntcted!')
            break
    else:
        print('达到最大重连次数，停止重连，设备%s连接失败' % str(SCANED_DEVICE))
        logger.debug('达到最大重连次数，停止连接，设备%s连接失败' % str(SCANED_DEVICE))


def re_conn(dev, chip=None, retry=5):
    global CONNECTED_DEVICE
    print('检测到设备 %s 断开连接，尝试重连该设备' % dev)
    logger.debug('\n检测到设备 %s 断开连接，尝试重连该设备...\n' % dev)
    i = 1
    while 1:
        if chip:
            code, body, duration = api.connect_device(device_info['bdaddr'], device_info['bdaddrType'], chip=chip,
                                                      timeout=CONNECT_TIMEOUT)
        else:
            code, body, duration = api.connect_device(device_info['bdaddr'], device_info['bdaddrType'],
                                                      timeout=CONNECT_TIMEOUT)
        time.sleep(2)
        a, b = api.get_devices_list('connected')
        if device_info['bdaddr'] in b:
            msg = '设备 %s 重新连接成功' % dev
            logger.info(msg)
            print(msg)
            write_csv([dev, dev_name, str(rssi), sum(rssi) / len(rssi), duration, i])
            CONNECTED_DEVICE.append(dev)
            print('当前成功连接的设备数量为：%d' % len(CONNECTED_DEVICE))
            for dev in CONNECTED_DEVICE:
                print(dev)
            break
        else:
            wait = random.randint(1, 10)
            print('设备 %s 第%d次连接失败，随机等待%d秒后重新连接' % (dev, i, wait))
            logger.debug('设备 %s 第%d次连接失败，随机等待%d秒后重新连接' % (dev, i, wait))
            time.sleep(wait)
        i += 1
        if i > retry + 1:
            print('达到最大重连次数，停止重连，设备%s连接失败.' % dev)
            break


def get_dev_list():
    a, b = api.get_devices_list('connected')
    data = json.loads(b)
    dev_count = len(data['nodes'])
    print('当前连接设备数量为：%d' % dev_count)
    for dev in data['nodes']:
        print(dev['id'])


def dis_all(api):
    a, b = api.get_devices_list('connected')
    nodes = json.loads(b)
    for device in nodes['nodes']:
        mac = device['id']
        api.disconnect_device(mac)


def get_msg(sseclient):
    for message in sseclient:
        if "keep-alive" in message:
            pass
        elif message.startswith('data'):
            print('Notification:' + message)
            msg = 'Notification:' + message
            logger.debug(msg)
            break


def write_csv(data):
    with open('logs/info.csv', 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data)


def get_connect_state():
    global CONNECTED_DEVICE
    for message in api.get_device_connect_state():
        # message = json.loads(event)
        message = str(message)
        print(message)
        if message.startswith('data'):
            msg = json.loads(message[:6])
            if msg['handle'] == 'disconnected':
                print('Device %s is disconnected,will reconnected.' % msg['handle'])
                CONNECTED_DEVICE.remove(msg['handle'])
                threading.Thread(target=re_conn, args=(msg['handle'], conf['chip'], conf['retry'])).start()


def main(conf):
    global SCANED_DEVICE, CHIP_FULL, CONNECTED_DEVICE
    if len(sys.argv) == 1:
        # device = []
        if not os.path.exists('logs/info.csv'):
            write_csv(['device', 'device type', 'rssis', 'average rssi', 'connected duration', 'connected times'])
        for data in api.scan(active=1, chip=conf['chip']):
            names = conf['device_type_name']
            if data.startswith('data'):
                data = json.loads(data[5:])
                for name in eval(names):
                    if name in data['name']:
                        print(data['name'])
                        if data['bdaddrs'][0]['bdaddr'] in SCANED_DEVICE:                       	
                            pass
                        elif data['bdaddrs'][0]['bdaddr'] in CONNECTED_DEVICE:
                        	CONNECTED_DEVICE.remove(data['bdaddrs'][0]['bdaddr'])
                        elif threading.active_count() < 10:
                            t = threading.Thread(target=auto_conn, args=(
                                data['bdaddrs'][0]['bdaddr'], conf['chip'], conf['rssi_count'],
                                conf['retry']), )
                            t.setDaemon(True)
                            t.start()
                            SCANED_DEVICE.append(data['bdaddrs'][0]['bdaddr'])
                            print('扫描到新设备 %s.' % data['bdaddrs'][0]['bdaddr'])
                        break  # 退出for name循环
                    break  # 退出for name循环
                if CHIP_FULL:
                    print('芯片连满，请切换芯片!')
                    break
    elif sys.argv[1] == 'dis_one':
        api.disconnect_device(sys.argv[2])
    elif sys.argv[1] == 'dis_all':
        dis_all(api)
    elif sys.argv[1] == 'conn':
        devs = eval(conf['devices'])  # 转换成列表
        conn(devs, conf['chip'], conf['retry'])
    elif sys.argv[1] == 'get':
        get_dev_list()
    elif sys.argv[1] == 'help' or '--help' or '-help':
        helps = [('commond:', "命令说明"),
                 ('None', '无参数，默认连接扫描到的配置文件中指定名称的设备,直到强制停止程序'),
                 ('conn', '连接配置文件中指定的一组设备'),
                 ('dis_one', '断连一个指定的设备'),
                 ('dis_all', '断连所有设备'),
                 ('get', '获取当前连接的所有设备'),
                 ('use example', "'python main.py conn'")]
        for a, b in helps:
            print('%-15s%-30s' % (a, b))
    else:
        helps = [('commond:', "命令说明"),
                 ('None', '无参数，默认连接扫描到的配置文件中指定名称的设备,直到强制停止程序'),
                 ('conn', '连接配置文件中指定的一组设备'),
                 ('dis_one', '断连一个指定的设备'),
                 ('dis_all', '断连所有设备'),
                 ('get', '获取当前连接的所有设备'),
                 ('use example', "'python main.py conn'")]
        for a, b in helps:
            print('%-15s%-30s' % (a, b))


if __name__ == '__main__':
    conf = get_conf()
    api = api(conf['host'], conf['ap'], conf['user'], conf['pwd'])
    if conf['auto_reconnect'] == 'True':
        threading.Thread(target = get_connect_state).start()
    main(conf)
