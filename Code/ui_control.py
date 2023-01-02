import os
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from multiprocessing import *
from PIL import ImageQt
from widget_v2 import Ui_Widget
from gesture_V3 import *
import json
import time
import win32gui
#start = time.time() #测试手势图像打印时间

class Widget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_Widget()
        self.ui.setupUi(self)
        self.timer=QTimer(self)  # 定时器
        self.timer.start(100)  #0.1s更新一次
        self.value_end=Value('i',0)#用于点击结束时让手势代码自己结束
        #管道通信用于传递无人机飞行动作和手势灰度图
        self.parent_conn, self.child_conn = Pipe()
        self.my_process = Process(target=main, args=(self.child_conn,self.value_end,))
        #self.subpro_flag=1#设置flag，当子进程已经结束时不在运行kill子进程

        self.ui.pushButton_start.clicked.connect(self.show_vs)
        self.ui.pushButton_return.clicked.connect(self.return_clicked)

        #获取天气
        self.get_weather()
        #获取leapmotion连接状态

        wid = win32gui.FindWindow("WindowsForms10.Window.8.app.0.fcf9a4_r6_ad1",
                                  "Mission Planner 1.3.76 build 1.3.8029.15962")
        start = time.time()
        while wid == 0:
            time.sleep(0.01)
            wid = win32gui.FindWindow("WindowsForms10.Window.8.app.0.129c866_r6_ad1",
                                      "Mission Planner 1.3.76 build 1.3.8029.15962")
            end = time.time()
            if end - start > 5:
                return
        self.parwid = wid
        # print wid
        windGps1 = QWindow.fromWinId(wid)
        windGps1.setFlags(windGps1.flags() | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        ww31 = QWidget.createWindowContainer(windGps1, self.ui.widget_gps_img, Qt.Widget)
        # time.sleep(5)
        ww31.setMinimumSize(1050, 820)

    def show_vs(self):
        self.my_process.start()
        self.timer.timeout.connect(self.change_g)

    def change_g(self):
        #print("#")
        global start
        QApplication.processEvents()
        item1=self.parent_conn.recv()  # type: item_pip
        a=item1.action
        if a==-2:#连接状态
            self.ui.label_light1.setStyleSheet(u"min-width: 20px; min-height: 20px;max-width:20px; max-height: 20px;border-radius: 10px;background-color:green;border: 1px solid gray;padding: -1px;")
        else:
            qimage = ImageQt.toqpixmap(item1.image)
            self.ui.label_gray_img.setPixmap(qimage)
        #end = time.time()
        #print end-start
        #start=end
        if a ==0:
            self.ui.widget_gesture_img.setStyleSheet(u"border-image: url(./images/g_up.png);")
            #print(0)
        elif a==1:
            self.ui.widget_gesture_img.setStyleSheet(u"border-image: url(./images/g_down.png);")
            #print(1)
        elif a==2:
            self.ui.widget_gesture_img.setStyleSheet(u"border-image: url(./images/g_l.png);")
            #print(2)
        elif a==3:
            self.ui.widget_gesture_img.setStyleSheet(u"border-image: url(./images/g_r.png);")
            #print(3)
        elif a==4:
            self.ui.widget_gesture_img.setStyleSheet(u"border-image: url(./images/g_stop.png);")
        elif a==5:
            self.ui.widget_gesture_img.setStyleSheet(u"border-image: url(./images/g_f.png);")
        elif a==6:
            self.ui.widget_gesture_img.setStyleSheet(u"border-image: url(./images/g_b.png);")
        elif a==-1:
            self.ui.widget_gesture_img.setStyleSheet(u"border-image: url(./images/g_return.png);")
            #self.ui.label_gray_img.setPixmap(QPixmap("./images/back.png"))
            self.timer.stop()
            #关闭计时器停止接收消息，设置返回状态
            self.ui.label_light3.setStyleSheet(u"min-width: 20px; min-height: 20px;max-width:20px; max-height: 20px;border-radius: 10px;background-color:green;border: 1px solid gray;padding: -1px;")
            #设备连接状态红灯，返回状态绿灯
            self.ui.label_light1.setStyleSheet(u"min-width: 20px; min-height: 20px;max-width:20px; max-height: 20px;border-radius: 10px;background-color:red;border: 1px solid gray;padding: -1px;")
            #self.subpro_flag=0

    def return_clicked(self):
        sender=self.sender()
        self.value_end.value=1
        #管道结束
        #os.system('taskkill /f /pid %s' % self.my_process.pid)
        #self.timer.stop()

        #print 'return被点击'

    def get_weather(self):
        #获取公网ip
        import requests
        #http://whatismyip.akamai.com/ 快
        #https: // checkip.amazonaws.com
        #https://ipecho.net/plain
        ip = requests.get('https://ipecho.net/plain').text.strip()
        #print ip
        #获取地址
        #resp = requests.get(url='http://ip-api.com/json/%s?lang=zh-CN' % (ip))
        #data = resp.json()
        resp = requests.get(url='http://ip-api.com/line/%s?lang=zh-CN' % (ip))#可以用field传来参数
        country='中国'
        province='江苏省'
        city = '南京'
        area = country + ', ' + province + ', ' + city
        temperature = 'None' + '°'
        suit_for_fly = "未联网，请自行判断"
        if resp.status_code==200:
            #网络状态
            self.ui.label_light2.setStyleSheet(u"min-width: 20px; min-height: 20px;max-width:20px; max-height: 20px;border-radius: 10px;background-color:green;border: 1px solid gray;padding: -1px;")
            content= resp.content
            text=content.decode(encoding="utf-8")
            #print text
            temp= text.split()
            country= temp[1]
            province=temp[4]
            city=temp[5]

            # 获取天气
            rb = requests.get('http://wthrcdn.etouch.cn/weather_mini?city=%s' % (city))
            rb.encoding = 'utf-8'
            data = json.loads(rb.text)
            # data = rb.text.json()
            # 访问今天的天气情况
            temperature = data['data']['wendu']
            temperature = temperature.encode('utf8')
            windt = data['data']['forecast'][0]['fengli']
            wind = windt[9:-3]  # 除去不需要的
            wind = wind.encode('utf8')
            i = len(wind)
            if i == 5:  # 风力超过10级
                windnum = wind[0:2]
            else:
                windnum = wind[0]
            windnum = int(windnum)

            typetmp = data['data']['forecast'][0]['type']  # 天气类型
            type = typetmp.encode('utf8')
            rain = type.find("雨")  # 天气是否下雨
            suit_for_fly = "适宜飞行"
            if rain != -1 or windnum > 5:
                suit_for_fly = "不适宜飞行"
            # print suit_for_fly
            area = country + ', ' + province + ', ' + city
            area = area.encode('utf8')
            temperature = temperature + '°'
        # print country
        # print province
        # print city
        self.ui.label_weather1.setText(temperature)
        self.ui.label_weather2.setText(area)
        self.ui.label_weather3.setText(suit_for_fly)

if __name__ == '__main__':

    # parent_conn, child_conn = Pipe()  # 1.创建一个链路 父进程 子进程
    app = QApplication([])
    stats = Widget()
    stats.show()
    sys.exit(app.exec_())
