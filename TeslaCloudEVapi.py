#!/usr/bin/env python3
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
        self.carInfo = None
        if self.teslaApi.isConnectedToTesla():
            self.connnected = True
        else:
            self.connected = False

        self.carInfo = {}
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
                list = r.json()
                temp = []
                for id in range(0,len(list['response'])):
                    temp.append(list['response'][id]['id_s'])
                    r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(list['response'][id]['id_s']), headers=self.Header)
                    if not r.ok:                        
                        time.sleep(30)
                        r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(list['response'][id]['id_s']), headers=self.Header)
                    resp = r.json()
                    logging.debug('teslaEV_GetIdList RETURN: {}'.format(resp))
                    if 'state' in resp: 
                        attempts = 0
                        while resp['response']['state'] != 'online' and attempts < 3:
                            r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(list['response'][id]['id_s'])+'/wake_up', headers=self.Header)
                            time.sleep(10)                            
                            attempts = attempts + 1
                            r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(list['response'][id]['id_s']), headers=self.Header)
                            resp = r.json()
                return (temp)
            except Exception as e:
                logging.debug('Exception teslaEV_GetVehicleIdList: ' + str(e))
                logging.error('Error getting vehicle list')
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)

    
    def teslaEV_getLatestCloudInfo(self, EVid):
        logging.debug('teslaEV_getLatestCloudInfo: {}'.format(EVid))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])            
                r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/latest_vehicle_data', headers=self.Header)          
                carInfo = r.json()
                logging.debug('teslaEV_getLatestCloudInfo RETURN: {}'.format(carInfo))
                if 'response' in carInfo:
                    self.carInfo = self.process_EV_data(carInfo['response'])
                logging.debug('carinfo : {}'.format(self.carInfo))

            except Exception as e:
                logging.debug('Exception teslaGetSiteInfo: {}'.format(e))
                logging.error('Error getting data from vehicle id: {}'.format(EVid))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)


    def teslaEV_UpdateCloudInfo(self, EVid):
            #if self.connectionEstablished:
        logging.debug('teslaEV_UpdateCloudInfo: {}'.format(EVid))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])            
                r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/vehicle_data', headers=self.Header)          
                logging.debug('OAuth2BearerToken 1: {} '.format(r))
                attempts = 0
                carInfo = r.json()
                logging.debug('OAuth2BearerToken 2: {} - {} '.format(r, carInfo))
                if not r.ok:
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid)+'/wake_up', headers=self.Header)
                    if r.ok:
                        onlineInfo = r.json()
                        logging.debug('teslaEV_UpdateCloudInfo RETRUN: {}'.format(onlineInfo))
                        if 'state ' in onlineInfo['response']: 
                            attempts = 0
                            while onlineInfo['response']['state'] != 'online' and attempts < 3:
                                time.sleep(10)
                                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid)+'/wake_up', headers=self.Header)
                                onlineInfo = r.json()
                                attempts = attempts + 1
                            r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(EVid) +'/vehicle_data', headers=self.Header)     

                carInfo = r.json()

                if 'response' in carInfo:
                    #self.process_EV_data(carInfo['response'])
                    self.carInfo = self.process_EV_data(carInfo['response'])
                logging.debug('carinfo : {}'.format(self.carInfo))
                #return()
            except Exception as e:
                logging.debug('Exception teslaGetSiteInfo: {}'.format(e))
                logging.error('Error getting data from vehicle id: {}'.format(EVid))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)

    def process_EV_data(self, carInfo):
        logging.debug('process_EV_data')
        if 'version' in carInfo:
            if carInfo['version'] == 9: # latest release
                temp = carInfo['legacy']
        else:
            temp = carInfo
        return(temp)
            


    def teslaEV_GetInfo(self, EVid):
        #if self.connectionEstablished:
        #maxAttempts = 3
        #attempts = 0
        #while maxAttempts > attempts and self.carInfo == None:
        #    attempts = attempts + 1
        #    time.sleep(1)
        logging.debug('teslaEV_GetInfo: {}'.format(self.carInfo))
        return(self.carInfo)


    def teslaEV_GetLocation(self, EVid):
        logging.debug('teslaEV_GetLocation: for {}'.format(EVid))
        temp = {}
        temp['longitude'] = self.carInfo['drive_state']['longitude']
        temp['latitide'] = self.carInfo['drive_state']['latitide']
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


