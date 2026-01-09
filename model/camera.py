# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 12:50:25 2024

@author: joudin
"""
import numpy as np
#from model.calculations import build_fake_image, make_random_noise
from tools.singleton import SingletonMeta
from typing_extensions import override
from model.calculations import build_fake_image, make_random_noise

# Active camera accessor (service) : stocke l'instance de caméra créée
_active_camera = None

def get_active_camera():
    return _active_camera

def _set_active_camera(cam):
    global _active_camera
    _active_camera = cam


class Camera(metaclass=SingletonMeta):
    def __str__(self):
        pass
        
    def connect(self) -> bool:
        pass
    
    def disconnect(self) -> None:
        pass
    
    def snapshot(self) -> np.array:
        pass

    def stop(self) -> None:
        pass
    
class SimulationCamera(Camera):
    def __init__(self,camera_type: str, camera_sn: str):
        self.camera_type = camera_type
        self.camera_sn = camera_sn

    @override
    def __str__(self):
        return f'********************\nCamera name : {self.camera_sn}\nSerial number : {self.camera_sn}\n********************'
    
    @override
    def connect(self) -> bool:
        print(f'Camera {self.camera_type} connected')
        return True

    @override
    def stop(self) -> None:
        print(f'Camera {self.camera_type} stopped')

    @override
    def snapshot(self) -> np.array:
        dim = (2000,2500)
        np_image = (build_fake_image(dim,250,250,100,100,200) +  3 * make_random_noise(dim)).astype(np.uint8)
        return np_image
    
    @override
    def disconnect(self):
        print(f'Camera  {self.camera_type} disconnected')


def create_camera(camera_type: str, camera_sn: str) -> Camera:
    if camera_type == "Simu":
        camera = SimulationCamera(camera_type, camera_sn)
        _set_active_camera(camera)
        print("SIMU camera recognized")
        return camera
    else:
        print("Camera not recognized")
    
