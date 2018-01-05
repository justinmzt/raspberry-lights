# coding=utf-8
import i2c  # 导入i2c AD模块

from pymongo import MongoClient  # 连接mongoDB，读取配置

client = MongoClient()
db = client.powerful_light

# 导入智能灯类
from light import Light
from light import LightWithOpticalSensor
from light import LightWithOpticalSoundSensor
from light import LightWithAdjustLightness

"""
设备类，设备的变量与方法

Parameters:
self.threshold: {Number} 光感阈值，当光感数值超过这个阈值，才使某些功能有效
self.lights: {List} 设备管控的智能灯对象
self.opticalVal: {Number} 此刻光感传感器数值。
self.soundSensorValues: {List} 此刻声感传感器的数值数组。

self.process(self): {function} 用于检测此刻小灯对应
self.getSensorVal(self): {function} 获取传感器数值
"""


class Device:
    def __init__(self):
        # 获取第一条设备配置信息
        device = db.devices.find_one({})
        self.opticalVal = 0
        self.soundSensorValues = {}
        self.threshold = device['threshold']
        self.lights = []
        self.getSensorVal()
        # 获取所有灯配置信息
        for item in db.lights.find({}):
            type = item['type']
            if type == 0:
                print("常亮")
                light = Light({
                    'id': item['id'],
                    'gpio': item['GPIO'],
                    'brightness': item['brightness'],
                })
                light.switchOn()
                self.lights.append(light)
            elif type == 1:
                print("常暗")
                self.lights.append(Light({
                    'id': item['id'],
                    'gpio': item['GPIO'],
                    'brightness': item['brightness'],
                }))
            elif type == 2:
                print("光控智能")
                self.lights.append(LightWithOpticalSensor({
                    'id': item['id'],
                    'gpio': item['GPIO'],
                    'brightness': item['brightness'],
                }))
            elif type == 3:
                print("光控+声控智能")
                self.lights.append(LightWithOpticalSoundSensor({
                    'id': item['id'],
                    'soundSensorValues': self.soundSensorValues,
                    'gpio': item['GPIO'],
                    'brightness': item['brightness'],
                    'duration': item['time'],
                    'sensitivity': sound_sensor_sensitivity_map[item['sensitivity']]
                }))
            elif type == 4:
                print("光控+声控调光")
                self.lights.append(LightWithAdjustLightness({
                    'id': item['id'],
                    'soundSensorValues': self.soundSensorValues,
                    'gpio': item['GPIO'],
                    'brightness': item['brightness'],
                    'duration': item['time'],
                    'sensitivity': sound_sensor_sensitivity_map[item['sensitivity']]
                }))
            else:
                print("出错")

    def process(self):
        for light in self.lights:
            light.process(self.opticalVal, self.soundSensorValues, self.threshold)

    def getSensorVal(self):
        dict = i2c.getI2c()
        self.opticalVal = dict['opticalVal']
        self.soundSensorValues = dict['soundVal']
