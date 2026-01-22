import json
import os
from tools.singleton import SingletonMeta
from model.data_supplements import XDIM, YDIM
import numpy as np

# Active harmonisation data accessor (service) : stocke l'instance de données harmonisation créée
_active_harmonisation_data = None

def get_active_harmonisation_data():
    return _active_harmonisation_data

def _set_active_harmonisation_data(data):
    global _active_harmonisation_data
    _active_harmonisation_data = data

class HarmonisationData(metaclass=SingletonMeta):
    def __init__(self):
        self.fileName = ""
        self.working_dir = ""

    def write(self, key:str, value:str):
        pass

    def read(self, key:str) -> str:
        pass

    def save(self):
       pass

    def load(self):
        pass

    def append_new_field(self, key:str, value:str):
        pass
    
    def __str__(self):
        pass

class JsonHarmonisationData(HarmonisationData) :
    def __init__(self):
        self.keys_data_list = ["SOFT_VERSION","SN", "OPERATOR_NAME", "DATE", "PIXEL_SIZE_IN_M", "FOCAL_LENGTH_IN_M",
                               "CUBE_POSITION_X_EMISSION",
                               "CUBE_POSITION_Y_EMISSION",
                               "CUBE_POSITION_X_RECEPTION",
                               "CUBE_POSITION_Y_RECEPTION",
                               "MIROR_POSITION_X_EMISSION",
                               "MIROR_POSITION_Y_EMISSION",
                               "MIROR_POSITION_X_RECEPTION",
                               "MIROR_POSITION_Y_RECEPTION",
                               "DISTANCE_CUBE_MIROR_IN_PX_EMISSION",
                               "DISTANCE_CUBE_MIROR_IN_PX_RECEPTION",
                               "DIVERGENCE_IN_MRAD",
                               "EMISSION_WEDGE_WIDTH_IN_MM",
                               "LASER_POSITION_X_EMISSION",
                               "LASER_POSITION_Y_EMISSION",
                               "DISTANCE_CUBE_LASER_IN_PX_EMISSION",
                               "LASER_POSITION_X_RECEPTION",
                               "LASER_POSITION_Y_RECEPTION",
                               "DISTANCE_CUBE_LASER_IN_PX_RECEPTION",
                               "RECEPTION_WEDGE_WIDTH_IN_MM"
                               "APD_POSITION_UP_X",
                               "APD_POSITION_UP_Y",
                               "APD_POSITION_DOWN_X",
                               "APD_POSITION_DOWN_Y",
                               "APD_POSITION_LEFT_X",
                               "APD_POSITION_LEFT_Y"
                               "APD_POSITION_RIGHT_X",
                               "APD_POSITION_RIGHT_Y",
                               "DISTANCE_LASER_APD_IN_PX"
                               ]

        self.data_dict = {key: None for key in self.keys_data_list}
        self.sn = ""
        self.cube_position_x = None
        self.cube_position_y = None
        self.miror_position_x = None
        self.miror_position_y = None
        self.distance_cube_miror_in_px = None
        self.divergence_in_mrad = None
        self.wedge_width_list_in_mm = []
        self.divergence_list_in_mrad = []
        self.emission_final_wedge_width_in_mm = None
        self.laser_position_x = None
        self.laser_position_y = None
        self.distance_cube_laser_in_px = None
        self.step = None
        self.recetion_final_wedge_width_in_mm = None
        self.background_image = np.zeros((YDIM,XDIM), dtype=np.uint8)  # Placeholder for background image
        self.apd_position_up_x = None
        self.apd_position_up_y = None
        self.apd_position_down_x = None
        self.apd_position_down_y = None
        self.apd_position_left_x = None
        self.apd_position_left_y = None
        self.apd_position_right_x = None
        self.apd_position_right_y = None
        self.distance_laser_apd_in_px = None

    def write(self, key:str, value:str):
        self.data_dict[key] = value

    def read(self, key:str) -> str:
        return self.data_dict.get(key)

    def save(self):
        if self.data_dict.get("SN") is not None:
            with open(self.fileName, 'w') as fichier:
                json.dump(self.data_dict, fichier,indent=4)

    def load(self,sn:str):
        self.fileName = f'SN{sn}.json'
        if os.path.exists(self.fileName):
            with open(self.fileName, 'r') as self.fileName:
                self.data_dict = json.load(self.fileName)

    def append_new_field(self, key:str, value:str):
        self.data_dict = {key: value}
        
    def __str__(self):
        return str(self.data_dict)

def create_harmonisation_data(type_dest:str,sn:str,step:str) -> HarmonisationData:
    #TODO créer un dossier SN_v{i} pour y associer les resultats
    os.makedirs(f'results\\{sn}\\{step}', exist_ok=True)
    for i in range(1,100,1):
        path = f'results\\{sn}\\{step}\\SN{sn}_v{i}'
        if os.path.isdir(path):
            continue
        else:
            os.makedirs(path, exist_ok=True)
            break

    if type_dest.upper() == "JSON": 
        data = JsonHarmonisationData() 
        data.working_dir = path
        data.fileName = f'{path}\\SN{sn}.json'
        data.sn = sn
        data.step = step
        _set_active_harmonisation_data(data)
        return data
    else:
        return None
        