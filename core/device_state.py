from enum import Enum
from typing import Optional, Tuple
from .adb_manager import AdbManager
from .fastboot_manager import FastbootManager
class DeviceState(Enum):
    DISCONNECTED='disconnected'; ADB='adb'; RECOVERY='recovery'; SIDELOAD='sideload'; FASTBOOT='fastboot'; FASTBOOTD='fastbootd'; EDL='edl'
class DeviceDetector:
    def __init__(self, adb, fastboot):
        self.adb=adb; self.fastboot=fastboot
    def detect_state(self, serial=None):
        for s,state in self.adb.devices():
            if serial and s!=serial: continue
            if state=='device':
                mode=self.adb.get_prop('ro.bootmode',serial=s)
                if mode=='recovery': return DeviceState.RECOVERY,s
                elif mode=='sideload': return DeviceState.SIDELOAD,s
                else: return DeviceState.ADB,s
            elif state=='recovery': return DeviceState.RECOVERY,s
            elif state=='sideload': return DeviceState.SIDELOAD,s
        fb=self.fastboot.devices()
        if fb:
            first=fb[0]
            if serial and serial not in fb: return DeviceState.DISCONNECTED,None
            is_fastbootd = self.fastboot.getvar('is-userspace',first) == 'yes'
            return DeviceState.FASTBOOTD if is_fastbootd else DeviceState.FASTBOOT, first
        return DeviceState.DISCONNECTED,None
