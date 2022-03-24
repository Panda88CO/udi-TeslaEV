#!/usr/bin/env python3
PG_CLOUD_ONLY = False



#from os import truncate
import sys

import time
try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

class teslaEV_ChargeNode(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name, id,  TEV):
        super(teslaEV_ChargeNode, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ Tesla Power Wall Status Node')
        self.ISYforced = False
        self.id = id
        self.TEV = TEV
        self.address = address 
        self.name = name

        polyglot.subscribe(polyglot.START, self.start, address)
        
    def start(self):                
        logging.debug('Start Tesla EV charge Node: {}'.format(self.id))  
        while not self.TEV.systemReady:
            time.sleep(1)
        self.updateISYdrivers('all')

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    def bool2ISY(self, bool):
        if bool == True:
            return(1)
        else:
            return(0)

    def latch2ISY(self, state):
        if state == 'Engaged':
            return(1)
        else:
            return(0)

    def state2ISY(self,state): # Still TBD - 
        if state == 'Complete':
            return(1)
        else:
            return(0)  


    def updateISYdrivers(self, id):
        logging.debug('ChargeNode updateISYdrivers')
        if self.TEV.systemReady:
            logging.debug('GV1: {} '.format(self.TEV.teslaEV_FastChargerPresent(self.id)))
            self.setDriver('GV1', self.bool2ISY(self.TEV.teslaEV_FastChargerPresent(self.id)))
            logging.debug('GV2: {} '.format(self.TEV.teslaEV_ChargePortOpen(self.id)))
            self.setDriver('GV2', self.bool2ISY(self.TEV.teslaEV_ChargePortOpen(self.id)))
            logging.debug('GV3: {}'.format(self.TEV.teslaEV_ChargePortLatched(self.id)))
            self.setDriver('GV3', self.bool2ISY(self.TEV.teslaEV_ChargePortLatched(self.id)))
            logging.debug('BATLVL: {}'.format(self.TEV.teslaEV_GetBatteryLevel(self.id)))
            self.setDriver('BATLVL', self.TEV.teslaEV_GetBatteryLevel(self.id))
            logging.debug('GV5: {}'.format(self.TEV.teslaEV_MaxChargeCurrent(self.id)))
            self.setDriver('GV5', self.state2ISY(self.TEV.teslaEV_MaxChargeCurrent(self.id)))
            logging.debug('GV6: {}'.format(self.TEV.teslaEV_MaxChargeCurrent(self.id)))     
            self.setDriver('GV6', self.TEV.teslaEV_MaxChargeCurrent(self.id))
            logging.debug('GV7: {}'.format(self.TEV.teslaEV_GetChargingPower(self.id)))
            self.setDriver('GV7', self.TEV.teslaEV_GetChargingPower(self.id))
            logging.debug('GV8: {}'.format(self.TEV.teslaEV_ChargingRequested(self.id)))
            self.setDriver('GV8', self.bool2ISY(self.TEV.teslaEV_ChargingRequested(self.id)))
            logging.debug('GV9: {}'.format(self.TEV.teslaEV_GetBatteryMaxCharge(self.id)))
            self.setDriver('GV9', self.TEV.teslaEV_GetBatteryMaxCharge(self.id))

  

        else:
            logging.debug('System not ready yet')


    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        self.TEV.teslaEV_GetInfo(self.id)
        self.updateISYdrivers()
     

    def evChargePort (self, command):
        logging.debug('evChargePort called')

    def evChargeControl (self, command):
        logging.debug('evChargeControl called')


    def evSetBatteryChargeLimit (self, command):
        logging.debug('evSetBatteryChargeLimit called')

    def evSetCurrentChargeLimit (self, command):
        logging.debug('evSetCurrentChargeLimit called')

    id = 'evcharge'
    commands = { 'UPDATE': ISYupdate, 
                 'CHARGEPORT' : evChargePort,
                 'CHARGECTRL' : evChargeControl,
                 'BATERCENT' : evSetBatteryChargeLimit,
                 'CHARGEAMPS' : evSetCurrentChargeLimit,

                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},
            {'driver': 'GV1', 'value': 0, 'uom': 25},  #fast_charger_present
            {'driver': 'GV2', 'value': 0, 'uom': 25},  #charge_port_door_open
            {'driver': 'GV3', 'value': 0, 'uom': 25},  #charge_port_latch
            {'driver': 'BATLVL', 'value': 0, 'uom': 51},  #battery_level
            {'driver': 'GV5', 'value': 0, 'uom': 1},  #charge_current_request_max
            {'driver': 'GV6', 'value': 0, 'uom': 25},  #charging_state
            {'driver': 'GV8', 'value': 0, 'uom': 25},  #charge_enable_request
            {'driver': 'GV7', 'value': 0, 'uom': 33},  #charger_power
            {'driver': 'GV9', 'value': 0, 'uom': 51},  #bat charge_limit_soc


            ]
            


