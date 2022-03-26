
#from datetime import datetime
#from tempfile import tempdir
import requests
import time
from requests_oauth2 import OAuth2BearerToken
#from TPWauth import TPWauth

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

from TeslaCloudApi import teslaCloudApi

class teslaCloudEVapi(object):
    def __init__(self):
        logging.debug('teslaCloudEVapi')
        self.teslaApi = teslaCloudApi()

        self.TESLA_URL = self.teslaApi.TESLA_URL
        self.API = self.teslaApi.API

        if self.teslaApi.isConnectedToTesla():
            self.connnected = True
        else:
            self.connected = False

        self.carInfo = {}

    def isConnectedToEV(self):
       return(self.teslaApi.isConnectedToTesla())

    def teslaEV_GetIdList(self ):
        logging.debug('teslaEV_GetVehicleIdList:')
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])  
                r = s.get(self.TESLA_URL + self.API+ '/vehicles')                         
                list = r.json()
                temp = []
                for id in range(0,len(list['response'])):
                    temp.append(list['response'][id]['id_s'])
                return (temp)
            except Exception as e:
                logging.error('Exception teslaEV_GetVehicleIdList: ' + str(e))
                logging.error('Error getting vehicle list')
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)

    
    def teslaEV_UpdateInfo(self):
            #if self.connectionEstablished:
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])            
                r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/vehicle_data')          
                carInfo = r.json()
                self.carInfo = carInfo['response']
                #logging.debug('carinf : {}'.format(self.carInfo))
                #return()
            except Exception as e:
                logging.error('Exception teslaGetSiteInfo: {}'.format(e))
                logging.error('Error getting data from vehicle id: {}'.format(id))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)

    def teslaEV_GetInfo(self, id):
        #if self.connectionEstablished:
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])            
                r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/vehicle_data')          
                carInfo = r.json()
                self.carInfo[id] =carInfo['response']
                #logging.debug('carinf : {}'.format(self.carInfo))
                return(self.carInfo[id])

            except Exception as e:
                logging.error('Exception teslaGetSiteInfo: {}'.format(e))
                logging.error('Error getting data from vehicle id: {}'.format(id))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)

    def teslaEV_GetLocation(self, id):
        logging.debug('teslaEV_GetLocation: for {}'.format(id))
        temp = {}
        temp['longitude'] = self.carInfo[id]['drive_state']['longitude']
        temp['latitide'] = self.carInfo[id]['drive_state']['latitide']
        return(temp)


