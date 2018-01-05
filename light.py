# coding=utf-8
import redis as Redis  # 连接redis，用来存放亮灯记录

redis = Redis.StrictRedis(host='localhost', port=6379, db=0)
redis_key = "pwl_record"

import time

rightBrace = "}"  # 存放用于字符串输出用

# 声控传感器敏感度对应表，4~0敏感度递减。单位（ADC最小精度）
sound_sensor_sensitivity_map = {
    4: 3,
    3: 5,
    2: 8,
    1: 10,
    0: 15
}

"""
智能灯父类，用于定义智能灯基本参数、方法。

Parameters:
self.id: {Number} 0,1,2, 智能灯的序号
self.gpioSetting: {Table} gpio对象
self.gpio: {Number} gpio引脚号
self.on: {Boolean} 智能灯是否开启，True为开启。
self.light_on: {String} 智能灯开启存放的部分信息。
self.light_off: {String} 智能灯关闭存放的部分信息。

self.switchOn(self): {function} 打开智能灯。

self.switchOff(self): {function} 关闭智能灯。

self.pushRecord(self, action): {function} 存放信息
    @:param action: {Boolean}开启/关闭动作（True是开启）

self.process(self, opticalSensorVal, soundSensorValues, threshold): {function} 小灯根据传感器值进行操作
    @:param opticalSensorVal: {Number} 光传感器值
    @:param soundSensorValues: {Number} 声传感器值
    @:param threshold: {Number} 光感阈值
"""


class Light:
    def __init__(self, dict):
        import RPi.GPIO as GPIO
        self.gpio = dict['gpio']
        self.brightness = dict['brightness']
        self.gpioSetting = GPIO
        self.gpioSetting.setmode(self.gpioSetting.BCM)
        for i in range(len(self.gpio)):
            self.gpioSetting.setup(self.gpio[i], self.gpioSetting.OUT)
        # self.pre_gpio = dict['pre_gpio']
        self.id = dict['id']
        self.on = False
        self.light_on = "{\"id\": " + str(self.id) + ", \"brightness\": " + str(
            self.brightness) + ", \"action\": true, \"occur_at\": "
        self.light_off = "{\"id\": " + str(self.id) + ", \"action\": false, \"occur_at\": "
        for i in range(len(self.gpio)):
            if self.gpioSetting.input(self.gpio[i]):
                self.switchOff()

    def switchOn(self):
        for i in range(self.brightness):
            self.gpioSetting.output(self.gpio[i], True)
        self.on = True
        self.pushRecord(True)

    def switchOff(self):
        self.pushRecord(False)
        self.on = False
        for i in range(len(self.gpio)):
            self.gpioSetting.output(self.gpio[i], False)

    def pushRecord(self, action):
        time_str = str(time.time())
        if action:
            output = self.light_on + time_str + rightBrace
        else:
            output = self.light_off + time_str + rightBrace
        redis.rpush(redis_key, output)

    def process(self, opticalSensorVal, soundSensorValues, threshold):
        pass


"""
光控亮暗智能灯类（继承智能灯父类），用于定义光控亮暗智能灯参数、方法。

Parameters:
self.process(self, opticalSensorVal, soundSensorValues, threshold): {function} （方法重写）根据光感数值判断灯亮暗
    @:param opticalSensorVal: {Number} 光传感器值
    @:param soundSensorValues: {Number} 声传感器值
    @:param threshold: {Number} 光感阈值
"""


class LightWithOpticalSensor(Light):
    def __init__(self, dict):
        Light.__init__(self, dict)
        self.sleep = 2
        self.end = 0

    def setSleep(self):
        self.end = time.time() + self.sleep

    def process(self, opticalSensorVal, soundSensorValues, threshold):
        if self.end < time.time():
            if opticalSensorVal > threshold:
                if not self.gpioSetting.input(self.gpio[0]):
                    self.switchOn()
                    self.setSleep()
            else:
                if self.gpioSetting.input(self.gpio[0]):
                    self.switchOff()
                    self.setSleep()


"""
光控声控智能灯类（继承智能灯父类），用于定义光控声控智能灯参数、方法。

Parameters:
self.duration: {Number} 亮灯时间间隔
self.sensitivity: {Number} 声控敏感度
self.queue: {List} 记录前后两次声控信息进行比较
self.end: {Time} 亮灯结束时间戳

self.switchOn(self): {function} （方法重写）打开智能灯，并设置关灯时间。

self.getSoundSensorVal(self, soundSensorValues): {function} 将声感数值入队

self.check(self): {function} 判断是否声控亮灯

self.checkTime(self): {function} 判断是否时间到了灭灯

self.process(self, opticalSensorVal, soundSensorValues, threshold): {function} （方法重写）根据光感数值和声控数值判断灯亮暗
    @:param opticalSensorVal: {Number} 光传感器值
    @:param soundSensorValues: {Number} 声传感器值
    @:param threshold: {Number} 光感阈值
"""