####################
# Charge Data
####################
    def teslaEV_GetChargingInfo(self, id):
        logging.debug('teslaEV_GetChargingInfo: for {}'.format(id))
        temp = {}
        if 'fast_charger_present' in  self.carInfo['charge_state']:
            temp['fast_charger_present'] = self.carInfo['charge_state']['fast_charger_present']
        if 'charge_port_latch' in  self.carInfo['charge_state']:    
            temp['charge_port_latch'] =  self.carInfo['charge_state']['charge_port_latch']
        if 'charge_port_door_open' in  self.carInfo['charge_state']: 
            temp['charge_port_door_open'] =  self.carInfo['charge_state']['charge_port_door_open']
        if 'est_battery_range' in  self.carInfo['charge_state']: 
            temp['est_battery_range'] = self.carInfo['charge_state']['est_battery_range']            
        if 'battery_level' in  self.carInfo['charge_state']: 
            temp['battery_level'] = self.carInfo['charge_state']['battery_level']
        if 'charge_current_request_max' in  self.carInfo['charge_state']: 
            temp['charge_current_request_max'] = self.carInfo['charge_state']['charge_current_request_max']
        if 'est_battery_range' in  self.carInfo['charge_state']: 
            temp['est_battery_range'] = self.carInfo['charge_state']['est_battery_range']
        if 'charging_state' in  self.carInfo['charge_state']: 
            temp['charging_state'] = self.carInfo['charge_state']['charging_state']
        if 'charge_enable_request' in  self.carInfo['charge_state']: 
            temp['charge_enable_request'] = self.carInfo['charge_state']['charge_enable_request']
        if 'charger_power' in  self.carInfo['charge_state']: 
            temp['charger_power'] = self.carInfo['charge_state']['charger_power']
        if 'charge_limit_soc' in  self.carInfo['charge_state']: 
            temp['charge_limit_soc'] = self.carInfo['charge_state']['charge_limit_soc']      
        if 'charge_current_request_max' in  self.carInfo['charge_state']: 
            temp['charge_current_request_max'] = self.carInfo['charge_state']['charge_current_request_max']      
        if 'charge_current_request' in  self.carInfo['charge_state']: 
            temp['charge_current_request'] = self.carInfo['charge_state']['charge_current_request']      
        if 'charger_actual_current' in  self.carInfo['charge_state']: 
            temp['charger_actual_current'] = self.carInfo['charge_state']['charger_actual_current']      
        if 'charge_amps' in  self.carInfo['charge_state']: 
            temp['charge_amps'] = self.carInfo['charge_state']['charge_amps']      
        if 'time_to_full_charge' in  self.carInfo['charge_state']: 
            temp['time_to_full_charge'] = self.carInfo['charge_state']['time_to_full_charge']      
        if 'charge_energy_added' in  self.carInfo['charge_state']: 
            temp['charge_energy_added'] = self.carInfo['charge_state']['charge_energy_added']      
        if 'charge_miles_added_rated' in  self.carInfo['charge_state']: 
            temp['charge_miles_added_rated'] = self.carInfo['charge_state']['charge_miles_added_rated']      
        if 'charger_voltage' in  self.carInfo['charge_state']: 
            temp['charger_voltage'] = self.carInfo['charge_state']['charger_voltage']                
        if 'timestamp' in  self.carInfo['charge_state']: 
            temp['timestamp'] = int(self.carInfo['charge_state']['timestamp'] /1000) # Tesla reports in miliseconds                
        return(temp)

    def teslaEV_GetChargeTimestamp(self,id):
        if 'timestamp' in self.carInfo['charge_state']:
            return(self.carInfo['charge_state']['timestamp'])
        else:
            return(None)

    def teslaEV_charge_current_request_max(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'charge_current_request_max' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['charge_current_request_max'],1)) 
        else:
            return(None)
    def teslaEV_charge_current_request(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'charge_current_request' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['charge_current_request'],1)) 
        else:
            return(None)
    def teslaEV_charger_actual_current(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'charger_actual_current' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['charger_actual_current'],1)) 
        else:
            return(None)
    def teslaEV_charge_amps(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'charge_amps' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['charge_amps'],1)) 
        else:
            return(None)            
    def teslaEV_time_to_full_charge(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'time_to_full_charge' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['time_to_full_charge'],0)) 
        else:
            return(None)            

    def teslaEV_charge_energy_added(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'charge_energy_added' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['charge_energy_added'],1)) 
        else:
            return(None)            

    def teslaEV_charge_miles_added_rated(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'time_to_full_charge' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['charge_miles_added_rated'],1)) 
        else:
            return(None)            

    def teslaEV_charger_voltage(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'charger_voltage' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['charger_voltage'],0)) 
        else:
            return(None)            

    def teslaEV_GetTimeSinceLastChargeUpdate(self, id):
        timeNow = int(time.time())
        logging.debug('Time Now {} Last UPdate {}'.format(timeNow,self.carInfo['charge_state']['timestamp']/1000 ))
        return(int(timeNow - float(self.carInfo['charge_state']['timestamp']/1000)))

    def teslaEV_FastChargerPresent(self, id):
        #logging.debug('teslaEV_FastchargerPresent for {}'.format(id))
        if 'fast_charger_present' in self.carInfo['charge_state']:
            return(self.carInfo['charge_state']['fast_charger_present'])
        else:
            return(None)

  
    def teslaEV_ChargePortOpen(self, id):
        #logging.debug('teslaEV_ChargePortOpen for {}'.format(id))
        if 'charge_port_door_open' in self.carInfo['charge_state']:
            return(self.carInfo['charge_state']['charge_port_door_open']) 
        else:
            return(None) 

    def teslaEV_ChargePortLatched(self, id):
        #logging.debug('teslaEV_ChargePortOpen for {}'.format(id))
        if 'charge_port_latch' in self.carInfo['charge_state']:
            return(self.carInfo['charge_state']['charge_port_latch']) 
        else:
            return(None)         

    def teslaEV_GetBatteryRange(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'est_battery_range' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['est_battery_range'],0)) 
        else:
            return(None)

    def teslaEV_GetBatteryLevel(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        if 'battery_level' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['battery_level'],1)) 
        else:
            return(None)

    def teslaEV_MaxChargeCurrent(self, id):
        #logging.debug('teslaEV_MaxChargeCurrent for {}'.format(id))
        if 'charge_current_request_max' in self.carInfo['charge_state']:
            return( self.carInfo['charge_state']['charge_current_request_max'])             
        else:
            return(None)          

    def teslaEV_ChargeState(self, id):
        #logging.debug('teslaEV_GetChargingState for {}'.format(id))
        if 'charging_state' in self.carInfo['charge_state']:
            return( self.carInfo['charge_state']['charging_state'])  
        else:
            return(None)

    def teslaEV_ChargingRequested(self, id):
        #logging.debug('teslaEV_ChargingRequested for {}'.format(id))
        if 'charge_enable_request' in self.carInfo['charge_state']:
            return(  self.carInfo['charge_state']['charge_enable_request'])  
        else:
            return(None)

    def teslaEV_GetChargingPower(self, id):
        #logging.debug('teslaEV_GetChargingPower for {}'.format(id))
        if 'charger_power' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['charger_power'],1)) 
        else:
            return(None)

    def teslaEV_GetBatteryMaxCharge(self, id):
        #logging.debug('teslaEV_GetBatteryMaxCharge for {}'.format(id))
        if 'charge_limit_soc' in self.carInfo['charge_state']:
            return(round(self.carInfo['charge_state']['charge_limit_soc'],1)) 
        else:
            return(None)


    def teslaEV_ChargePort(self, id, ctrl):
        logging.debug('teslaEV_ChargePort for {}'.format(id))
 
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}      
                if ctrl == 'open':  
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/charge_port_door_open', headers=self.Header, json=payload ) 
                elif ctrl == 'close':
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/charge_port_door_close', headers=self.Header, json=payload ) 
                else:
                    logging.debug('Unknown teslaEV_ChargePort command passed for vehicle id (open, close) {}: {}'.format(id, ctrl))
                    return(False)
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_ChargePort for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_Charging(self, id, ctrl):
        logging.debug('teslaEV_Charging for {}'.format(id))
 
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}      
                if ctrl == 'start':  
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/charge_start', headers=self.Header, json=payload ) 
                elif ctrl == 'stop':
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/charge_stop', headers=self.Header, json=payload ) 
                else:
                    logging.debug('Unknown teslaEV_Charging command passed for vehicle id (start, stop) {}: {}'.format(id, ctrl))
                    return(False)
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_AteslaEV_ChargingutoCondition for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SetChargeLimit (self, id, limit):
        logging.debug('teslaEV_SetChargeLimit for {}'.format(id))
       
        if float(limit) > 100 or float(limit) < 0:
            logging.error('Invalid seat heat level passed (0-100%) : {}'.format(limit))
            return(False)
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = { 'percent':limit}    
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/set_charge_limit', headers=self.Header, json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SetChargeLimit for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)

    def teslaEV_SetChargeLimitAmps (self, id, limit):
        logging.debug('teslaEV_SetChargeLimitAmps for {}'.format(id))
       
        if limit > 300 or limit < 0:
            logging.error('Invalid seat heat level passed (0-300A) : {}'.format(limit))
            return(False)
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = { 'charging_amps': int(limit)}    
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/set_charging_amps', headers=self.Header, json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SetChargeLimitAmps for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)




