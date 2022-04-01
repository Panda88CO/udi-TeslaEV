#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

        
               
class teslaEV_ClimateNode(udi_interface.Node):

    def __init__(self, polyglot, parent, address, name, id,  TEV):
        super(teslaEV_ClimateNode, self).__init__(polyglot, parent, address, name)
        logging.info('_init_ Tesla ClimateNode Status Node')
        self.poly = polyglot
        self.ISYforced = False
        self.TEV = TEV
        self.EVid = id
        self.address = address 
        self.name = name
        self.nodeReady = False
        #self.node = self.poly.getNode(address)
        self.poly.subscribe(polyglot.START, self.start, address)
        
    def start(self):                
        logging.debug('Start TeslaEV Climate Node')  
        self.setDriver('ST', 1, True, True)
        self.nodeReady = True
        self.updateISYdrivers()

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    def climateNodeReady (self):
        return(self.nodeReady )
    
    def poll(self):
        
        logging.debug('Climate node {}'.format(self.EVid) )
        if self.nodeReady:
            self.updateISYdrivers()

    def bool2ISY(self, bool):
        if bool == True:
            return(1)
        else:
            return(0)

    def cond2ISY(self, condition):
        if condition == None:
            return(99)
        elif condition:
            return(1)
        else:
            return(0)


    def updateISYdrivers(self):
        logging.info('Climate updateISYdrivers {}'.format(self.EVid))
        logging.debug('Climate updateISYdrivers {}'.format(self.TEV.teslaEV_GetClimateInfo(self.EVid)))

        logging.debug('GV1: {} '.format(self.TEV.teslaEV_GetCabinTemp(self.EVid)))
        tempC = self.TEV.teslaEV_GetCabinTemp(self.EVid)
        if tempC == -99:
            self.setDriver('GV1', 0, True, True, 25)
        else:
            self.setDriver('GV1', self.TEV.teslaEV_GetCabinTemp(self.EVid), True, True, 4)
        logging.debug('CLITEMP: {} '.format(self.TEV.teslaEV_GetOutdoorTemp(self.EVid)))
        tempC = self.TEV.teslaEV_GetOutdoorTemp(self.EVid)
        if tempC == -99:
            self.setDriver('CLITEMP', 0, True, True, 25)
        else:
            self.setDriver('CLITEMP', self.TEV.teslaEV_GetOutdoorTemp(self.EVid), True, True, 4)
        logging.debug('GV3: {}'.format(self.TEV.teslaEV_GetLeftTemp(self.EVid)))
        self.setDriver('GV3', self.TEV.teslaEV_GetLeftTemp(self.EVid), True, True, 4)
        logging.debug('GV4: {}'.format(self.TEV.teslaEV_GetLeftTemp(self.EVid)))
        self.setDriver('GV4', self.TEV.teslaEV_GetRightTemp(self.EVid), True, True, 4)
        logging.debug('GV5-9: {}'.format(self.TEV.teslaEV_GetSeatHeating(self.EVid)))
        temp = self.TEV.teslaEV_GetSeatHeating(self.EVid)
        self.setDriver('GV5', temp['FrontLeft'], True, True)
        self.setDriver('GV6', temp['FrontRight'], True, True)
        self.setDriver('GV7', temp['RearLeft'], True, True)
        self.setDriver('GV8', temp['RearMiddle'], True, True)
        self.setDriver('GV9', temp['RearRight'], True, True)
        logging.debug('GV10: {}'.format(self.TEV.teslaEV_AutoConditioningRunning(self.EVid)))
        self.setDriver('GV10', self.cond2ISY(self.TEV.teslaEV_AutoConditioningRunning(self.EVid)), True, True)
        logging.debug('GV11: {}'.format(self.TEV.teslaEV_PreConditioningEnabled(self.EVid)))
        self.setDriver('GV11',self.cond2ISY(self.TEV.teslaEV_PreConditioningEnabled(self.EVid)), True, True)
        logging.debug('GV12: {}'.format(self.TEV.teslaEV_MaxCabinTempCtrl(self.EVid)))
        self.setDriver('GV12', self.TEV.teslaEV_MaxCabinTempCtrl(self.EVid), True, True, 4)
        logging.debug('GV13: {}'.format(self.TEV.teslaEV_MinCabinTempCtrl(self.EVid)))
        self.setDriver('GV13', self.TEV.teslaEV_MinCabinTempCtrl(self.EVid), True, True, 4)
        logging.debug('GV14: {}'.format(self.TEV.teslaEV_SteeringWheelHeatOn(self.EVid)))
        self.setDriver('GV14', self.TEV.teslaEV_SteeringWheelHeatOn(self.EVid), True, True) #nned to be implemented                                                

    def ISYupdate (self, command):
        logging.info('ISY-update called')
        self.TEV.teslaEV_GetInfo(self.EVid)
        self.updateISYdrivers()
 
 
    def evWindows (self, command):
        logging.info('evWindows- called')
        windowCtrl = int(command.get('value'))
        if windowCtrl == 1:
            self.TEV.teslaEV_Windows(self.EVid, 'vent')
        elif windowCtrl == 0:
            self.TEV.teslaEV_Windows(self.EVid, 'close')            
        else:
            logging.error('Wrong command for evWndows: {}'.format(windowCtrl))


    def evSunroof (self, command):
        logging.info('evSunroof called')   
        sunroofCtrl = int(command.get('value'))
        if sunroofCtrl == 1:
            self.TEV.teslaEV_SunRoof(self.EVid, 'vent')
        elif sunroofCtrl == 0:
            self.TEV.teslaEV_SunRoof(self.EVid, 'close')            
        else:
            logging.error('Wrong command for evSunroof: {}'.format(sunroofCtrl)) 

    def evAutoCondition (self, command):
        logging.info('evAutoCondition called')  
        autoCond = int(command.get('value'))  
        if autoCond == 1:
            self.TEV.teslaEV_AutoCondition(self.EVid, 'start')
        elif autoCond == 0:
            self.TEV.teslaEV_AutoCondition(self.EVid, 'stop')            
        else:
            logging.error('Wrong command for evAutoCondition: {}'.format(autoCond)) 

    def evDefrostMax (self, command):
        logging.info('evDefrostMax called')    
        defrost = int(command.get('value'))  
        if defrost == 1:
            self.TEV.teslaEV_DefrostMax(self.EVid, 'on')
        elif defrost == 0:
            self.TEV.teslaEV_DefrostMax(self.EVid, 'off')            
        else:
            logging.error('Wrong command for evDefrostMax: {}'.format(defrost)) 


    def evSetCabinTemp (self, command):
        logging.info('evSetCabinTemp called')      
        cabinTemp = float(command.get('value'))  
        self.TEV.teslaEV_SetCabinTemps(self.EVid, cabinTemp)
        

    def evSetSeat0Heat (self, command):
        logging.info('evSetSeat0Heat called')    
        seatTemp = int(command.get('value'))  
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 0, seatTemp)

    def evSetSeat1Heat (self, command):
        logging.info('evSetSeat1Heat called')    
        seatTemp = int(command.get('value'))  
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 1, seatTemp)

    def evSetSeat2Heat (self, command):
        logging.info('evSetSea2tHeat called')    
        seatTemp = int(command.get('value'))  
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 2, seatTemp)

    def evSetSeat4Heat (self, command):
        logging.info('evSetSeat4Heat called')    
        seatTemp = int(command.get('value'))  
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 4, seatTemp)

    def evSetSeat5Heat (self, command):
        logging.info('evSetSeat5Heat called')    
        seatTemp = int(command.get('value'))  
        self.TEV.teslaEV_SetSeatHeating(self.EVid, 5, seatTemp)


    def evSteeringWheelHeat (self, command):
        logging.info('evSteeringWheelHeat called')    
        wheel = int(command.get('value'))  
        if wheel == 1:
            self.TEV.teslaEV_SteeringWheelHeat(self.EVid, 'on')
        elif wheel == 0:
            self.TEV.teslaEV_SteeringWheelHeat(self.EVid, 'off')            
        else:
            logging.error('Wrong command for evDefrostMax: {}'.format(wheel)) 

    id = 'evclimate'
    commands = { 'UPDATE': ISYupdate, 
                 'WINDOWS' : evWindows,
                 'SUNROOF' : evSunroof,
                 'AUTOCON' : evAutoCondition,
                 'CABINTEMP' : evSetCabinTemp,
                 'DEFROST' : evDefrostMax,            
                 'SEAT1' :evSetSeat0Heat,
                 'SEAT2' :evSetSeat1Heat,
                 'SEAT3' :evSetSeat2Heat,
                 'SEAT4' :evSetSeat4Heat,
                 'SEAT5' :evSetSeat5Heat,
                 'STEERINGW' : evSteeringWheelHeat   

                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},
            {'driver': 'GV1', 'value': 0, 'uom': 4},  #inside_temp
            {'driver': 'CLITEMP', 'value': 0, 'uom': 4},  #outside_temp
            {'driver': 'GV3', 'value': 0, 'uom': 4},  #driver_temp_setting
            {'driver': 'GV4', 'value': 0, 'uom': 4},  #passenger_temp_setting
            {'driver': 'GV5', 'value': 0, 'uom': 25},  #seat_heater_left
            {'driver': 'GV6', 'value': 0, 'uom': 25},  #seat_heater_right
            {'driver': 'GV7', 'value': 0, 'uom': 25},  #seat_heater_rear_left
            {'driver': 'GV8', 'value': 0, 'uom': 25},  #seat_heater_rear_center
            {'driver': 'GV9', 'value': 0, 'uom': 25},  #seat_heater_rear_right
            {'driver': 'GV10', 'value': 0, 'uom': 25}, #is_auto_conditioning_on
            {'driver': 'GV12', 'value': 0, 'uom': 25}, #is_preconditioning
            {'driver': 'GV12', 'value': 0, 'uom': 4}, #max_avail_temp
            {'driver': 'GV13', 'value': 0, 'uom': 4}, #min_avail_temp   
            {'driver': 'GV14', 'value': 99, 'uom': 25}, #Steering Wheel Heat
            ]