####################
# Charge Data
####################
    def teslaEV_GetChargingInfo(self, id):
        logging.debug('teslaEV_GetChargingInfo: for {}'.format(id))
        temp = {}
        temp['fast_charger_present'] = self.carInfo[id]['charge_state']['fast_charger_present']
        temp['charge_port_latch'] =  self.carInfo[id]['charge_state']['charge_port_latch']
        temp['charge_port_door_open'] =  self.carInfo[id]['charge_state']['charge_port_door_open']
        temp['battery_level'] = self.carInfo[id]['charge_state']['battery_level']
        temp['charge_current_request_max'] = self.carInfo[id]['charge_state']['charge_current_request_max']
        temp['est_battery_range'] = self.carInfo[id]['charge_state']['est_battery_range']
        temp['charging_state'] = self.carInfo[id]['charge_state']['charging_state']
        temp['charge_enable_request'] = self.carInfo[id]['charge_state']['charge_enable_request']
        temp['charger_power'] = self.carInfo[id]['charge_state']['charger_power']
        temp['charge_limit_soc'] = self.carInfo[id]['charge_state']['charge_limit_soc']      
        return(temp)


    def teslaEV_FastChargerPresent(self, id):
        #logging.debug('teslaEV_FastchargerPresent for {}'.format(id))
        return(self.carInfo[id]['charge_state']['fast_charger_present'])

  
    def teslaEV_ChargePortOpen(self, id):
        #logging.debug('teslaEV_ChargePortOpen for {}'.format(id))
        return(self.carInfo[id]['charge_state']['charge_port_door_open'])  

    def teslaEV_ChargePortLatched(self, id):
        #logging.debug('teslaEV_ChargePortOpen for {}'.format(id))
        return(self.carInfo[id]['charge_state']['charge_port_latch'])             

    def teslaEV_GetBatteryLevel(self, id):
        #logging.debug('teslaEV_GetBatteryLevel for {}'.format(id))
        return(round(self.carInfo[id]['charge_state']['battery_level'],1)) 

    def teslaEV_MaxChargeCurrent(self, id):
        #logging.debug('teslaEV_MaxChargeCurrent for {}'.format(id))
        return( self.carInfo[id]['charge_state']['charge_current_request_max'])                

    def teslaEV_ChargeState(self, id):
        #logging.debug('teslaEV_GetChargingState for {}'.format(id))
        return( self.carInfo[id]['charge_state']['charging_state'])  

    def teslaEV_ChargingRequested(self, id):
        #logging.debug('teslaEV_ChargingRequested for {}'.format(id))
        return(  self.carInfo[id]['charge_state']['charge_enable_request'])  

    def teslaEV_GetChargingPower(self, id):
        #logging.debug('teslaEV_GetChargingPower for {}'.format(id))
        if self.carInfo[id]['charge_state']['charger_power']:
            return(round(self.carInfo[id]['charge_state']['charger_power'],1)) 
        else:
            return(0)

    def teslaEV_GetBatteryMaxCharge(self, id):
        #logging.debug('teslaEV_GetBatteryMaxCharge for {}'.format(id))
        return(round(self.carInfo[id]['charge_state']['charge_limit_soc'],1)) 


    def teslaEV_ChargePort(self, id, ctrl):
        logging.debug('teslaEV_ChargePort for {}'.format(id))
 
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {}      
                if ctrl == 'open':  
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/charge_port_door_open', json=payload ) 
                elif ctrl == 'close':
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/charge_port_door_close', json=payload ) 
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
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/charge_start', json=payload ) 
                elif ctrl == 'stop':
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/charge_stop', json=payload ) 
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
       
        if limit > 100 or limit < 0:
            logging.error('Invalid seat heat level passed (0-100%) : {}'.format(limit))
            return(False)
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = { 'percent':limit}    
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/set_charge_limit', json=payload ) 
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
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/set_charging_amps', json=payload ) 
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
        temp['inside_temp'] = self.carInfo[id]['climate_state']['inside_temp']
        temp['outside_temp'] = self.carInfo[id]['climate_state']['outside_temp']
        temp['driver_temp_setting'] = self.carInfo[id]['climate_state']['driver_temp_setting']
        temp['passenger_temp_setting'] = self.carInfo[id]['climate_state']['passenger_temp_setting']
        temp['seat_heater_left'] = self.carInfo[id]['climate_state']['seat_heater_left']
        temp['seat_heater_right'] = self.carInfo[id]['climate_state']['seat_heater_right']
        temp['seat_heater_rear_center'] = self.carInfo[id]['climate_state']['seat_heater_rear_center']
        temp['seat_heater_rear_left'] = self.carInfo[id]['climate_state']['seat_heater_rear_left']
        temp['seat_heater_rear_right'] = self.carInfo[id]['climate_state']['seat_heater_rear_right']
        temp['is_auto_conditioning_on'] = self.carInfo[id]['climate_state']['is_auto_conditioning_on']
        temp['is_preconditioning'] = self.carInfo[id]['climate_state']['is_preconditioning']
        temp['max_avail_temp'] = self.carInfo[id]['climate_state']['max_avail_temp']
        temp['min_avail_temp'] = self.carInfo[id]['climate_state']['min_avail_temp']
        return(temp)

    def teslaEV_GetCabinTemp(self, id):
        #logging.debug('teslaEV_GetCabinTemp for {} - {}'.format(id, self.carInfo[id]['climate_state']['inside_temp'] ))
        if self.carInfo[id]['climate_state']['inside_temp']:
            return(round(self.carInfo[id]['climate_state']['inside_temp'],1)) 
        else:
            return(-99)

    def teslaEV_GetOutdoorTemp(self, id):
        #logging.debug('teslaEV_GetOutdoorTemp for {} = {}'.format(id, self.carInfo[id]['climate_state']['outside_temp']))
        if self.carInfo[id]['climate_state']['outside_temp']:
            return(round(self.carInfo[id]['climate_state']['outside_temp'],1)) 
        else:
            return(-99)

    def teslaEV_GetLeftTemp(self, id):
        #logging.debug('teslaEV_GetLeftTemp for {}'.format(id))
        return(round(self.carInfo[id]['climate_state']['driver_temp_setting'],1))        

    def teslaEV_GetRightTemp(self, id):
        #logging.debug('teslaEV_GetRightTemp for {}'.format(id))
        return(round(self.carInfo[id]['climate_state']['passenger_temp_setting'],1))   

    def teslaEV_GetSeatHeating(self, id):
        #logging.debug('teslaEV_GetSeatHeating for {}'.format(id))
        temp = {}
        temp['FrontLeft'] = self.carInfo[id]['climate_state']['seat_heater_left']
        temp['FrontRight'] = self.carInfo[id]['climate_state']['seat_heater_right']   
        temp['RearLeft'] = self.carInfo[id]['climate_state']['seat_heater_rear_left']   
        temp['RearMiddle'] = self.carInfo[id]['climate_state']['seat_heater_rear_center']           
        temp['RearRight'] = self.carInfo[id]['climate_state']['seat_heater_rear_right']           
        return(temp)

    def teslaEV_AutoConditioningRunning(self, id):
        #logging.debug('teslaEV_AutoConditioningRunning for {}'.format(id))
        if self.carInfo[id]['climate_state']['is_auto_conditioning_on']:
            return( self.carInfo[id]['climate_state']['is_auto_conditioning_on']) 
        else:
            return(99)

    def teslaEV_PreConditioningEnabled(self, id):
        #logging.debug('teslaEV_PreConditioningEnabled for {}'.format(id))
        return(self.carInfo[id]['climate_state']['is_preconditioning']) 
    
    def teslaEV_MaxCabinTempCtrl(self, id):
        #logging.debug('teslaEV_MaxCabinTempCtrl for {}'.format(id))
        return(round(self.carInfo[id]['climate_state']['max_avail_temp'],1))   

    def teslaEV_MinCabinTempCtrl(self, id):
        #logging.debug('teslaEV_MinCabinTempCtrl for {}'.format(id))
        return(round(self.carInfo[id]['climate_state']['min_avail_temp'],1))   


    def teslaEV_SteeringWheelHeatOn(self, id):
        #logging.debug('teslaEV_SteeringWheelHeatOn for {}'.format(id))
        return(99)  



    def teslaEV_Windows(self, id, cmd):
        logging.debug('teslaEV_Windows for {}'.format(id))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                if cmd != 'vent' and cmd != 'close':
                    logging.error('Wrong command passed to (vent or close) to teslaEV_Windows: {} '.format(cmd))
                    return(False)
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {'lat':self.carInfo[id]['drive_state']['latitude'],
                           'lon':self.carInfo[id]['drive_state']['longitude'],
                           'command': cmd}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/window_control', json=payload ) 
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
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/sun_roof_control', json=payload ) 
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
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/auto_conditioning_start', json=payload ) 
                elif ctrl == 'stop':
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/auto_conditioning_stop', json=payload ) 
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
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/set_temps', json=payload ) 
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
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/set_preconditioning_max', json=payload ) 
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
        if int(levelHeat) > 3 or int(levelHeat) < 0:
            logging.error('Invalid seat heat level passed (0-3) : {}'.format(levelHeat))
            return(False)
        if seat not in seats: 
            logging.error('Invalid seatpassed (frontLeft, frontRight ,rearLeft, rearCenter, rearRight) : {}'.format(seat))
            return(False)          

        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = { 'heater':seats[seat], 'level':int(levelHeat)}    
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/remote_seat_heater_request', json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SetSeatHeating for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


    def teslaEV_SteeringWheelHeat(self, id, ctrl):
        logging.debug('teslaEV_SteeringWheelHeat for {}'.format(id))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                payload = {}    
                if ctrl == 'on':
                    payload = {'on':True}  
                elif  ctrl == 'off':
                    payload = {'on':False}  
                else:
                    logging.error('Wrong parameter for teslaEV_SteeringWheelHeat (on/off) for vehicle id {}: {}'.format(id, ctrl))
                    return(False)
                s.auth = OAuth2BearerToken(S['access_token'])
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/remote_steering_wheel_heater_request', json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_SteeringWheelHeat for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)


