'''
Created on Nov 27, 2018

@author: HaiViet
'''
from cx_Freeze import setup, Executable

base = None    

executables = [Executable("__init__.py", base=base)]

packages = ["idna","urllib","bs4","datetime","urllib.request","pandas","xmltodict","os","collections","numpy","sys","re","re"]
options = {
    'build_exe': {    
        'packages':packages,
    },    
}

setup(
    name = "EdgarRun",
    options = options,
    version = "0.1",
    description = 'Run for scrapting data',
    executables = executables
)