import os
import pickle
import subprocess
import numpy as np
from PIL import Image
from yacs.config import CfgNode as CN

class Submodule:
    
    def __init__(self):
        self.data_dict = {}
    
    def transform(self, data, type=None):
        if type is None:
            if isinstance(data, np.ndarray):
                return data.tolist()
            elif isinstance(data, CN):
                return data.to_dict()
            elif isinstance(data, Image.Image):
                return pickle.dumps(data)
            else:
                return data
        else:
            if type == np.ndarray:
                return np.array(data)
            elif type == CN:
                return CN().from_dict(data)
            elif type == Image.Image:
                return pickle.loads(data)
            else:
                return data
            
    def add(self, name, data):
        self.data_dict[name] = self.transform(data)
    
    def get(self, name, type=None):
        return self.transform(self.data_dict[name], type)
    
    def clear(self):
        self.data_dict.clear()
    
    def serialize(self):
        return pickle.dumps(self.data_dict)
        
    def deserialize(self, data):
        self.data_dict = pickle.loads(data)
        
    def call(self, env_name, script_path):     
        print(f"[Submodule call] \033[34mInfo\033[0m: Start run submodule {script_path} in {env_name}")
        # input_data = pickle.dumps(input_data)
        input_data = self.serialize()
        script_path = os.path.join('..', script_path)
        result = subprocess.run(
            ['conda', 'run', '--no-capture-output', '-n', env_name, 'python', script_path],
            input=input_data,
            capture_output=True
        )
        if result.returncode != 0:
            print(f"[Submodule call] \033[31merror\033[0m: Error occurred: {result.stderr.decode()}")
        # result = pickle.loads(result.stdout)
        self.deserialize(result.stdout)
        print(f"[Submodule call] \033[34mInfo\033[0m: End run submodule {script_path} in {env_name}!")
        # return result
    