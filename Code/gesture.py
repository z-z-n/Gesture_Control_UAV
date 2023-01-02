import sys
import socket  # 导入 socket 模块
from multiprocessing import * #进程模块
from PIL import Image #图像保存
import ctypes#图像格式转换

sys.path.insert(0, "D:\应用安装\leapmotion开发\Leap_Motion_SDK_Win_3.1.3\LeapSDK\lib")

import Leap, time
minVelocity = 75.0  # type:float
maxVelocity = 35.0  # type:float
maxVelocity2 = maxVelocity * maxVelocity
keep = 4  # type: int #for the keep of gesture
miss = 0.0  # type: float
dic_keep = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0}
time_stamp_temp, vx, vy, vz, count = 0, 0, 0, 0, 0  # type: (long, float, float, float, int) #count for counts of frame
flag = 1  # for the first data's proper
flagback = 0#for exit

class item_pip:#管道通信封装数据的类
    def __init__(self,num,picture):
        """
        :type picture: Image
        """
        self.action=num
        self.image=picture

def is_straight(x, z):
    if x > 130:
        return (abs(x - z) / x) > 0.75
    elif x > 75:
        return (abs(x - z) / x) > 0.63
    else:
        return 0

def movemerge(x, y, z):
    if is_straight(x, y) and abs(x) > minVelocity and is_straight(x, z):
        return True
    else:
        return False

def isStop(x, y, z):
    return (x * x + y * y + z * z) < maxVelocity2  # 向量长度^2


def FullMove(x, y, z, s,frame):
    """
    :type frame: Leap.Frame
    """
    #leapmotion图像保存
    images = frame.images  # type: Leap.ImageList
    image1 = images[0]  # type: Leap.Image
    imagedata = ctypes.cast(image1.data.cast().__long__(), ctypes.POINTER(image1.width * image1.height * ctypes.c_ubyte)).contents
    image = Image.frombuffer("L", (image1.width, image1.height), imagedata, "raw", "L", 0, 1)

    global keep
    tx = abs(x)
    ty = abs(y)
    tz = abs(z)
    tempmax = max(tx, ty, tz)
    px=0
    pz=0
    if not isMove(frame):#判断是否是移动手势，手势有效性
        print "keep foremer gesture,velocity: %s mm/s" % dic_keep[keep]
        v = '$0' + '%d' % (keep + 1) + '#' + '%04d' % round(dic_keep[keep]) + '$'
        # print(s.recv(8))
        s.recv(8)
        s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
        con.send(item_pip(keep, image))
        return
    for hand in frame.hands:
        px=hand.palm_position.x#当前帧的手位置
        pz = hand.palm_position.z

    if tempmax == ty and movemerge(ty, tx, tz) and y > 0:
        print "up, velocity: %s mm/s" % ty    #在gesture中没有使用ty而是通过增加负号完成，没有影响
        v = '$01#' + '%04d' % round(ty) + '$'
        # print(s.recv(8))
        s.recv(8)
        s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
        keep = 0
        con.send(item_pip(keep,image))
        dic_keep[keep] = ty
    elif tempmax == ty and movemerge(ty, tx, tz) and y < 0:
        print "down, velocity: %s mm/s" % ty
        v = '$02#' + '%04d' % round(ty) + '$'
        # print(s.recv(8))
        s.recv(8)
        s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
        keep = 1
        con.send(item_pip(keep,image))
        dic_keep[keep] = ty
    elif tempmax == tx and movemerge(tx, ty, tz) and x < 0 and px<0:
        print "left, velocity: %s mm/s" % tx
        v = '$03#' + '%04d' % round(tx) + '$'
        # print(s.recv(8))
        s.recv(8)
        s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
        keep = 2
        con.send(item_pip(keep, image))
        dic_keep[keep] = tx
    elif tempmax == tx and movemerge(tx, ty, tz) and x > 0 and px>0:
        print "right, velocity: %s mm/s" % tx
        v = '$04#' + '%04d' % round(tx) + '$'
        # print(s.recv(8))
        s.recv(8)
        s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
        keep = 3
        con.send(item_pip(keep, image))
        dic_keep[keep] = tx
    elif tempmax == tz and movemerge(tz, tx, ty) and z < 0 and pz<0:
        print "ahead, velocity: %s mm/s" % tz
        v = '$06#' + '%04d' % round(tz) + '$'
        # print(s.recv(8))
        s.recv(8)
        s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
        keep = 5
        con.send(item_pip(keep, image))
        dic_keep[keep] = tz
    elif tempmax == tz and movemerge(tz, tx, ty) and z > 0 and pz>0:
        print "back, velocity: %s mm/s" % tz
        v = '$07#' + '%04d' % round(tz) + '$'
        # print(s.recv(8))
        s.recv(8)
        s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
        keep = 6
        con.send(item_pip(keep, image))
        dic_keep[keep] = tz
    elif isStop(tx,ty,tz):
        print "STOP!!!!"
        v = '$05#0000$'
        # print(s.recv(8))
        s.recv(8)
        s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
        keep = 4
        con.send(item_pip(keep, image))
        dic_keep[keep] = 0
    else:
        if (keep < 0 or keep > 6):#这个应该不会出现所以不进行管道通信了
            # print "WAIT!"
            v = '$08#0000$'
            # print(s.recv(8))
            s.recv(8)
            s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
        else:
            print "keep foremer gesture,velocity: %s mm/s" % dic_keep[keep]
            v = '$0' + '%d' % (keep + 1) + '#' + '%04d' % round(dic_keep[keep]) + '$'
            # print(s.recv(8))
            s.recv(8)
            s.sendall(v.encode())  # $开头0x哪一种飞行方式#2，2，2 8位向量#4速度$   没有向量就直接速度
            con.send(item_pip(keep, image))