####################
# Climate Data
####################


    def teslaEV_GetClimateInfo(self, id):
        logging.debug('teslaEV_GetClimateInfo: for {}'.format(id))
        temp = {}
        if 'climate_state' in self.carInfo:
            if 'inside_temp' in self.carInfo['climate_state']:
                temp['inside_temp'] = self.carInfo['climate_state']['inside_temp']
            if 'outside_temp' in self.carInfo['climate_state']:
                temp['outside_temp'] = self.carInfo['climate_state']['outside_temp']
            if 'idriver_temp_setting' in self.carInfo['climate_state']:
                temp['driver_temp_setting'] = self.carInfo['climate_state']['driver_temp_setting']
            if 'passenger_temp_setting' in self.carInfo['climate_state']:
                temp['passenger_temp_setting'] = self.carInfo['climate_state']['passenger_temp_setting']
            if 'seat_heater_left' in self.carInfo['climate_state']:
                temp['seat_heater_left'] = self.carInfo['climate_state']['seat_heater_left']
            if 'seat_heater_right' in self.carInfo['climate_state']:
                temp['seat_heater_right'] = self.carInfo['climate_state']['seat_heater_right']
            if 'seat_heater_rear_center' in self.carInfo['climate_state']:
                temp['seat_heater_rear_center'] = self.carInfo['climate_state']['seat_heater_rear_center']
            if 'seat_heater_rear_left' in self.carInfo['climate_state']:
                temp['seat_heater_rear_left'] = self.carInfo['climate_state']['seat_heater_rear_left']
            if 'seat_heater_rear_right' in self.carInfo['climate_state']:
                temp['seat_heater_rear_right'] = self.carInfo['climate_state']['seat_heater_rear_right']
            if 'is_auto_conditioning_on' in self.carInfo['climate_state']:
                temp['is_auto_conditioning_on'] = self.carInfo['climate_state']['is_auto_conditioning_on']
            if 'is_preconditioning' in self.carInfo['climate_state']:
                temp['is_preconditioning'] = self.carInfo['climate_state']['is_preconditioning']
            if 'max_avail_temp' in self.carInfo['climate_state']:
                temp['max_avail_temp'] = self.carInfo['climate_state']['max_avail_temp']
            if 'min_avail_temp' in self.carInfo['climate_state']:
                temp['min_avail_temp'] = self.carInfo['climate_state']['min_avail_temp']
            if 'timestamp' in  self.carInfo['climate_state']: 
                temp['timestamp'] = int(self.carInfo['climate_state']['timestamp'] /1000) # Tesla reports in miliseconds
        if 'steering_wheel_heater' in self.carInfo['vehicle_state']: 
            self.steeringWheeelHeat = self.carInfo['vehicle_state']['steering_wheel_heater']
            self.steeringWheelHeatDetected = True


    def teslaEV_GetClimateTimestamp(self,id):
        if 'timestamp' in self.carInfo['climate_state']:
            return(self.carInfo['climate_state']['timestamp'])
        else:
            return(None)

    def teslaEV_GetTimeSinceLastClimateUpdate(self, id):
        timeNow = int(time.time())
        logging.debug('Time Now {} Last UPdate {}'.format(timeNow,self.carInfo['climate_state']['timestamp']/1000 ))

        return(int(timeNow - float(self.carInfo['climate_state']['timestamp']/1000)))


    def teslaEV_GetCabinTemp(self, id):
        logging.debug('teslaEV_GetCabinTemp for {} - {}'.format(id, self.carInfo['climate_state']['inside_temp'] ))
        if 'inside_temp' in self.carInfo['climate_state']:
            return(round(self.carInfo['climate_state']['inside_temp'],1)) 
        else:
            return(None)

    def teslaEV_GetOutdoorTemp(self, id):
        logging.debug('teslaEV_GetOutdoorTemp for {} = {}'.format(id, self.carInfo['climate_state']['outside_temp']))
        if 'outside_temp' in self.carInfo['climate_state']:
            return(round(self.carInfo['climate_state']['outside_temp'],1)) 
        else:
            return(None)

    def teslaEV_GetLeftTemp(self, id):
        #logging.debug('teslaEV_GetLeftTemp for {}'.format(id))
        if 'driver_temp_setting' in self.carInfo['climate_state']:
            return(round(self.carInfo['climate_state']['driver_temp_setting'],1))   
        else:
            return(None)     

    def teslaEV_GetRightTemp(self, id):
        #logging.debug('teslaEV_GetRightTemp for {}'.format(id))
        if 'passenger_temp_setting' in self.carInfo['climate_state']:
            return(round(self.carInfo['climate_state']['passenger_temp_setting'],1))   
        else:
            return(None)

    def teslaEV_GetSeatHeating(self, id):
        #logging.debug('teslaEV_GetSeatHeating for {}'.format(id))
        temp = {}
        if 'seat_heater_left' in self.carInfo['climate_state']:
            temp['FrontLeft'] = self.carInfo['climate_state']['seat_heater_left']
        if 'seat_heater_right' in self.carInfo['climate_state']:
            temp['FrontRight'] = self.carInfo['climate_state']['seat_heater_right']   
        if 'seat_heater_rear_left' in self.carInfo['climate_state']:
            temp['RearLeft'] = self.carInfo['climate_state']['seat_heater_rear_left']   
        if 'seat_heater_rear_center' in self.carInfo['climate_state']:
            temp['RearMiddle'] = self.carInfo['climate_state']['seat_heater_rear_center']           
        if 'seat_heater_rear_right' in self.carInfo['climate_state']:
            temp['RearRight'] = self.carInfo['climate_state']['seat_heater_rear_right']           
        return(temp)

    def teslaEV_AutoConditioningRunning(self, id):
        #logging.debug('teslaEV_AutoConditioningRunning for {}'.format(id))
        if 'is_auto_conditioning_on' in self.carInfo['climate_state']:
            return( self.carInfo['climate_state']['is_auto_conditioning_on']) 
        else:
            return(None)

    def teslaEV_PreConditioningEnabled(self, id):
        #logging.debug('teslaEV_PreConditioningEnabled for {}'.format(id))
        if 'is_preconditioning' in self.carInfo['climate_state']:
            return(self.carInfo['climate_state']['is_preconditioning']) 
        else:
            return(None)

    def teslaEV_MaxCabinTempCtrl(self, id):
        #logging.debug('teslaEV_MaxCabinTempCtrl for {}'.format(id))
        if 'max_avail_temp' in self.carInfo['climate_state']:
            return(round(self.carInfo['climate_state']['max_avail_temp'],1))   
        else:
            return(None)

    def teslaEV_MinCabinTempCtrl(self, id):
        #logging.debug('teslaEV_MinCabinTempCtrl for {}'.format(id))
        if 'min_avail_temp' in self.carInfo['climate_state']:
            return(round(self.carInfo['climate_state']['min_avail_temp'],1))   
        else:
            return(None)

    def teslaEV_SteeringWheelHeatOn(self, id):
        #logging.debug('teslaEV_SteeringWheelHeatOn for {}'.format(id))

        return(self.steeringWheeelHeat)  



    def teslaEV_Windows(self, id, cmd):
        logging.debug('teslaEV_Windows for {}'.format(id))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                if cmd != 'vent' and cmd != 'close':
                    logging.error('Wrong command passed to (vent or close) to teslaEV_Windows: {} '.format(cmd))
                    return(False)
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {'lat':self.carInfo['drive_state']['latitude'],
                           'lon':self.carInfo['drive_state']['longitude'],
                           'command': cmd}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/window_control', headers=self.Header,  json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_Windows for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SunRoof(self, id, cmd):
        logging.debug('teslaEV_SunRoof for {}'.format(id))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                if cmd != 'vent' and cmd != 'close':
                    logging.error('Wrong command passed to (vent or close) to teslaEV_SunRoof: {} '.format(cmd))
                    return(False)
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = { 'state': cmd}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/sun_roof_control',headers=self.Header,  json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SunRoof for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)
    

    def teslaEV_AutoCondition(self, id, ctrl):
        logging.debug('teslaEV_AutoCondition for {}'.format(id))
        
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}      
                if ctrl == 'start':  
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/auto_conditioning_start', headers=self.Header,  json=payload ) 
                elif ctrl == 'stop':
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/auto_conditioning_stop', headers=self.Header,  json=payload ) 
                else:
                    logging.debug('Unknown AutoCondition command passed for vehicle id {}: {}'.format(id, ctrl))
                    return(False)
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_AutoCondition for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SetCabinTemps(self, id, tempC):
        logging.debug('teslaEV_AutoCondition for {}'.format(id))
        
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {'driver_temp' : float(tempC), 'passenger_temp':float(tempC) }      
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/set_temps', headers=self.Header, json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_AutoCondition for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_DefrostMax(self, id, ctrl):
        logging.debug('teslaEV_DefrostMax for {}'.format(id))
 
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = {}    
                if ctrl == 'on':
                    payload = {'on':True}  
                elif  ctrl == 'off':
                    payload = {'on':False}  
                else:
                    logging.error('Wrong parameter for teslaEV_DefrostMax (on/off) for vehicle id {}: {}'.format(id, ctrl))
                    return(False)
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/set_preconditioning_max', headers=self.Header, json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_AutoCondition for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SetSeatHeating (self, id, seat, levelHeat):
        logging.debug('teslaEV_SetSeatHeating for {}'.format(id))
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
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/remote_seat_heater_request', headers=self.Header, json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SetSeatHeating for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SteeringWheelHeat(self, id, ctrl):
        logging.debug('teslaEV_SteeringWheelHeat for {}'.format(id))
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
                        logging.error('Wrong paralf.carInfo[id]meter for teslaEV_SteeringWheelHeat (on/off) for vehicle id {}: {}'.format(id, ctrl))
                        return(False)
                    s.auth = OAuth2BearerToken(S['access_token'])
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/remote_steering_wheel_heater_request', headers=self.Header, json=payload ) 
                    temp = r.json()
                    return(temp['response']['result'])
                except Exception as e:
                    logging.error('Exception teslaEV_SteeringWheelHeat for vehicle id {}: {}'.format(id, e))
                    logging.error('Trying to reconnect')
                    self.teslaApi.tesla_refresh_token( )
                    return(False)
        else:
            logging.error('Steering Wheet does not seem to support heating')
            return(False)


