#!/usr/bin/env python3
from ssl import OPENSSL_VERSION_NUMBER
import requests
import time
from requests_oauth2 import OAuth2BearerToken

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

from TeslaCloudApi import teslaCloudApi

class teslaCloudEVapi(object):
    def __init__(self, Rtoken):
        logging.debug('teslaCloudEVapi')
        self.teslaApi = teslaCloudApi(Rtoken)

        self.TESLA_URL = self.teslaApi.TESLA_URL
        self.API = self.teslaApi.API
        self.Header= {'Accept':'application/json'}
        if self.teslaApi.isConnectedToTesla():
            self.connnected = True
        else:
            self.connected = False

        self.carInfo = {}
        self.carBasicInfo = {}

        self.carStateList = ['online', 'offline', 'unknown' ]
        #self.carState = 'unknown'
        self.carState = {}
        self.canActuateTrunks = False
        self.sunroofInstalled = False
        self.readSeatHeat = False
        self.steeringWheeelHeat = False
        self.steeringWheelHeatDetected = False
        self.distUnit = 1

    def isConnectedToEV(self):
       return(self.teslaApi.isConnectedToTesla())

    def getRtoken(self):
        return(self.teslaApi.getRtoken())

    def teslaEV_GetIdList(self ):
        logging.debug('teslaEV_GetVehicleIdList:')
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])  
                r = s.get(self.TESLA_URL + self.API+ '/vehicles', headers=self.Header)         
                if r.ok:                
                    list = r.json()
                    timeStart = int(time.time()*1000)
                    temp = []
                    for id in range(0,len(list['response'])):
                        EVid = list['response'][id]['id']
                        temp.append(EVid)
                        #initialize start time in case car is off line
                        self.carInfo[EVid] ={}
                        self.carInfo[EVid]['vehicle_state'] = {}
                        self.carInfo[EVid]['vehicle_state']['timestamp'] = timeStart
                        self.carInfo[EVid]['climate_state'] = {}
                        self.carInfo[EVid]['climate_state']['timestamp'] = timeStart
                        self.carInfo[EVid]['charge_state'] = {}
                        self.carInfo[EVid]['charge_state']['timestamp'] = timeStart                                                
                        '''
                        r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(list['response'][id]['id_s']), headers=self.Header)
                        if not r.ok:                        
                            time.sleep(30)
                            r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(list['response'][id]['id_s']), headers=self.Header)
                        resp = r.json()
                        logging.debug('teslaEV_GetIdList RETURN: {}'.format(resp))
                        if 'state' in resp: 
                            attempts = 0
                            while resp['response']['state'].lower() != 'online' and attempts < 3:
                                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(list['response'][id]['id_s'])+'/wake_up', headers=self.Header)
                                time.sleep(10)                            
                                attempts = attempts + 1                                                     
                                if r.ok:
                                    r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(list['response'][id]['id_s']), headers=self.Header)
                                    if r.ok:
                                        resp = r.json()                
                        '''
                return (temp)
            except Exception as e:
                logging.debug('Exception teslaEV_GetIdList: ' + str(e))
                logging.error('Error getting vehicle list')
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)


    # Not used until caching works 
    def teslaEV_getLatestCloudInfo(self, EVid):
        logging.debug('teslaEV_getLatestCloudInfo: {}'.format(EVid))
        EV_online_state = self.teslaEV_retrieve_EV_online_status(EVid)
        logging.debug('car {} Status = {}'.format(EVid, EV_online_state))
        cloudInfo = False
        temp = None
        if self.carInfo != None:
            prevTimeStamp = self.teslaEV_GetTimeLastCarUpdate(EVid)        
        S = self.teslaApi.teslaConnect()

        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])        
                if EV_online_state == 'online': 
                    r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/vehicle_data', headers=self.Header)                          
                    #logging.debug('OAuth2BearerToken 1: {} '.format(r))
                    if r.ok:
                        carRaw = r.json()
                        logging.debug('teslaEV_getLatestCloudInfo: {}'.format(carRaw))
                        #self.carInfo[EVid] = self.process_EV_data(carRaw)
                        temp = self.process_EV_data(carRaw)
                        if 'state' in temp: 
                            if temp['state'].lower() == 'online':
                                self.carState[EVid] = 'online'
                            else:
                                self.carState[EVid] = 'offline'
                                #logging.debug( 'carState1 : {}'.format(self.carState[EVid]))
                        elif temp == None:
                            self.carState[EVid] = 'offline'
                elif EV_online_state == 'offline':
                        logging.info('Car appear to be sleeping - trying to retrieve cached data')
                        logging.info('lastest_vehicle_info (cached data) does not seem to be supported with car offline')
                        logging.info('For now - do nothing ')
                        #need to figure out if this call keeps car asleep
                        '''
                        r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/latest_vehicle_data', headers=self.Header)          
                        if r.ok:
                            carRaw = r.json()
                            self.carInfo[EVid]  = self.process_EV_data(carRaw)
                            #logging.debug( 'carInfoCloud1 : {}'.format(carInfoCloud))
                            if self.carInfo[EVid] != None:

                                self.carState[EVid] = 'Sleeping'
                            elif 'state' in self.carInfo[EVid] :
                                if self.carInfo[EVid]['state'].lower() == 'online':
                                    logging.debug('Appears calling for cached data wakes the car')
                                    self.carState[EVid] = 'Online'
                                else:
                                    self.carState[EVid] = 'Sleeping'
                                #logging.debug( 'carState2 : {}'.format(self.carState[EVid]))
                            else:
                                self.carState[EVid] = 'Offline'
                                    #logging.debug( 'carState3 : {}'.format(self.carState[EVid]))
                        else:
                            self.carState[EVid] = 'Unknown'
                            #logging.debug( 'carState4 : {}'.format(self.carState[EVid]))
                            cloudInfo = False
                        '''
                if temp != None:
                    self.carInfo[EVid] = {}
                    self.carInfo[EVid] = temp 
                    if self.teslaEV_GetTimeLastCarUpdate(EVid) == prevTimeStamp:
                        if prevTimeStamp == -1:
                            self.carState[EVid] == 'offline'
                        elif self.carState[EVid] == 'online':
                            self.carState[EVid] = 'Sleeping'
      
                    
                    '''
                    tmp = {}
                    tmp = self.carInfo[EVid]
                    tmp.update(temp)
                    self.carInfo[EVid] = tmp
                    '''
                logging.debug('carinfo - setting state: {} : {}'.format(self.carState[EVid], self.carInfo[EVid]))
                

            except Exception as e:
                logging.debug('Exception teslaEV_getLatestCloudInfo: {}'.format(e))
                logging.error('Error getting data from vehicle id: {}'.format(EVid))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)




    def teslaEV_UpdateCloudInfo(self, EVid):
        logging.debug('teslaEV_UpdateCloudInfo: {}'.format(EVid))
        EV_online_state = self.teslaEV_retrieve_EV_online_status(EVid)
        logging.debug('car {} status = {}'.format(EVid, EV_online_state))
        temp = None
        if self.carInfo != None:
            prevTimeStamp = self.teslaEV_GetTimeLastCarUpdate(EVid)
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                if 'online' == EV_online_state:
                    s.auth = OAuth2BearerToken(S['access_token'])            
                    r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/vehicle_data', headers=self.Header)          
                    #logging.debug('OAuth2BearerToken 1: {} '.format(r))
                    attempts = 0
                    #self.carInfo[EVid] = r.json()
                    #logging.debug('OAuth2BearerToken 2: {} - {} '.format(r, self.carInfo[EVid]))
                    if r.ok:
                        carRaw = r.json()
                        logging.debug('teslaEV_UpdateCloudInfo: {}'.format(carRaw))
                        #self.carInfo[EVid] = self.process_EV_data(carRaw) # handle different formats and remove 'response'
                        temp = self.process_EV_data(carRaw)
                        #logging.debug('self.carInfo[EVid]1 {}'.format(self.carInfo[EVid]))
                        if 'state' in temp: 
                            #logging.debug('if state in self.carInfo[EVid]: ')
                            if temp['state'].lower() == 'online':
                                self.carState[EVid] = 'Online'
                            else:
                                self.carState[EVid] = 'Online'
                            #logging.debug('self.carState[EVid] = Online')
                else:
                    logging.debug('Trying to wake-up car')                                    
                    attempts = 0
                    online = False
                    while attempts < 4 and not online:
                        r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid)+'/wake_up', headers=self.Header)
                        logging.debug('wakeing car: {}'.format(r))
                        if r.ok:
                            carRaw = r.json()
                            #self.carInfo[EVid] = self.process_EV_data(carRaw) # handle different formats and remove 'response'
                            temp = self.process_EV_data(carRaw) 
                            #logging.debug('self.carInfo[EVid]0 {}'.format(self.carInfo[EVid]))
                            #logging.debug('teslaEV_UpdateCloudInfo RETURN: {}'.format(self.carInfo[EVid]))
                            if 'state' in temp:
                                online =  temp['state'].lower() == 'online' 
                                self.carState[EVid] = 'online'
                        else:
                            time.sleep(15) # wait 15 sec and try again
                        attempts = attempts + 1
                        '''
                                attempts = 0
                                while temp['state'].lower() != 'online' and attempts < 6:
                                    time.sleep(10)
                                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid)+'/wake_up', headers=self.Header)
                                    if r.ok:
                                        carRaw = r.json()
                                        #self.carInfo[EVid] = self.process_EV_data(carRaw) # handle different formats and remove 'response'
                                        temp  = self.process_EV_data(carRaw) 
                                        #logging.debug('self.carInfo[EVid]-1 {}'.format(self.carInfo[EVid]))
                                    attempts = attempts + 1
                                if self.carInfo[EVid]['state'].lower() == 'online':
                                    r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/vehicle_data', headers=self.Header)     
                                    if r.ok:
                                        self.carState[EVid] = 'online'
                                        carRaw = r.json()
                                        #self.carInfo[EVid] = self.process_EV_data(carRaw) # handle different formats and remove 'response'                             
                                        temp = self.process_EV_data(carRaw)
                                        #logging.debug('self.carInfo[EVid]-2 {}'.format(self.carInfo[EVid]))
                                else:
                                    self.carState[EVid] = 'offline'
                            elif temp == None:
                                self.carState[EVid] = 'offline'        
                            else:
                                self.carState[EVid] = 'offline'
                        '''
                    if online:
                        self.carState[EVid] = 'online'
                    else:
                        self.carState[EVid] = 'offline'
                if temp != None:
                    #self.carInfo[EVid].update(temp)
                    self.carInfo[EVid] = {}
                    self.carInfo[EVid] = temp
                    if self.teslaEV_GetTimeLastCarUpdate(EVid) == prevTimeStamp:
                        if prevTimeStamp == -1:
                            self.carState[EVid] == 'offline'
                        elif self.carState[EVid] == 'online':
                            self.carState[EVid] = 'Sleeping'
                    '''
                    tmp = {}
                    tmp = self.carInfo[EVid]
                    tmp.update(temp)
                    self.carInfo[EVid] = tmp
                    '''
                logging.debug('teslaEV_UpdateCloudInfo - state {} END - carinfo[{}]:{}'.format(self.carState[EVid], EVid, self.carInfo[EVid] ))

            except Exception as e:
                logging.debug('Exception teslaEV_UpdateCloudInfo: {}'.format(e))
                logging.error('Error getting data from vehicle id: {}'.format(EVid))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                self.carState[EVid] = 'Offline'
                return(None)

    

    def teslaEV_EV_basic_data(self,EVid):
        logging.debug('teslaEV_EV_basic_data: {}'.format(EVid))
        #logging.debug('car {} Online = {}'.format(self.teslaEV_retrieve_EV_online_status(EVid)))
        temp = {}
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])            
                r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid), headers=self.Header)          
                if r.ok:
                    carData = r.json()
                    if EVid not in self.carBasicInfo:
                        self.carBasicInfo[EVid] = {}
                    logging.debug('teslaEV_EV_basic_data carData: {}'.format(carData))
                    temp = self.process_EV_data(carData)
                    logging.debug('after process_EV_data: {}'.format(temp))
                    if temp != None:
                        self.carBasicInfo[EVid] = temp
                    if 'state' in temp:
                        self.carState[EVid] = temp['state']
                    else:
                        self.carState[EVid] = 'offline'
                    logging.debug('teslaEV_EV_basic_data {} data:{}'.format(EVid, self.carBasicInfo[EVid]  ))

            except Exception as e:
                logging.error('Exception teslaEV_EV_basic_data:'.format(e))


    def teslaEV_retrieve_EV_online_status(self, EVid):
        logging.debug('teslaEV_retrieve_EV_online_status: {}'.format(EVid))
        logging.debug('car {} Online = {}'.format(self.teslaEV_retrieve_EV_online_status(EVid)))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])            
                r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid), headers=self.Header)          
                if r.ok:
                    carData = r.json()
                    logging.debug('carData: {}'.format(carData))
                    carStatus = self.process_EV_data(carData)
                    logging.debug('carStatus: {}'.format(carStatus))
                    if carStatus != None:
                        if 'state' in carStatus:
                            logging.debug('Car {} Online {}'.format(EVid, carStatus['state'].lower() ))
                            return( carStatus['state'].lower() )
                        else:
                            return('offline')  
                    else:
                        return('offline')

            except Exception as e:
                logging.error('Exception teslaEV_retrieve_EV_online_status :'.format(e))


    def teslaEV_EV_online_status(self, EVid):
        logging.debug('teslaEV_retrieve_EV_online_status: {}'.format(EVid))
        try:
            return(self.carState[EVid])
        except:
            logging.error('carState not defined for {}'.format(EVid))
            return('unknown')


    #need to decide if this is needed - otherwise simply overwrite existing data in not None
    def update_carInfo(self, updateDict, EVid):
        logging.debug('update_carInfo for {}'.format(EVid))
        logging.debug('updateDict: {}:{}'.format(len(updateDict), updateDict) )
        logging.debug('carInfo before :{}:{}'.format(len(self.carInfo[EVid]), self.carInfo[EVid]))
        try:
            if EVid not in self.carInfo:
                self.carInfo[EVid] = {}

            for idx1 in range(0, len(updateDict)):

                logging.debug('loop1 {} : {} : {}'.format(idx1, updateDict[idx1], self.carInfo[EVid])  )
                if 1 == len(updateDict[idx1]):
                    self.carInfo[EVid][idx1] = updateDict[idx1]
                else:
                    if idx1 not in self.carInfo[EVid]:
                        self.carInfo[EVid][idx1] = {}
                    for idx2 in range (0, len(updateDict[idx1])):
                        logging.debug('loop1 {} : {} : {}'.format(idx2, updateDict[idx1][idx2],self.carInfo[idx1] ) )
                        if 1 == len(updateDict[idx1][idx2]):
                            self.carInfo[EVid][idx1][idx2] = updateDict[idx1][idx2]
                        else: # should not happen
                            if idx2 not in self.carInfo[EVid][idx1]:
                                self.carInfo[EVid][idx1][idx2] = {}
                            for idx3 in range(0, len(updateDict[idx1][idx2])):
                                self.carInfo[EVid][idx1][idx2][idx3] = updateDict[idx1][idx2][idx3]    
            logging.debug('carInfo after :{}'.format(self.carInfo[EVid]))
        except Exception as e:
            logging.error('Exception update_carInfo : {}'.format(e))
            logging.error('updateDict: {}'.format(updateDict) )
            logging.error('carInfo :{}'.format(self.carInfo[EVid]))


    def process_EV_data(self, carData):
        logging.debug('process_EV_data {}'.format(carData))
        if 'response' in carData:
            if 'version' in carData['response']:
                if carData['response']['version'] == 9: # latest release
                    temp = carData['response']['data']
            else:
                temp = carData['response']
        else:
            temp = 'Error'
        logging.debug('process_EV_data: {}'.format(temp))
        return(temp)
            

    def teslaEV_GetCarState(self, EVid):
        logging.debug('teslaEV_GetCarState: {}'.format(self.carState[EVid]))
        return(self.carState[EVid])

    def teslaEV_GetInfo(self, EVid):
        logging.debug('teslaEV_GetInfo {}: {}'.format(EVid, self.carInfo[EVid]))
        return(self.carInfo[EVid])

    def teslaEV_GetBasicInfo(self, EVid):
        logging.debug('teslaEV_GetBasicInfo {}: {}'.format(EVid, self.carBasicInfo[EVid]))
        return(self.carBasicInfo[EVid])



    def teslaEV_GetLocation(self, EVid):
        logging.debug('teslaEV_GetLocation: for {}'.format(EVid))
        temp = {}
        temp['longitude'] = self.carInfo[EVid]['drive_state']['longitude']
        temp['latitide'] = self.carInfo[EVid]['drive_state']['latitide']
        return(temp)


    def teslaEV_SetDistUnit(self, dUnit):
        logging.debug('teslaEV_SetDistUnit: {}'.format(dUnit))
        self.distUnit = dUnit

    def teslaEV_GetDistUnit(self):
        logging.debug('teslaEV_GetDistUnit: {}'.format(self.distUnit))
        return(self.distUnit)

    def teslaEV_SetTempUnit(self, tUnit):
        logging.debug('teslaEV_SetDistUnit: {}'.format(tUnit))
        self.tempUnit = tUnit

    def teslaEV_GetTempUnit(self):
        logging.debug('teslaEV_GetDistUnit: {}'.format(self.distUnit))
        return(self.distUnit)

    def teslaEV_GetTimeLastCarUpdate(self, EVid):
        logging.debug('teslaEV_GetTimeLastCarUpdate')
        timeNow = int(time.time())
        timeMinimum = min( self.teslaEV_GetTimeStampClimateUpdate(EVid),self.teslaEV_GetTimeSinceLastChargeUpdate(EVid), self.teslaEV_GetTimeSinceLastStatusUpdate(EVid) )
        logging.debug('Time Now {} Last Update {}'.format(timeNow, timeMinimum ))
        return(float(timeMinimum))


    def teslaEV_GetTimeSinceLastCarUpdate(self, EVid):
        logging.debug('teslaEV_GetTimeSinceLastCarUpdate')
        timeNow = int(time.time())
        timeMax = max( self.teslaEV_GetTimeSinceLastClimateUpdate(EVid),self.teslaEV_GetTimeStampChargeUpdate(EVid), self.teslaEV_GetTimeStampStatusUpdate(EVid) )
        logging.debug('Time Now {} Last Update {}'.format(timeNow, timeMax ))
        return(float(timeMax))

