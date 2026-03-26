# -*- coding: utf-8 -*-
"""
Created on Thu Oct  3 12:50:25 2024

@author: joudin
"""
import numpy as np
#from model.calculations import build_fake_image, make_random_noise
from tools.singleton import SingletonMeta
from typing_extensions import override
from model.calculations import build_fake_spot_laser_image, make_random_noise, build_fake_apd_image, filter_intensity_range
from model.data_supplements import XDIM, YDIM
import tools.NITLibrary_x64_252_py38 as NIT
import threading
from model.data_supplements import XDIM, YDIM

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
    
    def snapshot(self, object:str) -> np.array:
        pass

    def stop(self) -> None:
        pass
    
class SimulationCamera(Camera):
    def __init__(self,camera_type: str, camera_sn: str):
        self.camera_type = camera_type
        self.camera_sn = camera_sn
        self.x_centroid_simu = int(XDIM/2)
        self.y_centroid_simu = int(YDIM/2)
        self.width_simu = 103
        self.amplitude_simu = 200

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
    def snapshot(self, object:str) -> np.array:
        dim = (YDIM,XDIM)
        if object == 'SPOT_LASER':
            np_image = (build_fake_spot_laser_image(dim,self.x_centroid_simu, self.y_centroid_simu, self.width_simu,self.width_simu,self.amplitude_simu) +  3 * make_random_noise(dim))#.astype(np.uint8)
        elif object == 'APD':
            #np_image = (build_fake_apd_image(dim,self.x_centroid_simu,self.y_centroid_simu,self.width_simu,5,100).T + 3 * make_random_noise(dim)).astype(np.uint8)
            np_image = build_fake_apd_image(dim,self.x_centroid_simu,self.y_centroid_simu,self.width_simu,300,self.amplitude_simu).T# + 3 * make_random_noise(dim)).astype(np.uint8)
        else:
            np_image = make_random_noise(dim)#.astype(np.uint8)

        return np_image
    
    @override
    def disconnect(self):
        print(f'Camera {self.camera_type} disconnected')
   
class OneShotObserver(NIT.NITUserObserver):
    def __init__(self):
        super().__init__()
        self.event = threading.Event()
        self.frame = None
        self.info = None

    def onNewFrame(self, array, info):
        """
        Méthode appelée automatiquement par le SDK
        dès qu'une nouvelle image arrive.
        """
        # Copier impérativement pour détacher du buffer interne du SDK
        self.frame = array.copy()
        self.info = info
        self.event.set()

    # Les deux méthodes suivantes sont optionnelles :
    def onStart(self):
        pass

    def onStop(self):
        pass

class NitCamera(Camera):
    def __init__(self,camera_type: str, camera_sn: str):
        self.camera_type = camera_type
        self.camera_sn = camera_sn
        self.dev = None
        self.obs = None

    @override
    def __str__(self):
        return f'********************\nCamera name : {self.camera_sn}\nSerial number : {self.camera_sn}\n********************'
    
    @override
    def connect(self) -> bool:
        status = False
        try:
            NIT.NITManager.useUsb = True
            self.mgr = NIT.NITManager.getInstance()

            # 2) Ouvrir la caméra
            self.dev = self.mgr.openOneDevice()
        
            # 3) Instancier notre observer
            self.obs = OneShotObserver()

            # 4) Brancher l'observer dans le pipeline
            self.dev << self.obs
            status = True
            print(f'Camera {self.camera_type} connected')

        except:
            print(f'Echec connexion camera {self.camera_type}')

        try:
            self.dev.setParamValueOf("Exposure Time", 100)
            current = self.dev.paramStrValueOf("Exposure Time")
            print("Exposure =", current)
        except:
            print("Echec réglage de l'exposition")
        return status

    @override
    def stop(self) -> None:
        print(f'Camera {self.camera_type} stopped')

    @staticmethod
    def _normalize_for_display(image: np.array) -> np.array:
        """
        Convertit l'image en 8-bit pour l'affichage sans suramplifié le bruit.
        Utilise une normalisation robuste basée sur les percentiles.
        """
        if image is None:
            return None

        if image.dtype == np.uint8:
            return image

        # Pour les formats 12/14/16 bits provenant de la caméra NIT
        img = image.astype(np.float32)
        
        # Normalisation robuste : utiliser percentiles 2%-98% au lieu de min/max
        # pour éviter que des pixels de bruit extrêmes n'amplifient tout
        p2 = np.percentile(img, 2)
        p98 = np.percentile(img, 98)
        
        if p98 == p2:
            return np.zeros_like(img, dtype=np.uint8)

        # Limiter (clip) l'image aux percentiles, puis normaliser
        img_clipped = np.clip(img, p2, p98)
        normalized = 255.0 * (img_clipped - p2) / (p98 - p2)
        return normalized.astype(np.uint8)

    @override
    def snapshot(self, object:str) -> np.array:
        self.dev.captureNFrames(1)

        # attendre l’arrivée d’une frame
        self.dev.waitEndCapture()

        if self.obs.frame is None:
            #raise TimeoutError("Aucune image reçue avant timeout.")
            dim = (YDIM,XDIM)
            return np.zeros(dim, dtype=np.uint8)

        # le SDK NIT peut renvoyer uint16 (12 bits utile) : filtrer puis normaliser en 8 bits
        np_image = self.obs.frame
        # Assurer la bonne orientation (height, width) = (YDIM, XDIM)
        if np_image.shape != (YDIM, XDIM):
            np_image = np_image.T
        #np_image = filter_intensity_range(np_image, drop_top_n=200)
        # Enregistrer l'image en TXT (pour debug/archives)
        np_image = self._normalize_for_display(np_image)

        return np_image
    
    @override
    def disconnect(self):
        self.obs.disconnect()
        NIT.NITManager.destroyInstance()
        print(f'Camera {self.camera_type} disconnected')

def create_camera(camera_type: str, camera_sn: str) -> Camera:
    if camera_type == "Simu":
        camera = SimulationCamera(camera_type, camera_sn)
        _set_active_camera(camera)
        print("Camera simu recognized")
        return camera
    
    elif camera_type == "NIT":
        camera = NitCamera(camera_type, camera_sn)
        _set_active_camera(camera)
        print("Camera NIT recognized")
        return camera
    else:
        print("Camera not recognized")
   
    