def isMove(frame):
    """
    :type frame: Leap.Frame
    """
    finger_count=0
    position_flag=True#在规定的范围内
    for hand in frame.hands:
        position=hand.palm_position
        if (position.x*position.x+position.z*position.z+position.y*position.y) > 90000:#30cm范围内
            position_flag=False
        for finger in hand.fingers.extended():
            finger_count=finger_count+1
    if finger_count==5 and position_flag:#五指张开为移动手势
        return True
    else:
        return False

def isBack(frame):
    """
    :type frame: Leap.Frame
    """
    global flagback  # 返航手势
    global back_val #UI端的结束运行值
    #print "value="+str(back_val.value)
    if int(back_val.value)==1:
        flagback = 1
        return True

    if not frame.hands.is_empty:
        fincou = 0  # count for extened finger
        for hand in frame.hands:
            for finger in hand.fingers.extended():
                if finger.type != finger.TYPE_THUMB:
                    fincou = fincou + 1
        if fincou == 0:
            flagback = 1
            return True
        else:
            return False

class SampleListener(Leap.Listener):
    finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
    sock = None

    def on_init(self, controller):
        self.sock = socket.socket()  # 创建 socket 对象
        host = "192.168.43.243"  # socket.gethostname()  # 获取本地主机名
        port = 8086  # 设置端口号
        self.sock.connect((host, port))
        print "Initialized"
        valueset = 8688  # add
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, valueset)  # add

    def on_connect(self, controller):
        print "Connected"
        global con
        con.send(item_pip(-2,Image.open("./images/back.png")))#传送连接状态

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print "Disconnected"

    def on_exit(self, controller):
        print "Exited"
        for temp in range(3):
            self.sock.sendall('$00#0000$')
        self.sock.close()

    def on_frame(self, controller):
        # Get the most recent frame and report some basic information
        frame = controller.frame()

        if isBack(frame):
            return

       #print "Frame id: %d, timestamp: %d, hands: %d, fingers: %d" % (
            #frame.id, frame.timestamp, len(frame.hands), len(frame.fingers))
        global flagback, miss, time_stamp_temp, vx, vy, vz, count, flag

        if flag == 1:
            flag = 0
            # Get hands
            for hand in frame.hands:  # multipule hands one frame,all count
                handType = "Left hand" if hand.is_left else "Right hand"

                print "  %s, id %d, position: %s" % (
                    handType, hand.id, hand.palm_position)

                # Get the hand's normal vector and direction
                normal = hand.palm_normal
                direction = hand.direction

                print " velocity: %s" % hand.palm_velocity
                if hand.is_valid:
                    vx = vx + hand.palm_velocity.x
                    vy = vy + hand.palm_velocity.y
                    vz = vz + hand.palm_velocity.z
                    count = count + 1#count用来计数，有几个帧
                    #print'v'
            if frame.hands.is_empty:
                miss = miss + 1#miss用来计没有手的次数
                count = count + 1
            time_stamp_temp = frame.timestamp

        if frame.timestamp - time_stamp_temp < 120000: # 时间速度平均
            for hand in frame.hands:  # multipule hands one frame,all count
                handType = "Left hand" if hand.is_left else "Right hand"

                # print "  %s, id %d, position: %s" % (handType, hand.id, hand.palm_position)
                # print " velocity: %s" % hand.palm_velocity
                if hand.is_valid:
                    vx = vx + hand.palm_velocity.x
                    vy = vy + hand.palm_velocity.y
                    vz = vz + hand.palm_velocity.z
                    count = count + 1#count用于计数
            if frame.hands.is_empty:
                count = count + 1
                miss = miss + 1#与gesture不同

        else:
            m=frame.timestamp - time_stamp_temp
            if m>400000:#检查延时间隔
                count=1
                print 'flag 大时间间隔'
            print m
            if count !=0 and miss / count > 0.5:
                miss = 0.0
                count=0
                v = '$0' + '%d' % (keep + 1) + '#' + '%04d' % round(dic_keep[keep]) + '$'
                self.sock.recv(8)
                self.sock.sendall(v.encode())

                images = frame.images  # type: Leap.ImageList
                image1 = images[0]  # type: Leap.Image
                imagedata = ctypes.cast(image1.data.cast().__long__(),ctypes.POINTER(image1.width * image1.height * ctypes.c_ubyte)).contents
                image = Image.frombuffer("L", (image1.width, image1.height), imagedata, "raw", "L", 0, 1)
                con.send(item_pip(keep, image))
                #print v
                time_stamp_temp = frame.timestamp
                vx, vy, vz = 0, 0, 0

            elif count!=0:#有帧，且时间间隔超过前面的要求
                vx = vx / count
                vy = vy / count
                vz = vz / count
                print(vx, vy, vz)
                FullMove(vx, vy, vz,self.sock,frame)
                count = 0
                time_stamp_temp = frame.timestamp
                vx, vy, vz = 0, 0, 0
            else:
                # 触发比如长时间没有手，自动降低帧数
                print str(miss) + ", " + str(count)
                images = frame.images  # type: Leap.ImageList
                image1 = images[0]  # type: Leap.Image
                imagedata = ctypes.cast(image1.data.cast().__long__(),ctypes.POINTER(image1.width * image1.height * ctypes.c_ubyte)).contents
                image = Image.frombuffer("L", (image1.width, image1.height), imagedata, "raw", "L", 0, 1)
                con.send(item_pip(keep, image))


def main(conn,val):
    """

    :type conn: (Pipe())[1]
    """
    global flagback
    global con#管道
    global back_val#value值共享内存，用于结束手势识别
    con=conn  # type: (Pipe())[1]
    back_val=val  # type: Value()

    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)
    # can get data at background
    controller.set_policy_flags(1)
    # can get images data
    controller.set_policy(Leap.Controller.POLICY_IMAGES)
    # whether connected to the device
    print(controller.is_connected)
    # Keep this process running until gesture is 1
    while True:
        if flagback == 1:
            #print 'END1!'
            conn.send(item_pip(-1,Image.open("./images/back.png")))#发送返回状态
            #send时候必须要那边还能收，不然下面无法执行
            conn.close()
            #print 'END2!'
            # Remove the sample listener when done
            controller.remove_listener(listener)
            break

if __name__ == "__main__":
    main()
