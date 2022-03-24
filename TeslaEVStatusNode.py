#!/usr/bin/env python3

#import udi_interface


#from os import truncate
import sys
import time
import re
from xml.etree.ElementTree import TreeBuilder
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

    def bool2ISY(self, bool):
        if bool == True:
            return(1)
        else:
            return(0)

    def online2ISY(self, state):
        if state == 'Online':
            return(1)
        else:
            return(0)
    
    def updateISYdrivers(self):

        if self.TEV.systemReady:
            temp = {}
            logging.debug('StatusNode updateISYdrivers')
            logging.debug('GV1: {} '.format(self.TEV.teslaEV_GetCenterDisplay(self.id)))
            self.setDriver('GV1', self.TEV.teslaEV_GetCenterDisplay(self.id))
            logging.debug('GV2: {} '.format(self.TEV.teslaEV_HomeLinkNearby(self.id)))
            self.setDriver('GV2', self.bool2ISY(self.TEV.teslaEV_HomeLinkNearby(self.id)))
            logging.debug('GV3: {}'.format(self.TEV.teslaEV_GetLockState(self.id)))
            self.setDriver('GV3', self.bool2ISY(self.TEV.teslaEV_GetLockState(self.id)))
            logging.debug('GV4: {}'.format(self.TEV.getTEV_onLine(self.id)))
            self.setDriver('GV4', self.TEV.getTEV_onLine(self.id))
            logging.debug('GV5: {}'.format(self.TEV.teslaEV_GetOnlineState(self.id)))
            self.setDriver('GV5', self.state2ISY(self.TEV.teslaEV_GetOnlineState(self.id)))
            logging.debug('GV6-9: {}'.format(self.TEV.teslaEV_GetWindoStates(self.id)))
            temp = self.TEV.teslaEV_GetWindoStates(self.id)
            self.setDriver('GV6', temp['FrontLeft'])
            self.setDriver('GV7', temp['FrontRight'])
            self.setDriver('GV8', temp['RearLeft'])
            self.setDriver('GV9', temp['RearRight'])
            logging.debug('GV10: {}'.format(self.TEV.teslaEV_GetSunRoofState(self.id)))
            self.setDriver('GV10', self.TEV.teslaEV_GetSunRoofState(self.id))
            logging.debug('GV11: {}'.format(self.TEV.teslaEV_GetSunRoofState(self.id)))
            self.setDriver('GV11', self.TEV.teslaEV_GetSunRoofState(self.id))
            logging.debug('GV12: {}'.format(self.TEV.teslaEV_GetSunRoofState(self.id)))
            self.setDriver('GV12', self.TEV.teslaEV_GetSunRoofState(self.id))
        else:
            logging.debug('System not ready yet')


    def ISYupdate (self, command):
        logging.debug('ISY-update called')
        self.TEV.teslaEV_GetInfo(self.id)
        self.updateISYdrivers()

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


