import json
import os
from tools.singleton import SingletonMeta
from model.data_supplements import VERSION

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
        self.keys_data_list = ["SOFT_VERSION","SN", "OPERATOR_NAME", "DATE"]
        
        self.data_dict = {key: None for key in self.keys_data_list}
        self.sn = ""
    
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
        if os.path.exists(fileName):
            data = JsonHarmonisationData()
            data.load(sn)
            return data
        else:
            return JsonHarmonisationData()
    else:
        return None
        