#!/usr/bin/env python3

#from TeslaCloudApi import teslaCloudApi

import json
import ast

def process_EV_data( carInfo):
    #logging.debug('process_EV_data')
    if 'version' in carInfo:
        if carInfo['version'] == 9: # latest release
            temp = carInfo['legacy']
    else:
        temp = carInfo
    return(temp)


dataFile = open('./newData.json', 'r')
temp = dataFile.read()

dataFile.close()
newData = ast.literal_eval(temp)



dataFile = open('./oldData.json', 'r')
temp = dataFile.read()
dataFile.close()
oldData =ast.literal_eval(temp)




data1 = process_EV_data(newData['3744498271591036'])
data2 = process_EV_data(oldData['3744498271591036'])
print()