####################
# Status Data
####################
    def teslaEV_GetStatusInfo(self, id):
        logging.debug('teslaEV_GetStatusInfo: for {} : {}'.format(id, self.carInfo))

        temp = {}
        if 'center_display_state' in self.carInfo['vehicle_state']:
            temp['center_display_state'] = self.carInfo['vehicle_state']['center_display_state']
        if 'homelink_nearby' in self.carInfo['vehicle_state']:    
            temp['homelink_nearby'] = self.carInfo['vehicle_state']['homelink_nearby']
        if 'hfd_window' in self.carInfo['vehicle_state']:        
            temp['fd_window'] = self.carInfo['vehicle_state']['fd_window']
        if 'fp_window' in self.carInfo['vehicle_state']:    
            temp['fp_window'] = self.carInfo['vehicle_state']['fp_window']
        if 'rd_window' in self.carInfo['vehicle_state']:    
            temp['rd_window'] = self.carInfo['vehicle_state']['rd_window']
        if 'rp_window' in self.carInfo['vehicle_state']:    
            temp['rp_window'] = self.carInfo['vehicle_state']['rp_window']
        if 'frunk' in self.carInfo['vehicle_state']:    
            temp['trunk'] = self.carInfo['vehicle_state']['ft']
        if 'homelink_nearby' in self.carInfo['vehicle_state']:    
            temp['trunk'] = self.carInfo['vehicle_state']['rt']
        if 'locked' in self.carInfo['vehicle_state']:    
            temp['locked'] = self.carInfo['vehicle_state']['locked']
        if 'odometer' in self.carInfo['vehicle_state']:    
            temp['odometer'] = self.carInfo['vehicle_state']['odometer']
        if 'sun_roof_percent_open' in self.carInfo['vehicle_state']:    
            temp['sun_roof_percent_open'] = self.carInfo['vehicle_state']['sun_roof_percent_open']
        if 'sun_roof_state' in self.carInfo['vehicle_state']:
            temp['sun_roof_state'] = self.carInfo['vehicle_state']['sun_roof_state']
        if 'state' in self.carInfo['vehicle_state']:    
            temp['state'] = self.carInfo['state']
        if 'timestamp' in  self.carInfo['vehicle_state']: 
            temp['timestamp'] = int(self.carInfo['vehicle_state']['timestamp'] /1000) # Tesla reports in miliseconds
       
        if 'can_actuate_trunks' in  self.carInfo['vehicle_config']: 
            self.canActuateTrunks = self.carInfo['vehicle_config']['can_actuate_trunks']    
        if 'sun_roof_installed' in  self.carInfo['vehicle_config']: 
            self.sunroofInstalled = (self.carInfo['vehicle_config']['sun_roof_installed']   > 0)
        if 'rear_seat_heaters' in  self.carInfo['vehicle_config']: 
            self.rearSeatHeat = (self.carInfo['vehicle_config']['rear_seat_heaters']   > 0)
        if 'steering_wheel_heater' in self.carInfo['vehicle_state']: 
            self.steeringWheeelHeat = self.carInfo['vehicle_state']['steering_wheel_heater']
            self.steeringWheelHeatDetected = True

        


    def teslaEV_GetCenterDisplay(self,id):

        #logging.debug('teslaEV_GetCenterDisplay: for {}'.format(id))
        #logging.debug('Car info : {}'.format(self.carInfo))
        if 'center_display_state' in self.carInfo['vehicle_state']:
            return(self.carInfo['vehicle_state']['center_display_state'])
        else:
            return(None)

    def teslaEV_GetStatusTimestamp(self,id):
        if 'timestamp' in self.carInfo['vehicle_state']:
            return(self.carInfo['vehicle_state']['timestamp'])
        else:
            return(None)

    def teslaEV_GetTimeSinceLastStatusUpdate(self, id):
        timeNow = int(time.time())
        logging.debug('Time Now {} Last Update {}'.format(timeNow,self.carInfo['vehicle_state']['timestamp']/1000 ))
        return(int(timeNow - float(self.carInfo['vehicle_state']['timestamp']/1000)))


    def teslaEV_HomeLinkNearby(self,id):
        #logging.debug('teslaEV_HomeLinkNearby: for {}'.format(id))
        if 'homelink_nearby' in self.carInfo['vehicle_state']:
            return(self.carInfo['vehicle_state']['homelink_nearby'])
        else:
            return(None)

    def teslaEV_GetLockState(self,id):
        #logging.debug('teslaEV_GetLockState: for {}'.format(id))
        if 'locked' in self.carInfo['vehicle_state']:
            return(self.carInfo['vehicle_state']['locked'])
        else:
            return(None)

    def teslaEV_GetWindoStates(self,id):
        #logging.debug('teslaEV_GetWindoStates: for {}'.format(id))
        temp = {}
        if 'fd_window' in self.carInfo['vehicle_state']:
            temp['FrontLeft'] = self.carInfo['vehicle_state']['fd_window']
        else:
            temp['FrontLeft'] = None
        if 'fp_window' in self.carInfo['vehicle_state']:
            temp['FrontRight'] = self.carInfo['vehicle_state']['fp_window']
        else:
            temp['FrontRight'] = None
        if 'rd_window' in self.carInfo['vehicle_state']:
            temp['RearLeft'] = self.carInfo['vehicle_state']['rd_window']
        else:
            temp['RearLeft'] = None
        if 'rp_window' in self.carInfo['vehicle_state']:
            temp['RearRight'] = self.carInfo['vehicle_state']['rp_window']
        else:
            temp['RearRight'] = None

        return(temp)

    def teslaEV_GetOnlineState(self,id):
        #logging.debug('teslaEV_GetOnlineState: for {}'.format(id))
        return(self.carInfo['state'])

    def teslaEV_GetOdometer(self,id):
        #logging.debug('teslaEV_GetOdometer: for {}'.format(id))
        if 'odometer' in self.carInfo['vehicle_state']:
            return(round(self.carInfo['vehicle_state']['odometer'], 2))
        else:
            return(0.0)

    def teslaEV_GetSunRoofPercent(self,id):
        #logging.debug('teslaEV_GetSunRoofState: for {}'.format(id))
        if 'sun_roof_percent_open' in self.carInfo['vehicle_state']:
            return(round(self.carInfo['vehicle_state']['sun_roof_percent_open']))
        else:
            return(None)

    def teslaEV_GetSunRoofState(self,id):
        #logging.debug('teslaEV_GetSunRoofState: for {}'.format(id))
        if 'sun_roof_state' in self.carInfo['vehicle_state'] and self.sunroofInstalled:
            return(round(self.carInfo['vehicle_state']['sun_roof_state']))
        else:
            return(99)

    def teslaEV_GetTrunkState(self,id):
        #logging.debug('teslaEV_GetTrunkState: for {}'.format(id))
        if 'rt' in self.carInfo['vehicle_state'] and self.canActuateTrunks:
            if self.carInfo['vehicle_state']['rt'] == 0:
                return(0)
            else:
                return(1)
        else:
            return(None)


    def teslaEV_GetFrunkState(self,id):
        #logging.debug('teslaEV_GetFrunkState: for {}'.format(id))
        if 'ft' in self.carInfo['vehicle_state'] and self.canActuateTrunks:
            if self.carInfo['vehicle_state']['ft'] == 0:
                return(0)
            else:
                return(1)
        else:
            return(None)     