####################
# Status Data
####################
    def teslaEV_GetStatusInfo(self, id):
        logging.debug('teslaEV_GetStatusInfo: for {}'.format(id))
        temp = {}
        temp['center_display_state'] = self.carInfo[id]['vehicle_state']['center_display_state']
        temp['homelink_nearby'] = self.carInfo[id]['vehicle_state']['homelink_nearby']
        temp['fd_window'] = self.carInfo[id]['vehicle_state']['fd_window']
        temp['fp_window'] = self.carInfo[id]['vehicle_state']['fp_window']
        temp['rd_window'] = self.carInfo[id]['vehicle_state']['rd_window']
        temp['rp_window'] = self.carInfo[id]['vehicle_state']['rp_window']
        temp['frunk'] = self.carInfo[id]['vehicle_state']['ft']
        temp['trunk'] = self.carInfo[id]['vehicle_state']['rt']
        temp['locked'] = self.carInfo[id]['vehicle_state']['locked']
        temp['odometer'] = self.carInfo[id]['vehicle_state']['odometer']
        temp['sun_roof_percent_open'] = self.carInfo[id]['vehicle_state']['sun_roof_percent_open']
        temp['state'] = self.carInfo[id]['state']
        return(temp)

    def teslaEV_GetCenterDisplay(self,id):

        #logging.debug('teslaEV_GetCenterDisplay: for {}'.format(id))
        #logging.debug('Car info : {}'.format(self.carInfo))
        return(self.carInfo[id]['vehicle_state']['center_display_state'])


    def teslaEV_HomeLinkNearby(self,id):
        #logging.debug('teslaEV_HomeLinkNearby: for {}'.format(id))
        return(self.carInfo[id]['vehicle_state']['homelink_nearby'])

    def teslaEV_GetLockState(self,id):
        #logging.debug('teslaEV_GetLockState: for {}'.format(id))
        return(self.carInfo[id]['vehicle_state']['locked'])

    def teslaEV_GetWindoStates(self,id):
        #logging.debug('teslaEV_GetWindoStates: for {}'.format(id))
        temp = {}
        temp['FrontLeft'] = self.carInfo[id]['vehicle_state']['fd_window']
        temp['FrontRight'] = self.carInfo[id]['vehicle_state']['fp_window']
        temp['RearLeft'] = self.carInfo[id]['vehicle_state']['rd_window']
        temp['RearRight'] = self.carInfo[id]['vehicle_state']['rp_window']
        return(temp)

    def teslaEV_GetOnlineState(self,id):
        #logging.debug('teslaEV_GetOnlineState: for {}'.format(id))
        return(self.carInfo[id]['state'])

    def teslaEV_GetOdometer(self,id):
        #logging.debug('teslaEV_GetOdometer: for {}'.format(id))
        return(round(self.carInfo[id]['vehicle_state']['odometer'], 2))

    def teslaEV_GetSunRoofState(self,id):
        #logging.debug('teslaEV_GetSunRoofState: for {}'.format(id))
        return(round(self.carInfo[id]['vehicle_state']['sun_roof_percent_open']))


    def teslaEV_GetTrunkState(self,id):
        #logging.debug('teslaEV_GetTrunkState: for {}'.format(id))
        return(self.carInfo[id]['vehicle_state']['rt'])

    def teslaEV_GetFrunkState(self,id):
        #logging.debug('teslaEV_GetFrunkState: for {}'.format(id))
        return(self.carInfo[id]['vehicle_state']['ft'])        

