from django.db import models
from datetime import datetime
import requests
import telnetlib


# Create your models here.

'''
class IP(models.Model):
    ip = models.CharField(max_length=16)
    iptype = models.CharField(max_length=16)
    province = models.CharField(max_length=16)
    city = models. CharField(max_length=16)
    isp = models.CharField(max_length=16)
    latitude = models.FloatField
    longitude = models.FloatField

    def get_info(self):
        pass
'''

class Router(models.Model):
    ip = models.GenericIPAddressField()
    iptype = models.CharField(max_length=16)
    ssid = models.CharField(max_length=32)
    mac = models.CharField(max_length=20, primary_key=True)
    passwd = models.CharField(max_length=32)
    lat = models.CharField(max_length=16)
    lng = models.CharField(max_length=16)
    accuracy = models.CharField(max_length=10)
    address = models.CharField(max_length=100)
    createtime = models.DateTimeField(default=datetime.now)
    province = models.CharField(max_length=16)
    city = models. CharField(max_length=16)
    isp = models.CharField(max_length=16)
    
    def get_info(self):
        username = 'admin'
        password = 'admin'
        TIMEOUT = 3
        cmdTime = 2

        t = telnetlib.Telnet(self.ip, timeout=TIMEOUT)
        d = t.read_some().decode('ascii')

        t.read_until(b'username:', cmdTime)
        t.write(username.encode('ascii') + b'\n')
        t.read_until(b'password:', cmdTime)
        t.write(password.encode('ascii') + b'\n')

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

        self.mac = mac
        self.ssid = ssid
        self.passwd = passwd

    def get_location(self):
        try:
            url = 'http://api.cellocation.com/wifi/?mac='+self.mac + '&output=csv'
            r = requests.get(url)
            v = r.text

            value = v.split(',')
            if value[0]=='0':
                info = [value[1],value[2],value[3],value[4]]
                return info
            else:
                print("Get " + self.mac+" locaition failed ...\n")
                return 0
        except Exception as e:
            print(e)

