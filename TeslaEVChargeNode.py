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

    def __init__(self, polyglot, parent, address, name, id,  TEV):
        super(teslaEV_ChargeNode, self).__init__(polyglot, parent, address, name)
        logging.info('_init_ Tesla Charge Node')
        self.poly = polyglot
        self.ISYforced = False
        self.EVid = id
        self.TEV = TEV
        self.address = address 
        self.name = name
        self.nodeReady = False
        self.node = self.poly.getNode(address)
        self.poly.subscribe(polyglot.START, self.start, address)
        
    def start(self):                
        logging.debug('Start Tesla EV charge Node: {}'.format(self.EVid))  
        self.setDriver('ST', 1, True, True)

        self.nodeReady = True

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    def poll(self):
        
        logging.debug('Charge node {}'.format(self.EVid) )
        if self.nodeReady:
            self.updateISYdrivers()
    
    def chargeNodeReady (self):
        return(self.nodeReady )
   
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
        if state == 'Connected':
            return(0)
        elif state == 'Connected':
            return(1)          
        elif state == 'Charging':
            return(2)
        elif state == 'Stopped':
            return(3)
        elif state == 'Complete':
            return(4)
        else:
            return(99)  


    def updateISYdrivers(self):
        logging.debug('ChargeNode updateISYdrivers {}'.format(self.TEV.teslaEV_GetChargingInfo(self.EVid)))
        #if self.TEV.isConnectedToEV():
        #logging.debug('GV1: {} '.format(self.TEV.teslaEV_FastChargerPresent(self.EVid)))
        self.setDriver('GV1', self.bool2ISY(self.TEV.teslaEV_FastChargerPresent(self.EVid)), True, True)
        #logging.debug('GV2: {} '.format(self.TEV.teslaEV_ChargePortOpen(self.EVid)))
        self.setDriver('GV2', self.bool2ISY(self.TEV.teslaEV_ChargePortOpen(self.EVid)), True, True)
        #logging.debug('GV3: {}'.format(self.TEV.teslaEV_ChargePortLatched(self.EVid)))
        self.setDriver('GV3', self.bool2ISY(self.TEV.teslaEV_ChargePortLatched(self.EVid)), True, True)
        #logging.debug('BATLVL: {}'.format(self.TEV.teslaEV_GetBatteryLevel(self.EVid)))
        self.setDriver('BATLVL', self.TEV.teslaEV_GetBatteryLevel(self.EVid))
        #logging.debug('GV5: {}'.format(self.TEV.teslaEV_MaxChargeCurrent(self.EVid)))
        self.setDriver('GV5', self.TEV.teslaEV_MaxChargeCurrent(self.EVid), True, True)
        logging.debug('GV6: {}'.format(self.TEV.teslaEV_ChargeState(self.EVid)))     
        self.setDriver('GV6',self.state2ISY(self.TEV.teslaEV_ChargeState(self.EVid), True, True))
        #logging.debug('GV7: {}'.format(self.TEV.teslaEV_GetChargingPower(self.EVid)))
        self.setDriver('GV7', self.bool2ISY(self.TEV.teslaEV_ChargingRequested(self.EVid), True, True))
        #logging.debug('GV8: {}'.format(self.TEV.teslaEV_ChargingRequested(self.EVid)))
        self.setDriver('GV8', self.TEV.teslaEV_GetChargingPower(self.EVid))
        #logging.debug('GV9: {}'.format(self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid)))
        self.setDriver('GV9', self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid), True, True)

  

        #else:
        #    logging.debug('System not ready yet')


    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
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
                 'BATPERCENT' : evSetBatteryChargeLimit,
                 'CHARGEAMPS' : evSetCurrentChargeLimit,

                }

    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},
            {'driver': 'GV1', 'value': 0, 'uom': 25},  #fast_charger_present
            {'driver': 'GV2', 'value': 0, 'uom': 25},  #charge_port_door_open
            {'driver': 'GV3', 'value': 0, 'uom': 25},  #charge_port_latch
            {'driver': 'BATLVL', 'value': 0, 'uom': 51},  #battery_level
            {'driver': 'GV5', 'value': 0, 'uom': 2},  #charge_current_request_max
            {'driver': 'GV6', 'value': 99, 'uom': 25},  #charging_state
            {'driver': 'GV7', 'value': 0, 'uom': 25},  #charge_enable_request
            {'driver': 'GV8', 'value': 99, 'uom':33},  #charger_power
            {'driver': 'GV9', 'value': 0, 'uom': 51},  #bat charge_limit_soc


            ]
            


