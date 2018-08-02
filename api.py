import requests
import time
import threading
import base64
import json
import sseclient


class api():

    '''
        para:update_header= False
        由于token有效期为1一小时，因此，如果脚本运行之间超过一个小时，应该
        传参数update_header= True，让其自动更新heders
        默认不自动更新
    '''

    def __init__(self,
                 host,
                 hub=None,  # 调用API的AP mac地址，当本地调用时该参数无效
                 user=None,  # AC上的开发者账号，本地调用时参数无效
                 pwd=None,        #
                 local=False,  # 是否采用本地调用，默认为否
                 model='E1000'  # AP的型号，E1000，X1000，S2000，S1000
                 ):
        self.host = host
        self.user = user
        self.pwd = pwd
        self.hub = hub
        self.model = model
        # print(self.host,self.user,self.pwd,self.hub,self.model)
        if local:
            self.local = True
            self.headers = None
        else:
            self.local = False
            self.set_header()

    def set_header(self):
        use_info = self.user + ':' + self.pwd
        # 编码开发者帐号
        encode_info = base64.b64encode(use_info.encode('utf-8'))
        head = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + encode_info.decode("utf-8")
        }
        data = {'grant_type': 'client_credentials'}
        try:
            # 发起请求
            res = requests.post(self.host + '/oauth2/token',
                                data=json.dumps(data), headers=head)
            # print(res.text,res.status_code)
            if res.status_code == 200:
                res_body = json.loads(res.text)
                # print(res_body.get("access_token"))
                TOKEN = res_body.get("access_token")
            elif res.status_code == 401:
                print('开发帐号错误')
            elif res.status_code == 400:
                print('API路径错误')
        except Exception as e:
            print(e)
            return
        headers = {
            'Content-Type': 'application/json',
            'version': '1',
            'Authorization': 'Bearer ' + TOKEN
        }
        self.headers = headers
        return headers

    """
        扫描接口的调用
        :paras:chip=0|1,active=0|1,duration=number,norepate=True|false
        :paras:filter_name=str,filter_mac=str,filter_rssi=number,filter_uuid=str
        :yield :scan data
        可以通过下面方式获取该函数的返回值
        for scan_data in api.scan(args):
            scan_data = json.loads(s[5:])
            device = scan_data['bdaddrs']
            device_mac = device[0]['bdaddr']	获取设备MAC
            device_type = device[0]['bdaddrType']	获取设备类型
    """

    def scan(self, **args):
        data = {"event": 1, 'mac': self.hub}
        if args:
            for key in args:
                if args[key]:
                    data[key] = args[key]
        url = self.host + '/gap/nodes'
        try:
            if not self.local:
                res = requests.get(
                    url, params=data, headers=self.headers, stream=True)
            else:
                res = requests.get(
                    url, params=data, stream=True)
            # print(res.url)
            if res.status_code == 200:
                for line in res.iter_lines():
                    scan_data = str(line, encoding='utf-8')
                    if scan_data.startswith('data'):
                        yield scan_data
            else:
                yield res.text
        except Exception as e:
            if 'NoneType' in str(e):
                pass
            else:
                print('SSE closeed!', threading.current_thread().name, e)

    # SSE连接，参考scan接口
    def get_device_connect_state(self):
        url = self.host + '/management/nodes/connection-state'
        data = {'mac': self.hub}
        res = requests.get(url, headers=self.headers, params=data, stream=True)
        if res.status_code == 200:
            for msg in res.iter_lines():
                yield str(msg, encoding='utf8')

    def connect_device(self, device, types='public', chip=None, timeout: int = None) -> str:
        if chip is None:
            values = {
                # 	timeout单位是ms
                'timeout': timeout,
                'type': types
            }
        else:
            values = {
                # 	timeout单位是ms
                'timeout': timeout,
                'type': types,
                "chip": chip
            }
        t_start = time.time()
        if not self.local:
            url = self.host + '/gap/nodes/' + device + '/connection?mac=' + self.hub
            res = requests.post(url, json=values, headers=self.headers)
        else:
            url = self.host + '/gap/nodes/' + device + '/connection?mac='
            res = requests.post(url, json=values)
        # print(res.url)
        if res.status_code == 200:
            t_end = time.time()
            duration = (t_end - t_start)
            # print(self.hub,'--->',device,'duration(s):',duration,'| connected success!')
            return res.status_code, res.text, duration
        else:
            t_end = time.time()
            duration = (t_end - t_start)
            # print(self.hub,'--->',device,'duration(s):',duration,'| connected failed! Reason:%s'%res.text)
            return res.status_code, res.text, duration

    def disconnect_device(self, device, timeout=5000):
        data = {'mac': self.hub, 'timeout': timeout}
        url = self.host + '/gap/nodes/' + device + '/connection'
        t_start = time.time()
        if not self.local:
            res = requests.delete(url, params=data, headers=self.headers)
        else:
            res = requests.delete(url, params=data)
        if res.status_code == 200:
            t_end = time.time()
            duration = (t_end - t_start)
            print('Device %s disconnect successed!' % device, duration)
            return res.status_code, res.text
        else:
            t_end = time.time()
            duration = (t_end - t_start)
            print(res.status_code, res.text,
                  '\nDevice %s disconnect failed!' % device, duration)
            return res.status_code, res.text

    def get_devices_list(self, state):
        data = {'mac': self.hub,
                'connection_state': state
                }
        url = self.host + '/gap/nodes/'
        if not self.local:
            res = requests.get(url, params=data, headers=self.headers)
        else:
            res = requests.get(url, params=data)
        if res.status_code == 200:
            # print('Get devices list successed:\n',res.text)
            return (res.status_code, res.text)
        else:
            print(res.status_code, res.text)
            return (res.status_code, res.text)

    '''
        下面四个函数返回值说明：
        discovery_services(self,device,uuid=None)
        discovery_charateristic(self,device_mac,charater_uuid)
        discover_descriptors(self,device_mac,charater_uuid)
        discover_descriptors(self,device_mac,charater_uuid)
        首先要弄清楚蓝牙服务的数据结构，如下面所示，分为三层，分别是：
        +services
         -service1
          +characteristics
           -characteristic1
            +descriptors
             -...
           -characteristic2
           ...
           -characteristicn
         -service2
         ...
         -servicen
        下面是个例子：
        +services 某个服务
         --00001800-0000-1000-8000-00805f9b34fb 服务的uuid
         --handle:1
           +characteristics  该服务下面的所有特征值
         --uuid:00002a00-0000-1000-8000-00805f9b34fb 第一个特征值的uuid
           --handle:3
           --properties:  read
           --valueHandle:3 以上全是第一个特征值的相关属性
          +descriptors 这层是该特征值的描述值，该层的属性为optional
          --uuid:00002a00-0000-1000-8000-00805f9b34fb 
            --handle:3
        结合上面的介绍，下面分别说明：
        discovery_services 函数返回某个设备下面的所有服务
        discovery_charateristic 函数返回某个服务下面的所有特征值
        discover_descriptors 函数返回某个服务下的某个特征值
        discover_descriptors 函数返回某个特征值的描述值

    '''

    def discovery_services(self, device, uuid=None):
        data = {
            'mac': self.hub,
            'uuid': uuid,
        }
        url = self.host + '/gatt/nodes/' + device + '/services/'
        res = requests.get(url, params=data, headers=self.headers)
        print(res.url)
        if res.status_code == 200:
            print('Discovery services successed:\n', res.text)
            return res.status_code, res.text
        else:
            print(res.status_code, res.text)
            return res.status_code, res.text

    def discovery_characteristics(self, device, service_uuid):
        data = {
            'mac': self.hub,
            'all': 1
        }
        url = self.host + '/gatt/nodes/' + device + \
            '/services/' + service_uuid + '/characteristics'
        res = requests.get(url, params=data, headers=self.headers)
        if res.status_code == 200:
            print('Discovery characteristics successed:\n', res.text)
            return res.status_code, res.text
        else:
            print(res.status_code, res.text)
            return res.status_code, res.text

    def discovery_charateristic(self, device, charater_uuid):
        data = {
            "mac": self.hub,
            "uuid": charater_uuid
        }
        url = self.host + '/gatt/nodes/' + device + '/characteristics'
        res = requests.get(url, params=data, headers=self.headers)
        if res.status_code == 200:
            print('Discovery characteristic successed:\n', res.text)
            return res.status_code, res.text
        else:
            print(res.status_code, res.text)
            return res.status_code, res.text

    def discover_descriptors(self, device, charater_uuid):
        url = self.host + '/gatt/nodes/' + device + '/characteristics/' + \
            charater_uuid + '/descriptors?mac=' + self.hub
        res = requests.get(url, headers=self.headers)
        if res.status_code == 200:
            print('Discovery descriptors successed:\n', res.text)
            return res.status_code, res.text
        else:
            print(res.status_code, res.text)
            return res.status_code, res.text

    '''
        This API returns the whole services & characteristics & desciptorsof the specified device
        可以理解为下面四个函数的返回值组合
            discovery_services 函数返回某个设备下面的所有服务
            discovery_charateristic 函数返回某个服务下面的所有特征值
            discover_descriptors 函数返回某个服务下的某个特征值
            discover_descriptors 函数返回某个特征值的描述值
    '''

    def discover_all(self, device):
        data = {"mac": self.hub}
        url = self.host + '/gatt/nodes/' + device + \
            '/services/characteristics/descriptors'
        res = requests.get(url, params=data, headers=self.headers)
        if res.status_code == 200:
            print('Discovery all successed:\n', res.text)
            return res.status_code, res.text
        else:
            print(res.status_code, res.text)
            return res.status_code, res.text

    def read_by_handle(self, device, handle):
        data = {"mac": self.hub}
        url = self.host + '/gatt/nodes/' + device + \
            '/handle/' + str(handle) + '/value'
        res = requests.get(url, params=data, headers=self.headers)
        if res.status_code == 200:
            print('Read by handle successed:\n', res.text)
            return res.status_code, res.text
        else:
            print(res.status_code, res.text)
            return res.status_code, res.text

    def write_by_handle(self, device, handle, handle_data):
        data = {"mac": self.hub}
        url = self.host + '/gatt/nodes/' + device + '/handle/' + \
            str(handle) + '/value/' + str(handle_data)
        res = requests.get(url, params=data, headers=self.headers)
        if res.status_code == 200:
            print('Write by handle successed:\n', res.text)
            return res.status_code, res.text
        else:
            print(res.status_code, res.text)
            return res.status_code, res.text

    # SSE连接，参考scan接口
    def recive_notification(self):
        data = {"mac": self.hub,
                "event": 1}
        url = self.host + '/gatt/nodes/'
        res = requests.get(url, headers=self.headers, params=data, stream=True)
        return res
        # for line in res.iter_lines():
        # 	message = str(line,encoding = 'utf-8')
        # 	if message:
        # 		yield message

    def start_advertise(self, chip, interval, adv_data, resp_data):
        data = {
            'mac': self.hub,
            'chip': chip,
            'interval': interval,
            'resp_data': resp_data
        }
        url = self.host + '/advertise/start'
        res = requests.get(url, headers=self.headers, params=data)
        if res.status_code == 200:
            print('Start advertise successed:\n', res.text)
            return res.status_code, res.text
        else:
            print(res.status_code, res.text)
            return res.status_code, res.text

    def stop_advertise(self, chip):
        data = {
            "mac": self.hub,
            "chip": chip
        }
        url = self.host + '/advertise/stop'
        res = requests.get(url, headers=self.headers, params=data)
        if res.status_code == 200:
            print('Stop advertise successed:\n', res.text)
            return res.status_code, res.text
        else:
            print(res.status_code, res.text)
            return res.status_code, res.text

if __name__ == '__main__':
    host = 'http://168.168.30.253/api'
    dev = 'EC:6F:47:BD:33:95'
    api = api(host, 'CC:1B:E0:E0:DC:68', 'tester', '10b83f9a2e823c47')
    # for x in api.scan():print(x)
    res = api.get_device_connect_state()
    for msg in res:
        print(msg)
    api.connect_device(dev, 'random')
    x = api.get_devices_list('connected')[1]
    print(dev in x)
    api.disconnect_device('EC:6F:47:BD:33:95')