###############
# Controls
################
    def teslaEV_FlashLights(self, id):
        logging.debug('teslaEV_GetVehicleInfo: for {}'.format(id))       
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])            
                r = s.get(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/vehicle_data')          
                temp = r.json()
                self.carInfo[id] = temp['response']
                return(self.carInfo[id])
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
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/wake_up') 
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
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/honk_horn', json=payload ) 
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
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/flash_lights', json=payload ) 
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
                    r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/door_unlock', json=payload ) 
                elif ctrl == 'lock':
                     r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/door_lock', json=payload ) 
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
                if frunkTrunk == 'Frunk':
                    cmd = 'front' 
                elif frunkTrunk == 'Trunk':
                     cmd = 'rear' 
                else:
                    logging.debug('Unknown trunk command passed: {}'.format(cmd))
                    return(False)
                payload = {'which_trunk':cmd}      
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/actuate_trunk', json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_FlashLights for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(None)


    def teslaEV_HomeLink(self, id):
        logging.debug('teslaEV_HomeLink for {}'.format(id))
        S = self.teslaApi.teslaConnect()
        with requests.Session() as s:
            try:
                s.auth = OAuth2BearerToken(S['access_token'])    
                payload = {'lat':self.carInfo[id]['drive_state']['latitude'],
                           'lon':self.carInfo[id]['drive_state']['longitude']}        
                r = s.post(self.TESLA_URL + self.API+ '/vehicles/'+str(id) +'/command/trigger_homelink', json=payload ) 
                temp = r.json()
                return(temp['response']['result'])
            except Exception as e:
                logging.error('Exception teslaEV_HomeLink for vehicle id {}: {}'.format(id, e))
                logging.error('Trying to reconnect')
                self.teslaApi.tesla_refresh_token( )
                return(False)

    
   