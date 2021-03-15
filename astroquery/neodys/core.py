
import requests
import pandas as pd

class NEODySClass():

    def __init__(self):
        super(NEODySClass, self).__init__()

    def query_object(self, Object_ID, OrbitElementType = "Keplerian", Epoch = "Near_Middle"):

        COV = []
        COR = []
        NOR = []

        if OrbitElementType == "Keplerian":
            if Epoch == "Near_Middle":
                NEODyS_url = f'https://newton.spacedys.com/~neodys2/epoch//{Object_ID}.ke0'
                print(NEODyS_url)
            elif Epoch == "Near_Present":
                NEODyS_url = f'https://newton.spacedys.com/~neodys2/epoch//{Object_ID}.ke1'
                print(NEODyS_url)
            else:
                print("Epoch must be Near_Middle or Near_Present")
        elif OrbitElementType == "Equinoctial":
            if Epoch == "Near_Middle":
                NEODyS_url = f'https://newton.spacedys.com/~neodys2/epoch//{Object_ID}.eq0'
                print(NEODyS_url)
            elif Epoch == "Near_Present":
                NEODyS_url = f'https://newton.spacedys.com/~neodys2/epoch//{Object_ID}.eq1'
                print(NEODyS_url)
            else:
                print("Epoch must be Near_Middle or Near_Present")
        else:
            print("OrbitElementType must be Keplerian or Equinoctial")
            
        html_out = requests.get(NEODyS_url)
        html_text = (html_out.text).split('\n')

        for line in html_text:
            if 'KEP' in line:
                KEP = [float(x) for x in line.split()[1:]]
            if 'EQU' in line:
                EQU = [float(x) for x in line.split()[1:]]
            if 'MJD' in line:
                MJD = line.split()[1:]
            if 'MAG' in line:
                MAG = [float(x) for x in line.split()[1:]]
            if 'LSP' in line:
                LSP = [int(x) for x in line.split()[1:]]
            if 'COV' in line:
                COV.extend([float(x) for x in line.split()[1:]])
            if 'COR' in line:
                COR.extend([float(x) for x in line.split()[1:]])
            if 'NOR' in line:
                NOR.extend([float(x) for x in line.split()[1:]])
        
        print("Time = " + str(MJD))
        print("MAG = " + str(MAG))
        print("LSP = " + str(LSP))
        print("COV = " + str(COV))
        if OrbitElementType == "Keplerian":
            print("KEP = " + str(KEP))
            print("COR = " + str(COR))
        if OrbitElementType == "Equinoctial":
            print("EQU = " + str(EQU))
            print("NOR = " + str(NOR))

        return 