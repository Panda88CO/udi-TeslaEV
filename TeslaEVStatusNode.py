#!/usr/bin/env python3

#import udi_interface


#from os import truncate
import sys
import TeslaEVInfo
import time

try:
    import udi_interface
    logging = udi_interface.logging
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

               
class teslaEVStatusNode(udi_interface.Node):

    def __init__(self, polyglot, primary, address, name, TEV):
        super(teslaPWStatusNode, self).__init__(polyglot, primary, address, name)
        logging.info('_init_ Tesla Power Wall Status Node')
        self.ISYforced = False
        self.TEV = TEV
        self.address = address 
        self.name = name
        self.hb = 0

        polyglot.subscribe(polyglot.START, self.start, address)
        
    def start(self):                
        logging.debug('Start Tesla Power Wall Status Node')  
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

 

    id = 'pwstatus'
    commands = { 'UPDATE': ISYupdate, 
                }


    drivers = [
            {'driver': 'GV1', 'value': 0, 'uom': 51},  #battery level
            {'driver': 'GV2', 'value': 0, 'uom': 25},  #mode
            {'driver': 'GV3', 'value': 0, 'uom': 25},  #grid status
            {'driver': 'GV4', 'value': 0, 'uom': 25},  #on/off line
            {'driver': 'GV5', 'value': 0, 'uom': 25},  #grid services
            {'driver': 'GV6', 'value': 0, 'uom': 33},  #battery supply
            {'driver': 'GV7', 'value': 0, 'uom': 33},  #battery today
            {'driver': 'GV8', 'value': 0, 'uom': 33},  #battery yesterday
            {'driver': 'GV9', 'value': 0, 'uom': 33},  #grid supply
            {'driver': 'GV10', 'value': 0, 'uom': 33}, #grid today
            {'driver': 'GV11', 'value': 0, 'uom': 33}, #grid yesterday
            {'driver': 'GV12', 'value': 0, 'uom': 33}, #load
            {'driver': 'GV13', 'value': 0, 'uom': 33}, #consumption today
            {'driver': 'GV14', 'value': 0, 'uom': 33}, #consumption yesterday
            {'driver': 'GV15', 'value': 0, 'uom': 33}, #generation today
            {'driver': 'GV16', 'value': 0, 'uom': 33}, #generation yesterday
            {'driver': 'GV17', 'value': 0, 'uom': 33}, #grid service today
            {'driver': 'GV18', 'value': 0, 'uom': 33}, #grid service yesterday
            ]


