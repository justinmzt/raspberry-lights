# raspberry-lights
## 介绍
基于树莓派的智能灯，小项目的核心代码，使用python实现
## 硬件
- 带模拟量输出的声传感器模块 *3
- 带模拟量输出的光传感器模块 *1
- PCF8591 AD/DA模块 *1
- 二极管、线材若干 面包板一块
## 演示
```python
from device import Device
import time

check_interval = 0.01  # 设置获取i2c信息的间隔0.01秒

device = Device()  # 生成设备对象

while True:
    device.process()  # 进行环境参数判断反映到智能灯上
    device.getSensorVal()  # 获取环境参数
    time.sleep(check_interval)

```

## 文件结构
- i2c.py: 用于检测环境参数
- light.py: 用于控制智能灯
- device.py: 总设备调度，控制所有智能灯
- optical.py: 只获取光照参数，用于之后统计光照参数