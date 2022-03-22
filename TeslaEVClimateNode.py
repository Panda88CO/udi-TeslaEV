#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.logging
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

import time
#import udi_interface
#logging = udi_interface.logging
               
class teslaEV_ClimateNode(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name, id,  TEV):
        super(teslaEV_ClimateNode, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ Tesla Power Wall Generator Status Node')
        self.ISYforced = False
        self.TEV = TEV
        self.id = id
        self.address = address 
        self.name = name


        polyglot.subscribe(polyglot.START, self.start, address)
        
    def start(self):                
        logging.debug('Start Tesla Power Wall Generator Node')  
        while not self.TEV.systemReady:
            time.sleep(1)
        self.updateISYdrivers('all')

    def stop(self):
        logging.debug('stop - Cleaning up')
    '''
    def updateISYdrivers(self, level):
        if self.TEV.systemReady:
            logging.debug('SolarNode updateISYdrivers')
            self.setDriver('GV1', self.TEV.getTEV_daysGeneratorUse())
            self.setDriver('GV2', self.TEV.getTEV_yesterdayGeneratorUse())
        else:
            logging.debug('System not ready yet')
    '''
    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        if self.TEV.teslaEV_GetClimateInfo(self.id):
            self.updateISYdrivers('all')
 
 
    def evWindows (self, command):
        logging.debug('evWindows- called')


    def evSunroof (self, command):
        logging.debug('evSunroof called')    

    def evAutoCondition (self, command):
        logging.debug('evAutoCondition called')    

    def evDefrostMax (self, command):
        logging.debug('evDefrostMax called')    


    def evSetCabinTemp (self, command):
        logging.debug('evSetCabinTemp called')    

    def evSetSeatHeat (self, command):
        logging.debug('evSetSeatHeat called')    

    def evSteeringWheelHeat (self, command):
        logging.debug('evSteeringWheelHeat called')    


    id = 'evclimate'
    commands = { 'UPDATE': ISYupdate, 
                 'WINDOWS' : evWindows,
                 'SUNROOF' : evSunroof,
                 'AUTOCON' : evAutoCondition,
                 'CABINTEMP' : evSetCabinTemp,
                 'DEFROST' : evDefrostMax,            
                 'SEAT1' :evSetSeatHeat,
                 'SEAT2' :evSetSeatHeat,
                 'SEAT3' :evSetSeatHeat,
                 'SEAT4' :evSetSeatHeat,
                 'SEAT5' :evSetSeatHeat,

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
            {'driver': 'GV14', 'value': 0, 'uom': 25}, #Steering Wheel Heat
         
            ]


