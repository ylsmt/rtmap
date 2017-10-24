import sys,os,django  
  
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) #把manage.py所在目录添加到系统目录  
os.environ['DJANGO_SETTINGS_MODULE'] = 'router.settings' #设置setting文件  
django.setup()#初始化Django环境   

from rtmap.models import Router
import requests
import telnetlib
from threading import Thread
import socket
import queue
import time
import logging


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def ip2num(ip):
    ip = [int(x) for x in ip.split('.')]
    return ip[0] << 24 | ip[1] << 16 | ip[2] << 8 | ip[3]

def num2ip(num):
    return '%s.%s.%s.%s' % ((num & 0xff000000) >> 24,
                            (num & 0x00ff0000) >> 16,
                            (num & 0x0000ff00) >> 8,
                            (num & 0x000000ff)
                            )

def ip_range(start, end):
    return [num2ip(num) for num in range(ip2num(start), ip2num(end) + 1)]

def MutiThread(iplist):
    que = queue.Queue()
    thread = []
    max_threads = 300
    threads = 300
    
    total = len(iplist)
    start = time.time()

# product ip into queue
    while iplist:
        thread1 = [ipProducer(que, host) for host in iplist[:threads]]

        for t1 in thread1:
            t1.start()

        for t in thread1:
            t.join()
           
        iplist = iplist[threads:]

# consume ip from queue
# threads' counts    max min

    size = que.qsize()
    if size:
        if size > max_threads:
            thread2 = [ipConsumer(que) for x in list(range(0,max_threads))]
        else:
            thread2 = [ipConsumer(que) for x in list(range(0,size))]
    
        for t in thread2:
            t.start()
        for t in thread2:
            t.join()
            
    c = time.time() - start
    cost = 'time: %0.2fs'%(c)
    logging.info('total:{}\t opend:{}\t time:{}'.format(total,size,cost))

class ipProducer(Thread):
    def __init__(self, que, host):
        Thread.__init__(self)
        self.que = que
        self.host = host
        self.setDaemon(True)

    def run(self):
        if isOpen(self.host):
            self.que.put(self.host)

class ipConsumer(Thread):
    def __init__(self, que):
        Thread.__init__(self)
        self.que = que
        self.setDaemon(True)

    def run(self):
        while not self.que.empty():
            host = self.que.get()
            info = get_router_info(host)
            if info:
                #if Router.objects.filter(mac=info[0]):
                #    print('{} exists'.format(info[0]))
                r = Router(ip=host, 
                        mac=info[0], 
                        ssid=info[1],
                        passwd=info[2], 
                        lat=info[3], 
                        lng=info[4],
                        accuracy=info[5],
                        address=info[6],
                        )
                #r.iptype = 'PUBLIC'
                r.iptype = 'NAT'
                r.isp = '中国移动'
                r.save()


def isOpen(ip):
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.settimeout(0.5)
    
    if sk.connect_ex((ip, 23)) == 0:
        return True
    
    else:
        return False
    '''
    try:
        sk.connect((ip,23))
        return True
    except Exception as e:
        # print(e)
        return False
    '''
    sk.close()


def get_router_info(ip):
    username = 'admin'
    password = 'admin'
    TIMEOUT = 5
    cmdTime = 3



    try:
        t = telnetlib.Telnet(ip, timeout=TIMEOUT)
        d = t.read_some().decode('ascii')
#        logging.info('{}\t{}'.format(ip, d))

        t.read_until(b'username:', cmdTime)
        t.write(username.encode('ascii') + b'\n')
        t.read_until(b'password:', cmdTime)
        t.write(password.encode('ascii') + b'\n')

#        读不出来 mecury(conf)
#        s = t.read_very_eager().decode('ascii')

#        if s:
#            logging.info('{}: {} || {}'.format(ip, d, s))
#            return
            

        t.write(b'lan show info\n')
        t.read_until(b'MACAddress', cmdTime)
        mac = t.read_very_eager().decode('ascii')[1:18]

        t.write(b'wlctl show\n')
        t.read_until(b'SSID', cmdTime)
        string = t.read_very_eager().decode('ascii')
        t.close()
        
        string = ''.join(string.split())
        ssid = string[1:string.find('QSS')]
        passwd = string[string.find('Key=') + 4:string.find('cmd')] if string.find('Key=') != -1 else ''

        router_info = []
        if mac and get_location(mac):
            macinfo = get_location(mac)
            # ['latitude','longitude','accuracy','address']
            router_info = [mac,ssid,passwd,macinfo[0],macinfo[1],macinfo[2],macinfo[3]]


            print('get router info %s' % ip)
            print('{}\t{}\t{}\t'.format(ssid,passwd,macinfo[3]))

        
        return router_info


   # except socket.timeout:
   #     pass
   # except EOFError:
   #     pass
        
    except Exception as e:
        pass

def get_location(mac):
    try:
        url = 'http://api.cellocation.com/wifi/?mac='+ mac + '&output=csv'
        r = requests.get(url)
        v = r.text

        info = []
        value = v.split(',')
        if value[0]=='0':
            info = [value[1],value[2],value[3],value[4]]
        else:
            print("Get " + mac+" location failed ...\n")

        return info

    except Exception as e:
        pass

def run(file):

    with open(file) as f:
        for line in f:
            ip = [line.split('-')[0], line.split('-')[1].strip()]
            startIp = ip[0]
            endIp = ip[1]
            iplist = ip_range(startIp, endIp)
            logging.info('{}-{}\t total: {}'.format(startIp, endIp, str(len(iplist))))
            MutiThread(iplist)

if __name__ == '__main__':

    ip_file = './rtmap/scripts/cdip.txt'

    log_path = './log/' + time.strftime("%Y-%m-%d", time.localtime()) +'/'
    mkdir(log_path)
    log_file_name = log_path + time.strftime("%Y-%m-%d-%H%M", time.localtime()) + '.log'
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(filename)s  %(levelname)s  %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=log_file_name,
                        filemode='w'
                        )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    try:
#        run(ip_file)
        startIp = '100.66.0.1'
        endIp = '100.66.255.255'
        iplist = ip_range(startIp, endIp)
        logging.info('{}-{}\t total: {}'.format(startIp, endIp, str(len(iplist))))
        MutiThread(iplist)
        
#        get_router_info('100.66.32.144')

    except KeyboardInterrupt:
        sys.exit()