class LightWithOpticalSoundSensor(Light):
    def __init__(self, dict):
        Light.__init__(self, dict)
        self.duration = dict['duration']
        self.sensitivity = dict['sensitivity']
        soundSensorVal = dict['soundSensorValues'][self.id]
        self.queue = [soundSensorVal, soundSensorVal]
        self.end = 0

    def switchOn(self):
        for i in range(self.brightness):
            self.gpioSetting.output(self.gpio[i], True)
        self.on = True
        self.pushRecord(True)
        self.end = time.time() + self.duration

    def getSoundSensorVal(self, soundSensorValues):
        self.queue.pop()
        self.queue.insert(0, soundSensorValues[self.id])

    def check(self):
        if abs(self.queue[0] - self.queue[1]) > self.sensitivity:
            if self.on:
                self.end = time.time() + self.duration
            else:
                self.switchOn()

    def checkTime(self):
        if self.on and self.end < time.time():
            self.switchOff()

    def process(self, opticalSensorVal, soundSensorValues, threshold):
        self.getSoundSensorVal(soundSensorValues)
        if opticalSensorVal > threshold:
            self.check()
            self.checkTime()
        else:
            if self.gpioSetting.input(self.gpio[0]):
                self.switchOff()


"""
常亮光控声控亮度智能灯类（继承智能灯父类），用于定义光控声控亮度智能灯参数、方法。

Parameters:
self.duration: {Number} 亮灯时间间隔
self.sensitivity: {Number} 声控敏感度
self.queue: {List} 记录前后两次声控信息进行比较
self.end: {Time} 提高亮度结束时间戳
self.up: {Boolean} 记录是否在提高亮度状态
self.light_up: {String} 下同输入数据时预设字符串
self.light_down: {String}
self.brightness_txt: {String}

self.switchUp(self): {function} 打开提高智能灯亮度，并设置恢复亮度等待时间。
self.switchDown(self): {function} 恢复平时智能灯亮度。

self.getSoundSensorVal(self, soundSensorValues): {function} 将声感数值入队

self.check(self): {function} 判断是否声控提升亮度

self.checkTime(self): {function} 判断是否时间到了恢复暗的亮度

self.pushUpDownRecord(self, action): {function} 记录数据

self.process(self, opticalSensorVal, soundSensorValues, threshold): {function} （方法重写）根据光感数值和声控数值判断灯亮暗
    @:param opticalSensorVal: {Number} 光传感器值
    @:param soundSensorValues: {Number} 声传感器值
    @:param threshold: {Number} 光感阈值
"""


class LightWithAdjustLightness(Light):
    def __init__(self, dict):
        Light.__init__(self, dict)
        self.duration = dict['duration']
        self.sensitivity = dict['sensitivity']
        soundSensorVal = dict['soundSensorValues'][self.id]
        self.queue = [soundSensorVal, soundSensorVal]
        self.end = 0
        self.up = False
        self.switchOn() // 平时为常亮状态
        self.light_up = "{\"id\": " + str(self.id) + ", \"action\": true, \"occur_at\": "
        self.light_down = "{\"id\": " + str(self.id) + ", \"action\": true, \"occur_at\": "
        self.brightness_txt = ", \"brightness\": "

    def switchUp(self):
        self.gpioSetting.output(self.gpio[self.brightness], True)
        self.up = True
        self.pushUpDownRecord(True)
        self.end = time.time() + self.duration

    def switchDown(self):
        self.pushUpDownRecord(False)
        self.up = False
        self.gpioSetting.output(self.gpio[self.brightness], False)

    def getSoundSensorVal(self, soundSensorValues):
        self.queue.pop()
        self.queue.insert(0, soundSensorValues[self.id])

    def check(self):
        if abs(self.queue[0] - self.queue[1]) > self.sensitivity:
            if self.up:
                self.end = time.time() + self.duration
            else:
                self.switchUp()

    def checkTime(self):
        if self.up and self.end < time.time():
            self.switchDown()

    def pushUpDownRecord(self, action):
        time_str = str(time.time())
        if action:
            output = self.light_up + time_str + self.brightness_txt + str(self.brightness + 1) + rightBrace
        else:
            output = self.light_down + time_str + self.brightness_txt + str(self.brightness) + rightBrace
        redis.rpush(redis_key, output)

    def process(self, opticalSensorVal, soundSensorValues, threshold):
        self.getSoundSensorVal(soundSensorValues)
        if opticalSensorVal > threshold:
            self.check()
            self.checkTime()
        else:
            if self.gpioSetting.input(self.gpio[0]):
                self.switchDown()
