import json
import os
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION


# Active harmonisation data accessor (service) : stocke l'instance de données harmonisation créée
_active_harmonisation_data = None

def get_active_harmonisation_data():
    return _active_harmonisation_data

def _set_active_harmonisation_data(data):
    global _active_harmonisation_data
    _active_harmonisation_data = data

class HarmonisationData(metaclass=SingletonMeta):
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
        self.keys_data_list = ["SOFT_VERSION","SN", "OPERATOR_NAME", "DATE",
                               "CUBE_POSITION_X",
                               "CUBE_POSITION_Y",
                               "MIROR_POSITION_X",
                               "MIROR_POSITION_Y",
                               "DISTANCE_CUBE_MIROR_IN_PX",
                               "DIVERGENCE_IN_MRAD",]
        
        self.data_dict = {key: None for key in self.keys_data_list}
        self.sn = ""
        self.cube_position_x = None
        self.cube_position_y = None
        self.miror_position_x = None
        self.miror_position_y = None
        self.distance_cube_miror_in_px = None
        self.divergence_in_mrad = None

    
    def write(self, key:str, value:str):
        self.data_dict[key] = value

    def read(self, key:str) -> str:
        return self.data_dict.get(key)

    def save(self):
        if self.data_dict.get("SN") is not None:
            fileName = f'results\\{self.sn}\\SN{self.data_dict["SN"]}.json'
            with open(fileName, 'w') as fichier:
                json.dump(self.data_dict, fichier,indent=4)

    def load(self,sn:str):
        fileName = f'SN{sn}.json'
        if os.path.exists(fileName):
            with open(fileName, 'r') as fileName:
                self.data_dict = json.load(fileName)

    def append_new_field(self, key:str, value:str):
        self.data_dict = {key: value}
        
    def __str__(self):
        return str(self.data_dict)

def create_harmonisation_data(type_dest:str,sn:str) -> HarmonisationData:
    os.makedirs(f'results\\{sn}', exist_ok=True)
    fileName = f'result\\{sn}\\SN{sn}.json'
    if type_dest.upper() == "JSON": 
        data = JsonHarmonisationData() 
        if os.path.exists(fileName):
            data.load(sn)
        _set_active_harmonisation_data(data)
        return data
    else:
        return None
        