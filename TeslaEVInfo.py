#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.logging
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

import requests
import json
import os 
from datetime import date
import time

#import tesla_powerwall
from tesla_powerwall import Powerwall, GridStatus, OperationMode, MeterType
#import tesla_powerwall
from TeslaCloudEVapi import TeslaCloudAPI


class tesla_info:
    def __init__ (self,  ISYname, ISY_Id):
        self.TEST = False

        logging.debug('class tesla_info - init')
        self.TPWcloud = None
        self.cloudEmail = ''
        self.cloudPassword = ''
        self.controllerID = ISY_Id
        self.controllerName = ISYname
        self.ISYCritical = {}
        self.lastDay = date.today()  

        self.systemReady = False 




    def loginCloud(self, email, password ):
        self.cloudEmail = email
        self.cloudPassword = password

        logging.debug('Cloud Access Supported')
        self.TPWcloud = TeslaCloudAPI(self.cloudEmail, self.cloudPassword)
        self.TPWcloudAccess = True
           
    



    def teslaCloudConnect(self ):
        logging.debug('teslaCloudConnect')
        
        if not(self.TPWcloud.teslaCloudConnect()):    
            logging.debug('Error connecting to Tesla Could - check email, password, and API key')
            self.cloudAccessUp=False
            self.TPWcloudAccess = False
        else:
            logging.debug('Logged in Cloud - retrieving data')
            self.TPWcloudAccess = True
            self.TPWcloud.teslaCloudInfo()
            self.TPWcloud.teslaRetrieveCloudData()
            self.solarInstalled = self.TPWcloud.teslaGetSolar()
            self.cloudAccessUp
        return(self.cloudAccessUp)


    def teslaInitializeData(self):
        logging.debug('teslaInitializeData')
     
     
        

    def pollSystemData(self, level):
        logging.debug('PollSystemData - ' + str(level))

        try:
            self.nowDay = date.today() 
                       
            # Get data from the cloud....
            if self.TPWcloudAccess:
                logging.debug('pollSystemData - CLOUD')
                self.cloudAccessUp = self.TPWcloud.teslaUpdateCloudData(level)
                if level == 'all':
                    self.daysTotalSolar = self.TPWcloud.teslaExtractDaysSolar()
                    self.daysTotalConsumption = self.TPWcloud.teslaExtractDaysConsumption()
                    self.daysTotalGeneraton = self.TPWcloud.teslaExtractDaysGeneration()
                    self.daysTotalBattery = self.TPWcloud.teslaExtractDaysBattery()
                    self.daysTotalGrid = self.TPWcloud.teslaExtractDaysGrid()
                    self.daysTotalGenerator = self.TPWcloud.teslaExtractDaysGeneratorUse()
                    self.daysTotalGridServices = self.TPWcloud.teslaExtractDaysGridServicesUse()
                    self.yesterdayTotalSolar = self.TPWcloud.teslaExtractYesteraySolar()
                    self.yesterdayTotalConsumption = self.TPWcloud.teslaExtractYesterdayConsumption()
                    self.yesterdayTotalGeneration  = self.TPWcloud.teslaExtractYesterdayGeneraton()
                    self.yesterdayTotalBattery =  self.TPWcloud.teslaExtractYesterdayBattery() 
                    self.yesterdayTotalGrid =  self.TPWcloud.teslaExtractYesterdayGrid() 
                    self.yesterdayTotalGridServices = self.TPWcloud.teslaExtractYesterdayGridServiceUse()
                    self.yesterdayTotalGenerator = self.TPWcloud.teslaExtractYesterdayGeneratorUse()          

            return True

        except Exception as e:
            logging.error('Exception PollSystemData: '+  str(e))
            logging.error('problems extracting data from tesla power wall')
            # NEED To logout and log back in locally
            # Need to retrieve/renew token from cloud

        
    ''' *****************************************************************

    methods to retrieve data.  pollSystemData() is used to query the
    PW data.  Then use the methods below to access it.  If we have
    local access, then we'll use that data, otherwise we'll use data
    from the cloud.
    '''
    # Need to be imlemented 
    def isNodeServerUp(self):
        logging.debug('isNodeServerUp - called' )
        if self.localAccessUp == True or self.cloudAccessUp == True:
             return(1)
        else:
             return(0) 

    