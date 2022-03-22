#!/usr/bin/env python3

#import udi_interface


#from os import truncate
import sys
import time
import re
from TeslaEVChargeNode import teslaEV_ChargeNode
from TeslaEVClimateNode import teslaEV_ClimateNode 

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

               
class teslaEV_StatusNode(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name, id, TEV):
        super(teslaEV_StatusNode, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ Tesla Power Wall Status Node')
        self.ISYforced = False
        self.id = id
        self.TEV = TEV
        self.primary = primary
        self.address = address
        self.name = name
        self.hb = 0

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.n_queue = []


    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()


    def start(self):                
        logging.info('Start Tesla EV Status Node for {}'.format(self.id)) 
        tmpStr = re.findall('[0-9]+', self.address)
        nbrStr = tmpStr.pop()

        nodeAdr = 'climate'+nbrStr
        if not self.poly.getNode(nodeAdr):
            climateNode = teslaEV_ClimateNode(self.poly, self.address, nodeAdr, 'EV climate Info', self.id, self.TEV )
        
        nodeAdr = 'charge'+nbrStr
        if not self.poly.getNode(nodeAdr):
            chargeNode = teslaEV_ChargeNode(self.poly, self.address, nodeAdr, 'EV Charging Info', self.id, self.TEV )
        
        
        
        
        while not self.TEV.systemReady:
            time.sleep(1)
        self.updateISYdrivers('all')

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    def updateISYdrivers(self, level):
        if self.TEV.systemReady:
            logging.debug('StatusNode updateISYdrivers')
            logging.debug('GV1: '+ str(self.TEV.getTEV_chargeLevel()))
            self.setDriver('GV1', self.TEV.getTEV_chargeLevel())
            logging.debug('GV2: '+ str(self.TEV.getTEV_operationMode()))
            self.setDriver('GV2', self.TEV.getTEV_operationMode())
            logging.debug('GV3: '+ str(self.TEV.getTEV_gridStatus()))
            self.setDriver('GV3', self.TEV.getTEV_gridStatus())
            logging.debug('GV4: '+ str(self.TEV.getTEV_onLine()))
            self.setDriver('GV4', self.TEV.getTEV_onLine())
            logging.debug('GV5: '+ str(self.TEV.getTEV_gridServiceActive()))
            self.setDriver('GV5', self.TEV.getTEV_gridServiceActive())
            logging.debug('GV6: '+ str(self.TEV.getTEV_chargeLevel()))
            self.setDriver('GV6', self.TEV.getTEV_gridSupply())
            logging.debug('GV9: '+ str(self.TEV.getTEV_chargeLevel()))
            self.setDriver('GV9', self.TEV.getTEV_gridSupply())
            logging.debug('GV12: '+ str(self.TEV.getTEV_load()))
            self.setDriver('GV12', self.TEV.getTEV_load())

            if level == 'all':
                self.setDriver('GV7', self.TEV.getTEV_daysBattery())
                self.setDriver('GV8', self.TEV.getTEV_yesterdayBattery())
                self.setDriver('GV10', self.TEV.getTEV_daysGrid())
                self.setDriver('GV11', self.TEV.getTEV_yesterdayGrid())
                self.setDriver('GV13', self.TEV.getTEV_daysConsumption())
                self.setDriver('GV14', self.TEV.getTEV_yesterdayConsumption())
                self.setDriver('GV15', self.TEV.getTEV_daysGeneration())
                self.setDriver('GV16', self.TEV.getTEV_yesterdayGeneration())
                self.setDriver('GV17', self.TEV.getTEV_daysGridServicesUse())
                self.setDriver('GV18', self.TEV.getTEV_yesterdayGridServicesUse())
        else:
            logging.debug('System not ready yet')


    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        if self.TEV.pollSystemData('all'):
            self.updateISYdrivers('all')

    def evWakeUp (self, command):
        logging.debug('EVwakeUp called')

    def evHonkHorn (self, command):
        logging.debug('EVhonkHorn called')

    def evFlashLights (self, command):
        logging.debug('EVflashLights called')

    def evControlDoors (self, command):
        logging.debug('EVctrlDoors called')

    def evControlSunroof (self, command):
        logging.debug('evControlSunroof called')


    def evOpenTrunkFrunk (self, command):
        logging.debug('EVopenTrunkFrunk called')                

    def evHomelink (self, command):
        logging.debug('EVhomelink called')   

    id = 'evstatus'
    commands = { 'UPDATE': ISYupdate, 
                 'WAKEUP' : evWakeUp,
                 'HONK' : evHonkHorn,
                 'LIGHTS' : evFlashLights,
                 'DOORS' : evControlDoors,
                 'SUNROOFCTRL' : evControlSunroof,
                 'TRUNK' : evOpenTrunkFrunk,
                 'FRUNK' : evOpenTrunkFrunk,
                 'HOMELINK' : evHomelink,
                }


    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},
            {'driver': 'GV1', 'value': 0, 'uom': 25},  #center_display_state
            {'driver': 'GV2', 'value': 0, 'uom': 25},  #homelink_nearby
            {'driver': 'GV3', 'value': 0, 'uom': 25},  #locked
            {'driver': 'GV4', 'value': 0, 'uom': 25},  #odometer
            {'driver': 'GV5', 'value': 0, 'uom': 25},  #state (on line)
            {'driver': 'GV6', 'value': 0, 'uom': 25},  #fd_window
            {'driver': 'GV7', 'value': 0, 'uom': 25},  #fp_window
            {'driver': 'GV8', 'value': 0, 'uom': 25},  #rd_window
            {'driver': 'GV9', 'value': 0, 'uom': 25},  #rp_window
            {'driver': 'GV10', 'value': 0, 'uom': 51}, #sun_roof_percent_open
            {'driver': 'GV11', 'value': 0, 'uom': 25}, #trunk
            {'driver': 'GV12', 'value': 0, 'uom': 25}, #frunk
            ]


