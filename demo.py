from device import Device
import time

check_interval = 0.01  # 设置获取i2c信息的间隔0.01秒

device = Device()  # 生成设备对象

while True:
    device.process()  # 进行环境参数判断反映到智能灯上
    device.getSensorVal()  # 获取环境参数
    time.sleep(check_interval)