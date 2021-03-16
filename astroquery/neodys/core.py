
import requests
import pandas as pd
from . import conf

__all__ = ['NEODyS', 'NEODySClass']  


class NEODySClass():
    NEODYS_URL = conf.server
    TIMEOUT = conf.timeout

    def __init__(self):
        super(NEODySClass, self).__init__()

    def query_object(self, Object_ID, OrbitElementType = "Keplerian", Epoch = "Near_Middle"):

        COV = []
        COR = []
        NOR = []

        if OrbitElementType == "Keplerian":
            if Epoch == "Near_Middle":
                Object_url = f'{NEODYS_URL}/{Object_ID}.ke0'
            elif Epoch == "Near_Present":
                Object_url = f'{NEODYS_URL}/{Object_ID}.ke1'
            else:
                print("Epoch must be Near_Middle or Near_Present")
        elif OrbitElementType == "Equinoctial":
            if Epoch == "Near_Middle":
                Object_url = f'https://newton.spacedys.com/~neodys2/epoch//{Object_ID}.eq0'
            elif Epoch == "Near_Present":
                Object_url = f'https://newton.spacedys.com/~neodys2/epoch//{Object_ID}.eq1'
            else:
                print("Epoch must be Near_Middle or Near_Present")
        else:
            print("OrbitElementType must be Keplerian or Equinoctial")
            
        html_out = requests.get(Object_url)
        html_text = (html_out.text).split('\n')

        Results = {}

        for line in html_text:
            if 'KEP' in line:
                Results["KEP"] = [float(x) for x in line.split()[1:]]
            if 'EQU' in line:
                Results["EQU"] = [float(x) for x in line.split()[1:]]
            if 'MJD' in line:
                Results["MJD"] = line.split()[1:]
            if 'MAG' in line:
                Results["MAG"] = [float(x) for x in line.split()[1:]]
            if 'LSP' in line:
                Results["LSP"] = [int(x) for x in line.split()[1:]]
            if 'COV' in line:
                COV.extend([float(x) for x in line.split()[1:]])
            if 'COR' in line:
                COR.extend([float(x) for x in line.split()[1:]])
            if 'NOR' in line:
                NOR.extend([float(x) for x in line.split()[1:]])
        Results["COV"] = COV
        Results["COR"] = COR
        Results["NOR"] = NOR

        return Results



NEODyS = NEODySClass()