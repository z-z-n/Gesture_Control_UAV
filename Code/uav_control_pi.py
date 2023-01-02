from __future__ import print_function
import time
from dronekit import connect, VehicleMode, LocationGlobalRelative
import socket
import re
from pymavlink import mavutil

connection_string = '/dev/ttyUSB0'
print('Connectingto vehicle on: %s' % connection_string)

vehicle = connect(connection_string, wait_ready=True, baud=921600)

#以下为起飞定义函数
def arm_and_takeoff(aTargetAltitude):

    #设置模式
    vehicle.mode = VehicleMode("GUIDED")

    #解锁无人机
    print("Arming motors")
    vehicle.armed = True

    while not vehicle.armed:
       print(" Waiting forarming...")
       time.sleep(1)

    print("Taking off!")

    vehicle.simple_takeoff(aTargetAltitude)

    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)

        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:
            print("Reached targetaltitude")
            break

        time.sleep(1)


#以下为任意方向飞行控制函数
def send_body_ned_velocity(velocity_x, velocity_y, velocity_z, duration=0):
     msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,       # time_boot_ms (not used)
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_FRAME_BODY_NED, # frame Needs to be MAV_FRAME_BODY_NED for forward/back left/right control.
        0b0000111111000111, # type_mask
        0, 0, 0, # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z, # m/s
        0,0,0,
        0,0)
     for x in range(0,duration):
        vehicle.send_mavlink(msg)
       # time.sleep(1)
# x表示前后方向,y表示左右方向,z表示垂直高度方向

#定义无人机控制关闭
def plane_off():
    # 退出并清除vehicle对象
    print("Closevehicle object")
    vehicle.close()

#无人机初参数设置

print("Setdefault/target airspeed to 3") #设置空速
vehicle.airspeed = 1

#参数设置结束

print('takeoff')  # 起飞
arm_and_takeoff(1)  # 起飞1米
#以下为socket部分

s=socket.socket()
host='192.168.43.240'#socket.gethostname()
port=8086
s.bind((host,port))
print(host)
s.listen(5)
c,addr=s.accept()
print('address:',addr)
c.send(b'ok')
strin=None

strin1=None # 临时
flag=0 # 判断是否连接错误

#主控循环
while True:
    for i in range(3):
        try:
            c.send(b'ok')#要加断开连接处理。在send处
        except socket.error:
             flag=1
             break
    else:
        strin1 = c.recv(9)
        strin = strin1.decode()
        if len(strin) != 0 and re.match(r'\$[0-9]{2}#[0-9]{4}\$', strin):
            strin = strin.strip('$')
            p = re.compile(r'#+')
            temp1 = p.split(strin)
            dir = int(temp1[0])
            spe = int(temp1[1])
            spe_float=spe/100.0
            fly_float=spe_float
            if spe_float>=0.5:
                spe_float=0.5   #无人机速度不大于0.5m/s

            if fly_float>=0.2:
                fly_float=0.2   #无人机升降速度不大于0.2m/s

            if dir == 0:  # 返航
                break
            elif dir == 1:
                print('up', spe_float)  # 上升
                send_body_ned_velocity(0, 0, -fly_float, 1)  # 让无人机上升,速度0.5m/s,飞行时间1秒
            elif dir == 2:
                print('down', spe_float)  # 下降
                send_body_ned_velocity(0, 0, fly_float, 1)  # 让无人机下降,速度0.5m/s,飞行时间1秒
            elif dir == 3:
                print('left', spe_float)  # 向左飞行
                send_body_ned_velocity(0, -spe_float, 0, 1)  # 让无人机向左飞行,速度0.5m/s,飞行时间1秒
            elif dir == 4:
                print('right', spe_float)  # 向右飞行
                send_body_ned_velocity(0, spe_float, 0, 1)  # 让无人机向右飞行,速度0.5m/s,飞行时间1秒
            elif dir == 6:
                print('towards', spe_float)  # 向前飞行
                send_body_ned_velocity(spe_float, 0, 0, 1)  # 让无人机向前飞行,速度0.5m/s,飞行时间1秒
            elif dir == 7:
                print('back', spe_float)  # 向后飞行
                send_body_ned_velocity(-spe_float, 0, 0, 1)  # 让无人机向后飞行,速度0.5m/s,飞行时间1秒
            elif dir == 5 or dir == 8:
                print('stop', 0)  # 悬停
    if(flag==1):# 连接错误中断
        break

# 发送"降落"指令  
print("Land")
# 降落，只需将无人机的飞行模式切换成"Land"   
vehicle.mode = VehicleMode("LAND")
plane_off()
c.close()