###############
# Controls
################
    def teslaEV_FlashLights(self, id):
        logging.debug('teslaEV_GetVehicleInfo: for {}'.format(id))       
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])            
                r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/vehicle_data', headers=self.Header)          
                temp = r.json()
                self.carInfo = temp['response']
                return(self.carInfo)
            except Exception as e:
                logging.error('Exception teslaEV_FlashLight for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)


    def teslaEV_Wake(self, id):
        logging.debug('teslaEV_Wake: for {}'.format(id))
        S = self.teslaApi.teslaConnect()
        online = False
        attempts = 0 
        MAX_ATTEMPTS = 6 # try for 1 minute max
        with requests.Session() as s:
            try:

                s.auth = OAuth2BearerToken(S['access_token'])            
                while not online and attempts < MAX_ATTEMPTS:
                    attempts = attempts + 1
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/wake_up', headers=self.Header) 
                    temp = r.json()
                    self.online = temp['response']['state']
                    if self.online == 'online':
                        online = True
                    else:
                        time.sleep(10)
                return(self.online)
            except Exception as e:
                logging.error('Exception teslaEV_Wake for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)


    def teslaEV_HonkHorn(self, id):
        logging.debug('teslaEV_HonkHorn for {}'.format(id))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/honk_horn',headers=self.Header, json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_HonkHorn for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_FlashLights(self, id):
        logging.debug('teslaEV_FlashLights for {}'.format(id))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/flash_lights', headers=self.Header, json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_FlashLights for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_Doors(self, id, ctrl):
        logging.debug('teslaEV_Doors for {}'.format(id))
        
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}      
                if ctrl == 'unlock':  
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/door_unlock', headers=self.Header, json=payload ) 
                elif ctrl == 'lock':
                     r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/door_lock', headers=self.Header,  json=payload ) 
                else:
                    logging.debug('Unknown door control passed: {}'.format(ctrl))
                    return(False)
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_FlashLights for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_TrunkFrunk(self, id, frunkTrunk):
        logging.debug('teslaEV_Doors for {}'.format(id))
        
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
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/actuate_trunk',headers=self.Header,  json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_TrunkFrunk for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)


    def teslaEV_HomeLink(self, id):
        logging.debug('teslaEV_HomeLink for {}'.format(id))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {'lat':self.carInfo['drive_state']['latitude'],
                           'lon':self.carInfo['drive_state']['longitude']}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/trigger_homelink', headers=self.Header, json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_HomeLink for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)

    
   