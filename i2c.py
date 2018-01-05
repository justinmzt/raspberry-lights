# coding=utf-8
# 启动smbus查看i2c数据
from smbus import SMBus

# i2c配置
i2c_id = 1
i2c_address = 0x48  # 0x48是PCF8591 AD/DA 转换芯片的地址
opticalSensor_address = 64
soundSensor_address_1 = 65
soundSensor_address_2 = 66
soundSensor_address_3 = 67
optical_key = 'opticalVal'
sound_key = 'soundVal'

bus = SMBus(i2c_id)


def getI2c():
    opticalVal = bus.read_byte_data(i2c_address, opticalSensor_address)
    soundVal_1 = bus.read_byte_data(i2c_address, soundSensor_address_1)
    soundVal_2 = bus.read_byte_data(i2c_address, soundSensor_address_2)
    soundVal_3 = bus.read_byte_data(i2c_address, soundSensor_address_3)
    return {
        optical_key: opticalVal,
        sound_key: {
            0: soundVal_1,
            1: soundVal_2,
            2: soundVal_3,
        }
    }