####################
# Charge Data
####################
    def teslaEV_GetChargingInfo(self, EVid):
        logging.debug('teslaEV_GetChargingInfo: for {}'.format(EVid))
        temp = {}
        if 'charge_state' in self.carInfo[EVid]:
            if 'fast_charger_present' in  self.carInfo[EVid]['charge_state']:
                temp['fast_charger_present'] = self.carInfo[EVid]['charge_state']['fast_charger_present']
            if 'charge_port_latch' in  self.carInfo[EVid]['charge_state']:    
                temp['charge_port_latch'] =  self.carInfo[EVid]['charge_state']['charge_port_latch']
            if 'charge_port_door_open' in  self.carInfo[EVid]['charge_state']: 
                temp['charge_port_door_open'] =  self.carInfo[EVid]['charge_state']['charge_port_door_open']
            if 'battery_range' in  self.carInfo[EVid]['charge_state']: 
                temp['battery_range'] = self.carInfo[EVid]['charge_state']['battery_range']            
            if 'battery_level' in  self.carInfo[EVid]['charge_state']: 
                temp['battery_level'] = self.carInfo[EVid]['charge_state']['battery_level']
            if 'charge_current_request_max' in  self.carInfo[EVid]['charge_state']: 
                temp['charge_current_request_max'] = self.carInfo[EVid]['charge_state']['charge_current_request_max']
            if 'charging_state' in  self.carInfo[EVid]['charge_state']: 
                temp['charging_state'] = self.carInfo[EVid]['charge_state']['charging_state']
            if 'charge_enable_request' in  self.carInfo[EVid]['charge_state']: 
                temp['charge_enable_request'] = self.carInfo[EVid]['charge_state']['charge_enable_request']
            if 'charger_power' in  self.carInfo[EVid]['charge_state']: 
                temp['charger_power'] = self.carInfo[EVid]['charge_state']['charger_power']
            if 'charge_limit_soc' in  self.carInfo[EVid]['charge_state']: 
                temp['charge_limit_soc'] = self.carInfo[EVid]['charge_state']['charge_limit_soc']      
            if 'charge_current_request_max' in  self.carInfo[EVid]['charge_state']: 
                temp['charge_current_request_max'] = self.carInfo[EVid]['charge_state']['charge_current_request_max']      
            if 'charge_current_request' in  self.carInfo[EVid]['charge_state']: 
                temp['charge_current_request'] = self.carInfo[EVid]['charge_state']['charge_current_request']      
            if 'charger_actual_current' in  self.carInfo[EVid]['charge_state']: 
                temp['charger_actual_current'] = self.carInfo[EVid]['charge_state']['charger_actual_current']      
            if 'charge_amps' in  self.carInfo[EVid]['charge_state']: 
                temp['charge_amps'] = self.carInfo[EVid]['charge_state']['charge_amps']      
            if 'time_to_full_charge' in  self.carInfo[EVid]['charge_state']: 
                temp['time_to_full_charge'] = self.carInfo[EVid]['charge_state']['time_to_full_charge']      
            if 'charge_energy_added' in  self.carInfo[EVid]['charge_state']: 
                temp['charge_energy_added'] = self.carInfo[EVid]['charge_state']['charge_energy_added']      
            if 'charge_miles_added_rated' in  self.carInfo[EVid]['charge_state']: 
                temp['charge_miles_added_rated'] = self.carInfo[EVid]['charge_state']['charge_miles_added_rated']      
            if 'charger_voltage' in  self.carInfo[EVid]['charge_state']: 
                temp['charger_voltage'] = self.carInfo[EVid]['charge_state']['charger_voltage']                
            if 'timestamp' in  self.carInfo[EVid]['charge_state']: 
                temp['timestamp'] = int(self.carInfo[EVid]['charge_state']['timestamp'] /1000) # Tesla reports in miliseconds                
        return(temp)

    def teslaEV_GetChargeTimestamp(self, EVid):
        try:
            return(self.carInfo['charge_state']['timestamp'])
        except:
            logging.warning('No data for teslaEV_GetChargeTimestamp')
            return(None)

    def teslaEV_charge_current_request_max(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['charge_current_request_max'],1)) 
        except:
            logging.warning('No data for teslaEV_charge_current_request_max')
            return(None)
    def teslaEV_charge_current_request(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['charge_current_request'],1)) 
        except:
            logging.warning('No data for teslaEV_charge_current_request')
            return(None)
    def teslaEV_charger_actual_current(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['charger_actual_current'],1)) 
        except:
            logging.warning('No data for teslaEV_charger_actual_current')
            return(None)

    def teslaEV_charge_amps(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['charge_amps'],1)) 
        except:
            logging.warning('No data for teslaEV_charge_amps')
            return(None)            

    def teslaEV_time_to_full_charge(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['time_to_full_charge']*60,0)) 
        except:
            logging.warning('No data for teslaEV_time_to_full_charge')
            return(None)            

    def teslaEV_charge_energy_added(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['charge_energy_added'],1)) 
        except:
            logging.warning('No data for teslaEV_charge_energy_added')
            return(None)            

    def teslaEV_charge_miles_added_rated(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['charge_miles_added_rated'],1)) 
        except:
            logging.warning('No data for teslaEV_charge_miles_added_rated')
            return(None)            

    def teslaEV_charger_voltage(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['charger_voltage'],0)) 
        except:
            logging.warning('No data for teslaEV_charger_voltage')
            return(None)            

    def teslaEV_GetTimeStampChargeUpdate(self, EVid):
        try:
            logging.debug('teslaEV_GetTimeStampChargeUpdate {}'.format(int(self.carInfo[EVid]['charge_state']['timestamp']/1000 )))
            return(int(self.carInfo[EVid]['charge_state']['timestamp']/1000))
        except Exception as e:
            logging.error ('teslaEV_GetTimeStampChargeUpdate has no  data :{} '.format(e))
            return(-1) # return negative number to indicate wrong data

    def teslaEV_GetTimeSinceLastChargeUpdate(self, EVid):
        timeNow = int(time.time())
        try:
            logging.debug('Time Now {} Last Update {}'.format(timeNow,self.teslaEV_GetTimeStampChargeUpdate(EVid)))
            return(int(timeNow - float(self.teslaEV_GetTimeStampChargeUpdate(EVid))))


        except Exception as e:
            logging.error ('teslaEV_GetTimeSinceLastChargeUpdate has no  data :{} '.format(e))
            return(-1) # return negative number to indicate wrong data

    def teslaEV_FastChargerPresent(self, EVid):
        logging.debug('teslaEV_FastchargerPresent for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['charge_state']['fast_charger_present'])
        except:
            logging.warning('No data for teslaEV_FastChargerPresent')
            return(None)

  
    def teslaEV_ChargePortOpen(self, EVid):
        logging.debug('teslaEV_ChargePortOpen for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['charge_state']['charge_port_door_open']) 
        except:
            logging.warning('No data for teslaEV_ChargePortOpen')
            return(None) 

    def teslaEV_ChargePortLatched(self, EVid):
        logging.debug('teslaEV_ChargePortOpen for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['charge_state']['charge_port_latch']) 
        except:
            logging.warning('No data for teslaEV_ChargePortLatched')
            return(None)         

    def teslaEV_GetBatteryRange(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['battery_range'],0)) 
        except:
            logging.warning('No data for teslaEV_GetBatteryRange')
            return(None)

    def teslaEV_GetBatteryLevel(self, EVid):
        logging.debug('teslaEV_GetBatteryLevel for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['battery_level'],1)) 
        except:
            logging.warning('No data for teslaEV_GetBatteryLevel')
            return(None)

    def teslaEV_MaxChargeCurrent(self, EVid):
        logging.debug('teslaEV_MaxChargeCurrent for {}'.format(EVid))
        try:
            return( self.carInfo[EVid]['charge_state']['charge_current_request_max'])             
        except:
            logging.warning('No data for teslaEV_MaxChargeCurrent')
            return(None)          

    def teslaEV_ChargeState(self, EVid):
        logging.debug('teslaEV_GetChargingState for {}'.format(EVid))
        try:
            return( self.carInfo[EVid]['charge_state']['charging_state'])  
        except:
            logging.warning('No data for teslaEV_ChargeState')
            return(None)

    def teslaEV_ChargingRequested(self, EVid):
        logging.debug('teslaEV_ChargingRequested for {}'.format(EVid))
        try:
            return(  self.carInfo[EVid]['charge_state']['charge_enable_request'])  
        except:
            logging.warning('No data for teslaEV_ChargingRequested')
            return(None)

    def teslaEV_GetChargingPower(self, EVid):
        logging.debug('teslaEV_GetChargingPower for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['charger_power'],1)) 
        except:
            logging.warning('No data for teslaEV_GetChargingPower')
            return(None)

    def teslaEV_GetBatteryMaxCharge(self, EVid):
        logging.debug('teslaEV_GetBatteryMaxCharge for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['charge_state']['charge_limit_soc'],1)) 
        except:
            logging.warning('No data for teslaEV_GetBatteryMaxCharge')
            return(None)


    def teslaEV_ChargePort(self, EVid, ctrl):
        logging.debug('teslaEV_ChargePort{} for {}'.format(ctrl, EVid))
 
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}      
                if ctrl == 'open':  
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/charge_port_door_open', headers=self.Header, json=payload ) 
                elif ctrl == 'close':
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/charge_port_door_close', headers=self.Header, json=payload ) 
                else:
                    logging.debug('Unknown teslaEV_ChargePort command passed for vehicle id (open, close) {}: {}'.format(EVid, ctrl))
                    return(False)
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_ChargePort for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_Charging(self, EVid, ctrl):
        logging.debug('teslaEV_Charging {} for {}'.format(ctrl, EVid))
 
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}      
                if ctrl == 'start':  
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/charge_start', headers=self.Header, json=payload ) 
                elif ctrl == 'stop':
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/charge_stop', headers=self.Header, json=payload ) 
                else:
                    logging.error('Unknown teslaEV_Charging command passed for vehicle id (start, stop) {}: {}'.format(EVid, ctrl))
                    return(False)
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_AteslaEV_ChargingutoCondition for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SetChargeLimit (self, EVid, limit):
        logging.debug('teslaEV_SetChargeLimit {} for {}'.format(limit, EVid))
       
        if int(limit) > 100 or int(limit) < 0:
            logging.error('Invalid seat heat level passed (0-100%) : {}'.format(limit))
            return(False)
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = { 'percent':int(limit)}    
                s.auth = OAuth2BearerToken(S['access_token'])
                logging.debug('POST: {} {}'.format(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/set_charge_limit', payload ))
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/set_charge_limit', headers=self.Header, json=payload ) 
                logging.debug('teslaEV_SetChargeLimit r :'.format(r))
                temp = r.json()
                logging.debug('teslaEV_SetChargeLimit temp :'.format(temp))
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SetChargeLimit for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)

    def teslaEV_SetChargeLimitAmps (self, EVid, limit):
        logging.debug('teslaEV_SetChargeLimitAmps {} for {} -'.format(limit, EVid))
       
        if limit > 300 or limit < 0:
            logging.error('Invalid seat heat level passed (0-300A) : {}'.format(limit))
            return(False)
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = { 'charging_amps': int(limit)}    
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/set_charging_amps', headers=self.Header, json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SetChargeLimitAmps for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)




####################
# Climate Data
####################


    def teslaEV_GetClimateInfo(self, EVid):
        logging.debug('teslaEV_GetClimateInfo: for {}'.format(EVid))
        temp = {}
        try:
            if 'climate_state' in self.carInfo[EVid]:
                if 'inside_temp' in self.carInfo[EVid]['climate_state']:
                    temp['inside_temp'] = self.carInfo[EVid]['climate_state']['inside_temp']
                if 'outside_temp' in self.carInfo[EVid]['climate_state']:
                    temp['outside_temp'] = self.carInfo[EVid]['climate_state']['outside_temp']
                if 'driver_temp_setting' in self.carInfo[EVid]['climate_state']:
                    temp['driver_temp_setting'] = self.carInfo[EVid]['climate_state']['driver_temp_setting']
                if 'passenger_temp_setting' in self.carInfo[EVid]['climate_state']:
                    temp['passenger_temp_setting'] = self.carInfo[EVid]['climate_state']['passenger_temp_setting']
                if 'seat_heater_left' in self.carInfo[EVid]['climate_state']:
                    temp['seat_heater_left'] = self.carInfo[EVid]['climate_state']['seat_heater_left']
                if 'seat_heater_right' in self.carInfo[EVid]['climate_state']:
                    temp['seat_heater_right'] = self.carInfo[EVid]['climate_state']['seat_heater_right']
                if 'seat_heater_rear_center' in self.carInfo[EVid]['climate_state']:
                    temp['seat_heater_rear_center'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_center']
                if 'seat_heater_rear_left' in self.carInfo[EVid]['climate_state']:
                    temp['seat_heater_rear_left'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_left']
                if 'seat_heater_rear_right' in self.carInfo[EVid]['climate_state']:
                    temp['seat_heater_rear_right'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_right']
                if 'is_auto_conditioning_on' in self.carInfo[EVid]['climate_state']:
                    temp['is_auto_conditioning_on'] = self.carInfo[EVid]['climate_state']['is_auto_conditioning_on']
                if 'is_preconditioning' in self.carInfo[EVid]['climate_state']:
                    temp['is_preconditioning'] = self.carInfo[EVid]['climate_state']['is_preconditioning']
                if 'max_avail_temp' in self.carInfo[EVid]['climate_state']:
                    temp['max_avail_temp'] = self.carInfo[EVid]['climate_state']['max_avail_temp']
                if 'min_avail_temp' in self.carInfo[EVid]['climate_state']:
                    temp['min_avail_temp'] = self.carInfo[EVid]['climate_state']['min_avail_temp']
                if 'timestamp' in  self.carInfo[EVid]['climate_state']: 
                    temp['timestamp'] = int(self.carInfo[EVid]['climate_state']['timestamp'] /1000) # Tesla reports in miliseconds
        
            if 'steering_wheel_heater' in self.carInfo[EVid]['vehicle_state']: 
                self.steeringWheeelHeat = self.carInfo[EVid]['vehicle_state']['steering_wheel_heater']
                self.steeringWheelHeatDetected = True
            return(temp)
        except Exception as e:
            logging.error('Exception -teslaEV_GetClimateInfo: {}'.format(e) )
            
    def teslaEV_GetClimateTimestamp(self, EVid):
        try:
            return(self.carInfo[EVid]['climate_state']['timestamp'])
        except:
            logging.warning('No data for teslaEV_GetClimateTimestamp')
            return(None)

    def teslaEV_GetTimeStampClimateUpdate(self, EVid):
        try:
            logging.debug('teslaEV_GetTimeStampClimateUpdate {}'.format(int(self.carInfo[EVid]['climate_state']['timestamp']/1000 )))
            return(int(self.carInfo[EVid]['climate_state']['timestamp']/1000))
        except Exception as e:
            logging.error ('teslaEV_GetTimeStampClimateUpdate has no  data :{} '.format(e))
            return(-1) # return negative number to indicate wrong data



    def teslaEV_GetTimeSinceLastClimateUpdate(self, EVid):
        timeNow = int(time.time())
        try:
            logging.debug('Time Now {} Last Update {}'.format(timeNow, self.teslaEV_GetTimeStampClimateUpdate(EVid) ))
            return(int(timeNow - float(self.teslaEV_GetTimeStampClimateUpdate(EVid))))
        except Exception as e:
            logging.error ('teslaEV_GetTimeSinceLastClimateUpdate has no  data :{} '.format(e))
            return(-1) # return negative number to indicate wrong data


    def teslaEV_GetCabinTemp(self, EVid):
        logging.debug('teslaEV_GetCabinTemp for {} - {}'.format(EVid, self.carInfo[EVid]['climate_state']['inside_temp'] ))
        try:
            return(round(self.carInfo[EVid]['climate_state']['inside_temp'],1)) 
        except:
            logging.warning('No data for teslaEV_GetCabinTemp')
            return(None)

    def teslaEV_GetOutdoorTemp(self, EVid):
        logging.debug('teslaEV_GetOutdoorTemp for {} = {}'.format(EVid, self.carInfo[EVid]['climate_state']['outside_temp']))
        try:
            return(round(self.carInfo[EVid]['climate_state']['outside_temp'],1)) 
        except:
            logging.warning('No data for teslaEV_GetOutdoorTemp')
            return(None)

    def teslaEV_GetLeftTemp(self, EVid):
        logging.debug('teslaEV_GetLeftTemp for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['climate_state']['driver_temp_setting'],1))   
        except:
            logging.warning('No data for teslaEV_GetLeftTemp')
            return(None)     

    def teslaEV_GetRightTemp(self, EVid):
        logging.debug('teslaEV_GetRightTemp for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['climate_state']['passenger_temp_setting'],1))   
        except:
            logging.warning('No data for teslaEV_GetRightTemp')
            return(None)

    def teslaEV_GetSeatHeating(self, EVid):
        logging.debug('teslaEV_GetSeatHeating for {}'.format(EVid))
        
        temp = {}
        try:
            if 'seat_heater_left' in self.carInfo[EVid]['climate_state']:
                temp['FrontLeft'] = self.carInfo[EVid]['climate_state']['seat_heater_left']
            if 'seat_heater_right' in self.carInfo[EVid]['climate_state']:
                temp['FrontRight'] = self.carInfo[EVid]['climate_state']['seat_heater_right']   
            if 'seat_heater_rear_left' in self.carInfo[EVid]['climate_state']:
                temp['RearLeft'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_left']   
            if 'seat_heater_rear_center' in self.carInfo[EVid]['climate_state']:
                temp['RearMiddle'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_center']           
            if 'seat_heater_rear_right' in self.carInfo[EVid]['climate_state']:
                temp['RearRight'] = self.carInfo[EVid]['climate_state']['seat_heater_rear_right']           
            return(temp)
        except:
            return(temp)

    def teslaEV_AutoConditioningRunning(self, EVid):
        logging.debug('teslaEV_AutoConditioningRunning for {}'.format(EVid))
        try:
            return( self.carInfo[EVid]['climate_state']['is_auto_conditioning_on']) 
        except:
            logging.warning('No data for teslaEV_AutoConditioningRunning')
            return(None)

    def teslaEV_PreConditioningEnabled(self, EVid):
        logging.debug('teslaEV_PreConditioningEnabled for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['climate_state']['is_preconditioning']) 
        except:
            logging.warning('No data for teslaEV_PreConditioningEnabled')
            return(None)
            return(None)

    def teslaEV_MaxCabinTempCtrl(self, EVid):
        logging.debug('teslaEV_MaxCabinTempCtrl for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['climate_state']['max_avail_temp'],1))   
        except:
            logging.warning('No data for teslaEV_MaxCabinTempCtrl')
            return(None)

    def teslaEV_MinCabinTempCtrl(self, EVid):
        logging.debug('teslaEV_MinCabinTempCtrl for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['climate_state']['min_avail_temp'],1))   
        except:
            logging.warning('No data for teslaEV_MinCabinTempCtrl')
            return(None)

    def teslaEV_SteeringWheelHeatOn(self, EVid):
        logging.debug('teslaEV_SteeringWheelHeatOn for {}'.format(EVid))

        return(self.steeringWheeelHeat)  



    def teslaEV_Windows(self, EVid, cmd):
        logging.debug('teslaEV_Windows {} for {}'.format(cmd, EVid))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                if cmd != 'vent' and cmd != 'close':
                    logging.error('Wrong command passed to (vent or close) to teslaEV_Windows: {} '.format(cmd))
                    return(False)
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {'lat':self.carInfo[EVid]['drive_state']['latitude'],
                           'lon':self.carInfo[EVid]['drive_state']['longitude'],
                           'command': cmd}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/window_control', headers=self.Header,  json=payload ) 
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_Windows for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SunRoof(self, EVid, cmd):
        logging.debug('teslaEV_SunRoof {} for {}'.format(cmd, EVid))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                if cmd != 'vent' and cmd != 'close':
                    logging.error('Wrong command passed to (vent or close) to teslaEV_SunRoof: {} '.format(cmd))
                    return(False)
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = { 'state': cmd}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/sun_roof_control',headers=self.Header,  json=payload ) 
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SunRoof for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)
    

    def teslaEV_AutoCondition(self, EVid, ctrl):
        logging.debug('teslaEV_AutoCondition {} for {}'.format(ctrl, EVid))
        
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}      
                if ctrl == 'start':  
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/auto_conditioning_start', headers=self.Header,  json=payload ) 
                elif ctrl == 'stop':
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/auto_conditioning_stop', headers=self.Header,  json=payload ) 
                else:
                    logging.debug('Unknown AutoCondition command passed for vehicle id {}: {}'.format(EVid, ctrl))
                    return(False)
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_AutoCondition for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SetCabinTemps(self, EVid, tempC):
        logging.debug('teslaEV_AutoCondition {} for {}'.format(tempC, EVid))
        
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {'driver_temp' : float(tempC), 'passenger_temp':float(tempC) }      
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/set_temps', headers=self.Header, json=payload ) 
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_AutoCondition for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_DefrostMax(self, EVid, ctrl):
        logging.debug('teslaEV_DefrostMax {}  for {}'.format(ctrl, EVid))
 
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = {}    
                if ctrl == 'on':
                    payload = {'on':True}  
                elif  ctrl == 'off':
                    payload = {'on':False}  
                else:
                    logging.error('Wrong parameter for teslaEV_DefrostMax (on/off) for vehicle id {}: {}'.format(EVid, ctrl))
                    return(False)
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/set_preconditioning_max', headers=self.Header, json=payload ) 
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_AutoCondition for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SetSeatHeating (self, EVid, seat, levelHeat):
        logging.debug('teslaEV_SetSeatHeating {} for {}'.format(levelHeat, EVid))
        seats = {{'frontLeft':0},{'frontRight':1},{'rearLeft':2},{'rearCenter':4},{'rearRight':5} } 
        rearSeats =  {{'rearLeft':2},{'rearCenter':4},{'rearRight':5} } 
        if int(levelHeat) > 3 or int(levelHeat) < 0:
            logging.error('Invalid seat heat level passed (0-3) : {}'.format(levelHeat))
            return(False)
        if seat not in seats: 
            logging.error('Invalid seatpassed (frontLeft, frontRight ,rearLeft, rearCenter, rearRight) : {}'.format(seat))
            return(False)  
        elif not self.rearSeatHeat and seat in rearSeats:
            logging.error('Rear seat heat not supported on this car')
            return (False)  

        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = { 'heater':seats[seat], 'level':int(levelHeat)}    
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/remote_seat_heater_request', headers=self.Header, json=payload ) 
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SetSeatHeating for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SteeringWheelHeat(self, EVid, ctrl):
        logging.debug('teslaEV_SteeringWheelHeat {} for {}'.format(ctrl, EVid))
        if self.steeringWheelHeatDetected:
            S = self.teslaApi.teslaConnect()
            with requests.Session() as s:
                try:
                    payload = {}    
                    if ctrl == 'on':
                        payload = {'on':True}  
                    elif  ctrl == 'off':
                        payload = {'on':False}  
                    else:
                        logging.error('Wrong paralf.carInfo[id]meter for teslaEV_SteeringWheelHeat (on/off) for vehicle id {}: {}'.format(EVid, ctrl))
                        return(False)
                    s.auth = OAuth2BearerToken(S['access_token'])
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/remote_steering_wheel_heater_request', headers=self.Header, json=payload ) 
                    temp = r.json()
                    logging.debug(temp['response']['result'])
                    return(temp['response']['result'])
                except Exception as e:
                    logging.error('Exception teslaEV_SteeringWheelHeat for vehicle id {}: {}'.format(EVid, e))
                    logging.error('Trying to reconnect')
                    self.teslaApi.tesla_refresh_token( )
                    return(False)
        else:
            logging.error('Steering Wheet does not seem to support heating')
            return(False)


####################
# Status Data
####################
    def teslaEV_GetStatusInfo(self, EVid):
        logging.debug('teslaEV_GetStatusInfo: for {} : {}'.format(EVid, self.carInfo[EVid]))
        temp = {}       
        if 'vehicle_state' in self.carInfo[EVid]:            
            if 'center_display_state' in self.carInfo[EVid]['vehicle_state']:
                temp['center_display_state'] = self.carInfo[EVid]['vehicle_state']['center_display_state']
            if 'homelink_device_count' in self.carInfo[EVid]['vehicle_state']:    
                temp['homelink_device_count'] = self.carInfo[EVid]['vehicle_state']['homelink_device_count']
            if 'homelink_nearby' in self.carInfo[EVid]['vehicle_state']:    
                temp['homelink_nearby'] = self.carInfo[EVid]['vehicle_state']['homelink_nearby']
            if 'hfd_window' in self.carInfo[EVid]['vehicle_state']:        
                temp['fd_window'] = self.carInfo[EVid]['vehicle_state']['fd_window']
            if 'fp_window' in self.carInfo[EVid]['vehicle_state']:    
                temp['fp_window'] = self.carInfo[EVid]['vehicle_state']['fp_window']
            if 'rd_window' in self.carInfo[EVid]['vehicle_state']:    
                temp['rd_window'] = self.carInfo[EVid]['vehicle_state']['rd_window']
            if 'rp_window' in self.carInfo[EVid]['vehicle_state']:    
                temp['rp_window'] = self.carInfo[EVid]['vehicle_state']['rp_window']
            if 'ft' in self.carInfo[EVid]['vehicle_state']:    
                temp['frunk'] = self.carInfo[EVid]['vehicle_state']['ft']
            if 'rt' in self.carInfo[EVid]['vehicle_state']:    
                temp['trunk'] = self.carInfo[EVid]['vehicle_state']['rt']
            if 'locked' in self.carInfo[EVid]['vehicle_state']:    
                temp['locked'] = self.carInfo[EVid]['vehicle_state']['locked']
            if 'odometer' in self.carInfo[EVid]['vehicle_state']:    
                temp['odometer'] = self.carInfo[EVid]['vehicle_state']['odometer']
            if 'sun_roof_percent_open' in self.carInfo[EVid]['vehicle_state']:    
                temp['sun_roof_percent_open'] = self.carInfo[EVid]['vehicle_state']['sun_roof_percent_open']
            #if 'sun_roof_state' in self.carInfo[EVid]['vehicle_state']:
            #    temp['sun_roof_state'] = self.carInfo[EVid]['vehicle_state']['sun_roof_state']
            if 'state' in self.carInfo[EVid]['vehicle_state']:    
                temp['state'] = self.carInfo[EVid]['state']
            if 'timestamp' in  self.carInfo[EVid]['vehicle_state']: 
                temp['timestamp'] = int(self.carInfo[EVid]['vehicle_state']['timestamp'] /1000) # Tesla reports in miliseconds
            if 'steering_wheel_heater' in self.carInfo[EVid]['vehicle_state']: 
                self.steeringWheeelHeat = self.carInfo[EVid]['vehicle_state']['steering_wheel_heater']
                self.steeringWheelHeatDetected = True        
        if 'vehicle_config' in self.carInfo[EVid]:
            if 'can_actuate_trunks' in  self.carInfo[EVid]['vehicle_config']: 
                self.canActuateTrunks = self.carInfo[EVid]['vehicle_config']['can_actuate_trunks']    
            if 'sun_roof_installed' in  self.carInfo[EVid]['vehicle_config']: 
                if type(self.carInfo[EVid]['vehicle_config']['sun_roof_installed']) != int:
                    self.sunroofInstalled = False
                else:   
                    self.sunroofInstalled = (self.carInfo[EVid]['vehicle_config']['sun_roof_installed']   > 0)
            if 'rear_seat_heaters' in  self.carInfo[EVid]['vehicle_config']: 
                if type (self.carInfo[EVid]['vehicle_config']['rear_seat_heaters']) !=  int:
                    self.rearSeatHeat = False
                else:
                    self.rearSeatHeat = (self.carInfo[EVid]['vehicle_config']['rear_seat_heaters']   > 0)
        return(temp)
        


    def teslaEV_GetCenterDisplay(self, EVid):
        logging.debug('teslaEV_GetCenterDisplay: for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['vehicle_state']['center_display_state'])
        except:
            logging.warning('No data for teslaEV_GetCenterDisplay')
            return(None)


    def teslaEV_GetStatusTimestamp(self, EVid):
        try:
            return(self.carInfo[EVid]['vehicle_state']['timestamp'])
        except:
            logging.warning('No data for teslaEV_GetStatusTimestamp')
            return(None)

    def teslaEV_GetTimeStampStatusUpdate(self, EVid):
        try:
            logging.debug('teslaEV_GetTimeStampStatusUpdate {}'.format(int(self.carInfo[EVid]['vehicle_state']['timestamp']/1000 )))
            return(int(self.carInfo[EVid]['vehicle_state']['timestamp']/1000))
        except Exception as e:
            logging.warning ('teslaEV_GetTimeStampStatusUpdate has no  data :{} '.format(e))
            return(-1) # return negative number to indicate wrong data


    def teslaEV_GetTimeSinceLastStatusUpdate(self, EVid):
        timeNow = int(time.time())
        try:
            logging.debug('Time Now {} Last Update {}'.format(timeNow,self.teslaEV_GetTimeStampStatusUpdate(EVid)))
            return(int(timeNow - float(self.teslaEV_GetTimeStampStatusUpdate(EVid))))
        except Exception as e:
            logging.warning ('teslaEV_GetTimeSinceLastStatusUpdate has no  data :{} '.format(e))
            return(-1) # return negative number to indicate wrong data

    def teslaEV_HomeLinkNearby(self, EVid):
        logging.debug('teslaEV_HomeLinkNearby: for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['vehicle_state']['homelink_nearby'])
        except:
            logging.warning('No data for teslaEV_HomeLinkNearby')
            return(None)

    def teslaEV_nbrHomeLink(self, EVid):
        try:
            return(self.carInfo[EVid]['vehicle_state']['homelink_device_count'])
        except:
            logging.warning('No data for teslaEV_nbrHomeLink')
            return(None)

    def teslaEV_GetLockState(self, EVid):
        logging.debug('teslaEV_GetLockState: for {}'.format(EVid))
        try:
            return(self.carInfo[EVid]['vehicle_state']['locked'])
        except:
            logging.warning('No data for teslaEV_GetLockState')
            return(None)

    def teslaEV_GetWindowStates(self, EVid):
        logging.debug('teslaEV_GetWindowStates: for {}'.format(EVid))

        temp = {}
        if 'vehicle_state' in self.carInfo[EVid]:
            if 'fd_window' in self.carInfo[EVid]['vehicle_state']:
                temp['FrontLeft'] = self.carInfo[EVid]['vehicle_state']['fd_window']
            else:
                temp['FrontLeft'] = None
            if 'fp_window' in self.carInfo[EVid]['vehicle_state']:
                temp['FrontRight'] = self.carInfo[EVid]['vehicle_state']['fp_window']
            else:
                temp['FrontRight'] = None
            if 'rd_window' in self.carInfo[EVid]['vehicle_state']:
                temp['RearLeft'] = self.carInfo[EVid]['vehicle_state']['rd_window']
            else:
                temp['RearLeft'] = None
            if 'rp_window' in self.carInfo[EVid]['vehicle_state']:
                temp['RearRight'] = self.carInfo[EVid]['vehicle_state']['rp_window']
            else:
                temp['RearRight'] = None
        else:
            logging.warning('No data for teslaEV_GetWindowStates')
            temp['FrontLeft'] = None
            temp['FrontRight'] = None
            temp['RearLeft'] = None
            temp['RearRight'] = None

        return(temp)

    def teslaEV_GetOnlineState(self, EVid):
        logging.debug('teslaEV_GetOnlineState: for {}'.format(EVid))
        return(self.carState[EVid])

    def teslaEV_GetOdometer(self, EVid):
        logging.debug('teslaEV_GetOdometer: for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['vehicle_state']['odometer'], 2))
        except:
            logging.warning('No data for teslaEV_GetOdometer')
            return(0.0)

    def teslaEV_GetSunRoofPercent(self, EVid):
        logging.debug('teslaEV_GetSunRoofState: for {}'.format(EVid))
        try:
            return(round(self.carInfo[EVid]['vehicle_state']['sun_roof_percent_open']))
        except:
            logging.warning('No data for teslaEV_GetSunRoofPercent')
            return(None)

    #def teslaEV_GetSunRoofState(self, EVid):
    #    #logging.debug('teslaEV_GetSunRoofState: for {}'.format(EVid))
    #    if 'sun_roof_state' in self.carInfo[EVid]['vehicle_state'] and self.sunroofInstalled:
    #        return(round(self.carInfo[EVid]['vehicle_state']['sun_roof_state']))
    #    else:
    #        return(99)

    def teslaEV_GetTrunkState(self, EVid):
        try:
            if 'rt' in self.carInfo[EVid]['vehicle_state'] and self.canActuateTrunks:
                if self.carInfo[EVid]['vehicle_state']['rt'] == 0:
                    return(0)
                else:
                    return(1)
        except:
            logging.warning('teslaEV_GetTrunkState')
            return(None)


    def teslaEV_GetFrunkState(self, EVid):
        logging.debug('teslaEV_GetFrunkState: for {}'.format(EVid))
        try:
            if 'ft' in self.carInfo[EVid]['vehicle_state'] and self.canActuateTrunks:
                if self.carInfo[EVid]['vehicle_state']['ft'] == 0:
                    return(0)
                else:
                    return(1)
        except:
            logging.warning('teslaEV_GetFrunkState')
            return(None)     

###############
# Controls
################
    def teslaEV_FlashLights(self, EVid):
        logging.debug('teslaEV_GetVehicleInfo: for {}'.format(EVid))       
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])            
                r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/vehicle_data', headers=self.Header)          
                temp = r.json()
                self.carInfo[EVid] = temp['response']
                return(self.carInfo[EVid])
            except Exception as e:
                logging.error('Exception teslaEV_FlashLight for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)


    def teslaEV_Wake(self, EVid):
        logging.debug('teslaEV_Wake: for {}'.format(EVid))
        S = self.teslaApi.teslaConnect()
        online = False
        attempts = 0 
        MAX_ATTEMPTS = 6 # try for 1 minute max
        with requests.Session() as s:
            try:

                s.auth = OAuth2BearerToken(S['access_token'])            
                while not online and attempts < MAX_ATTEMPTS:
                    attempts = attempts + 1
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/wake_up', headers=self.Header) 
                    temp = r.json()
                    self.online = temp['response'].lower()
                    if self.online == 'online':
                        online = True
                    else:
                        time.sleep(10)
                return(self.online)
            except Exception as e:
                logging.error('Exception teslaEV_Wake for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)


    def teslaEV_HonkHorn(self, EVid):
        logging.debug('teslaEV_HonkHorn for {}'.format(EVid))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/honk_horn',headers=self.Header, json=payload ) 
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_HonkHorn for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_FlashLights(self, EVid):
        logging.debug('teslaEV_FlashLights for {}'.format(EVid))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/flash_lights', headers=self.Header, json=payload ) 
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_FlashLights for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_Doors(self, EVid, ctrl):
        logging.debug('teslaEV_Doors {} for {}'.format(ctrl, EVid))
        
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}      
                if ctrl == 'unlock':  
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/door_unlock', headers=self.Header, json=payload ) 
                elif ctrl == 'lock':
                     r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/door_lock', headers=self.Header,  json=payload ) 
                else:
                    logging.debug('Unknown door control passed: {}'.format(ctrl))
                    return(False)
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_FlashLights for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_TrunkFrunk(self, EVid, frunkTrunk):
        logging.debug('teslaEV_Doors {} for {}'.format(frunkTrunk, EVid))
        
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])
                if frunkTrunk.upper() == 'FRUNK' or frunkTrunk.upper() == 'FRONT':
                    cmd = 'front' 
                elif frunkTrunk.upper()  == 'TRUNK' or frunkTrunk.upper() == 'REAR':
                     cmd = 'rear' 
                else:
                    logging.debug('Unknown trunk command passed: {}'.format(cmd))
                    return(False)
                payload = {'which_trunk':cmd}      
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/actuate_trunk',headers=self.Header,  json=payload ) 
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_TrunkFrunk for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)


    def teslaEV_HomeLink(self, EVid):
        logging.debug('teslaEV_HomeLink for {}'.format(EVid))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {'lat':self.carInfo[EVid]['drive_state']['latitude'],
                           'lon':self.carInfo[EVid]['drive_state']['longitude']}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/command/trigger_homelink', headers=self.Header, json=payload ) 
                temp = r.json()
                logging.debug(temp['response']['result'])
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_HomeLink for vehicle id {}: {}'.format(EVid, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)

    
   