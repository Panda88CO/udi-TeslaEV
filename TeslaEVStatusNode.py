#!/usr/bin/env python3

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
        logging.info('_init_ Tesla EV  Status Node')
        self.n_queue = []
        self.ISYforced = False
        self.EVid = id
        self.TEV = TEV
        self.primary = primary
        self.address = address
        self.name = name
        self.statusNodeReady = False
        self.climateNodeReady = False
        self.chargeNodeReady = False

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        


    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
            #logging.debug('wait_for_node_done')
        self.n_queue.pop()
    

    def start(self):       
        logging.info('Start Tesla EV Status Node for {}'.format(self.EVid)) 
        tmpStr = re.findall('[0-9]+', self.address)
        self.nbrStr = tmpStr.pop()
        self.setDriver('ST', 1, True, True)
        self.forceUpdateISYdrivers()
        self.createSubNodes()
        self.statusNodeReady = True
        
    def createSubNodes(self):
        logging.debug('Creating sub nodes for {}'.format(self.EVid))
        nodeAdr = 'climate'+self.nbrStr
        if not self.poly.getNode(nodeAdr):
            logging.info('Creating ClimateNode: {} - {} {} {} {}'.format(nodeAdr, self.address, nodeAdr,'EV climate Info',  self.EVid ))
            climateNode = teslaEV_ClimateNode(self.poly, self.address, nodeAdr, 'EV climate Info', self.EVid, self.TEV )
            self.poly.addNode(climateNode)             
            self.wait_for_node_done()   
            self.climateNodeReady =True
            climateNode.updateISYdrivers()

        nodeAdr = 'charge'+self.nbrStr
        if not self.poly.getNode(nodeAdr):
            logging.info('Creating ChargingNode: {} - {} {} {} {}'.format(nodeAdr, self.address, nodeAdr,'EV Charging Info',  self.EVid ))
            chargeNode = teslaEV_ChargeNode(self.poly, self.address, nodeAdr, 'EV Charging Info', self.EVid, self.TEV )
            self.poly.addNode(chargeNode)             
            self.wait_for_node_done()   
            self.chargeNodeReady = True
            chargeNode.updateISYdrivers()

    def subnodesReady(self):
        return(self.climateNodeReady and self.chargeNodeReady )

    def stop(self):
        logging.debug('stop - Cleaning up')

    def bool2ISY(self, bool):
        if bool == True:
            return(1)
        elif bool == False:
            return(0)
        else:
            return(99)


    def state2ISY(self, state):
        if state.lower() == 'offline':
            return(0)
        elif state.lower() == 'online':
            return(1)
        elif state.lower() == 'sleeping':
            return(2) 
        elif state.lower() == 'unknown':
            return(99)
        else:          
            logging.error('Unknown state passed {}'.format(state))
            return(99)



    def online2ISY(self, state):
        if state.lower() == 'online':
            return(1)
        else:
            return(0)

    def openClose2ISY(self, state):
        if state == None:
            return(99)
        elif state == 'closed':
            return(0)
        else:
            return(1)

    def ready(self):
        return(self.chargeNodeReady and self.climateNodeReady)

    def poll (self):    
        logging.info('Status Node Poll for {}'.format(self.EVid))        
        self.TEV.teslaEV_GetInfo(self.EVid)
        if self.statusNodeReady:
            if self.TEV.carState != 'Offline':
                self.updateISYdrivers()
            else:
                logging.info('Car appears off-line/sleeping - not updating data')

    def forceUpdateISYdrivers(self):
        logging.debug('forceUpdateISYdrivers: {}'.format(self.EVid))
        time.sleep(1)
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()


    def updateISYdrivers(self):
        try:
            
            logging.info('updateISYdrivers - Status for {}'.format(self.EVid))
            #if self.TEV.isConnectedToEV():
            #self.TEV.teslaEV_GetInfo(self.EVid)
            temp = {}
            logging.debug('StatusNode updateISYdrivers {}'.format(self.TEV.teslaEV_GetStatusInfo(self.EVid)))
            logging.debug('GV1: {} '.format(self.TEV.teslaEV_GetCenterDisplay(self.EVid)))
            self.setDriver('GV1', self.TEV.teslaEV_GetCenterDisplay(self.EVid), True, True)
            logging.debug('GV2: {} '.format(self.TEV.teslaEV_HomeLinkNearby(self.EVid)))
            self.setDriver('GV2', self.bool2ISY(self.TEV.teslaEV_HomeLinkNearby(self.EVid)), True, True)
            logging.debug('GV0: {} '.format(self.TEV.teslaEV_nbrHomeLink(self.EVid)))
            self.setDriver('GV0', self.TEV.teslaEV_nbrHomeLink(self.EVid), True, True)
            logging.debug('GV3: {}'.format(self.TEV.teslaEV_GetLockState(self.EVid)))
            self.setDriver('GV3', self.bool2ISY(self.TEV.teslaEV_GetLockState(self.EVid)), True, True)
            logging.debug('GV4: {} {}'.format(self.TEV.teslaEV_GetOdometer(self.EVid), self.TEV.teslaEV_GetDistUnit()))
            if self.TEV.teslaEV_GetDistUnit() == 1:
                self.setDriver('GV4', self.TEV.teslaEV_GetOdometer(self.EVid), True, True, uom=116)
            else:
                self.setDriver('GV4', self.TEV.teslaEV_GetOdometer(self.EVid) , True, True, uom=83 )

            logging.debug('GV5: {}'.format(self.TEV.teslaEV_GetOnlineState(self.EVid)))
            self.setDriver('GV5', self.online2ISY(self.TEV.teslaEV_GetOnlineState(self.EVid)), True, True)
            logging.debug('GV6-9: {}'.format(self.TEV.teslaEV_GetWindoStates(self.EVid)))
            temp = self.TEV.teslaEV_GetWindoStates(self.EVid)
            logging.debug('Windows: {} {} {} {}'.format(temp['FrontLeft'], temp['FrontRight'], temp['RearLeft'],temp['RearRight']))
            if  temp['FrontLeft'] == None:
                temp['FrontLeft'] = 99
            if temp['FrontRight'] == None:    
                temp['FrontRight'] = 99
            if temp['RearLeft'] == None:    
                temp['RearLeft'] = 99
            if temp['RearRight'] == None:    
                temp['RearRight'] = 99
            self.setDriver('GV6', temp['FrontLeft'], True, True)
            self.setDriver('GV7', temp['FrontRight'], True, True)
            self.setDriver('GV8', temp['RearLeft'], True, True)
            self.setDriver('GV9', temp['RearRight'], True, True)
            logging.debug('GV10: {}'.format(self.TEV.teslaEV_GetSunRoofPercent(self.EVid)))
            logging.debug('GV10: {}'.format(self.TEV.teslaEV_GetSunRoofPercent(self.EVid)))
            self.setDriver('GV10', self.TEV.teslaEV_GetSunRoofPercent(self.EVid), True, True, 51)
            #elif self.TEV.teslaEV_GetSunRoofState(self.EVid) != None:
            #    logging.debug('GV10: {}'.format(self.TEV.teslaEV_GetSunRoofState(self.EVid)))
            #    self.setDriver('GV10', self.openClose2ISY(self.TEV.teslaEV_GetSunRoofState(self.EVid)), True, True, 25)

            logging.debug('GV11: {}'.format(self.TEV.teslaEV_GetTrunkState(self.EVid)))
            self.setDriver('GV11', self.TEV.teslaEV_GetTrunkState(self.EVid), True, True)

            logging.debug('GV12: {}'.format(self.TEV.teslaEV_GetFrunkState(self.EVid)))
            self.setDriver('GV12', self.TEV.teslaEV_GetFrunkState(self.EVid), True, True)
            logging.debug('GV13: {}'.format(self.TEV.teslaEV_GetCarState(self.EVid)))
            self.setDriver('GV13', self.state2ISY(self.TEV.teslaEV_GetCarState(self.EVid)), True, True)
            
            ideal_bat = self.TEV.teslaEV_GetIdelBatteryRange(self.EVid)
            if ideal_bat:
                ideal_bat = round(ideal_bat, 2)
                logging.debug('GV16: {}'.format(ideal_bat))
                self.setDriver('GV16', ideal_bat, True, True, 56)   
            else:
                logging.debug('GV16: {}'.format('NONE'))
                self.setDriver('GV16', 99, True, True, 25)
                     
            
            location = self.TEV.teslaEV_GetLocation(self.EVid)
            if location['longitude']:
                logging.debug('GV17: {}'.format(round(location['longitude'], 3)))
                self.setDriver('GV17', round(location['longitude'], 3), True, True, 56)
            else:
                logging.debug('GV17: {}'.format('NONE'))
                self.setDriver('GV17', 99, True, True, 25)
            if location['latitude']:
                logging.debug('GV18: {}'.format(round(location['latitude'], 3)))
                self.setDriver('GV18', round(location['latitude'], 3), True, True, 56)
            else:
                logging.debug('GV18: {}'.format('NONE'))
                self.setDriver('GV18', 99, True, True, 25)

            logging.debug('GV19: {}'.format(round(float(self.TEV.teslaEV_GetTimeSinceLastCarUpdate(self.EVid)/60/60), 2)))
            self.setDriver('GV19', round(float(self.TEV.teslaEV_GetTimeSinceLastCarUpdate(self.EVid)/60/60), 2), True, True, 20)            

            logging.debug('GV20: {}'.format(round(float(self.TEV.teslaEV_GetTimeSinceLastStatusUpdate(self.EVid)/60/60), 2)))
            self.setDriver('GV20', round(float(self.TEV.teslaEV_GetTimeSinceLastStatusUpdate(self.EVid)/60/60), 2), True, True, 20)
       
            #else:
            #    logging.info('System not ready yet')

        except Exception as e:
            logging.error('updateISYdriver Status node failed: {}'.format(e))

    def ISYupdate (self, command):
        logging.info('ISY-update called')
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()

    def evWakeUp (self, command):
        logging.info('EVwakeUp called')
        self.TEV.teslaEV_Wake(self.EVid)

        self.forceUpdateISYdrivers()

    def evHonkHorn (self, command):
        logging.info('EVhonkHorn called')
        #self.TEV.teslaEV_Wake(self.EVid)
        self.TEV.teslaEV_HonkHorn(self.EVid)

        self.forceUpdateISYdrivers()

    def evFlashLights (self, command):
        logging.info('EVflashLights called')
        #self.TEV.teslaEV_Wake(self.EVid)
        self.TEV.teslaEV_FlashLights(self.EVid)

        self.forceUpdateISYdrivers()

    def evControlDoors (self, command):
        logging.info('EVctrlDoors called')
        #self.TEV.teslaEV_Wake(self.EVid)
        doorCtrl = int(float(command.get('value')))
        if doorCtrl == 1:
            self.TEV.teslaEV_Doors(self.EVid, 'unlock')
        elif doorCtrl == 0:
            self.TEV.teslaEV_Doors(self.EVid, 'lock')            
        else:
            logging.error('Unknown command for evControlDoors {}'.format(command))
        #self.setDriver('GV3', self.bool2ISY(self.TEV.teslaEV_GetLockState(self.EVid)), True, True)
  
        self.forceUpdateISYdrivers()


    def evControlSunroof (self, command):
        logging.info('evControlSunroof called')
        #self.TEV.teslaEV_Wake(self.EVid)
        sunroofCtrl = int(float(command.get('value')))
        if sunroofCtrl == 1:
            self.TEV.teslaEV_SunRoof(self.EVid, 'vent')
        elif sunroofCtrl == 0:
            self.TEV.teslaEV_SunRoof(self.EVid, 'close')            
        else:
            logging.error('Wrong command for evSunroof: {}'.format(sunroofCtrl))         
        if self.TEV.teslaEV_GetSunRoofPercent(self.EVid) != None:
            logging.debug('GV10: {}'.format(self.TEV.teslaEV_GetSunRoofPercent(self.EVid)))
            self.setDriver('GV10', self.TEV.teslaEV_GetSunRoofPercent(self.EVid), True, True, 51)
        elif self.TEV.teslaEV_GetSunRoofState(self.EVid) != None:
            logging.debug('GV10: {}'.format(self.TEV.teslaEV_GetSunRoofState(self.EVid)))
            self.setDriver('GV10', self.openClose2ISY(self.TEV.teslaEV_GetSunRoofState(self.EVid)), True, True, 25)

        self.forceUpdateISYdrivers()

    def evOpenFrunk (self, command):
        logging.info('evOpenFrunk called')
        #self.TEV.teslaEV_Wake(self.EVid)                
        self.TEV.teslaEV_TrunkFrunk(self.EVid, 'Frunk')

        self.forceUpdateISYdrivers()
        #self.setDriver('GV12', self.TEV.teslaEV_GetFrunkState(self.EVid), True, True)

    def evOpenTrunk (self, command):
        logging.info('evOpenTrunk called')   
        #self.TEV.teslaEV_Wake(self.EVid)             
        self.TEV.teslaEV_TrunkFrunk(self.EVid, 'Trunk')

        self.forceUpdateISYdrivers()
        #self.setDriver('GV11', self.TEV.teslaEV_GetTrunkState(self.EVid), True, True)


    def evHomelink (self, command):
        logging.info('evHomelink called')
        #self.TEV.teslaEV_Wake(self.EVid)   
        self.TEV.teslaEV_HomeLink(self.EVid)

        self.forceUpdateISYdrivers()
    '''
    def setDistUnit(self,command):
        logging.debug('setDistUnit')
        distUnit = int(float(command.get('value')))   
        self.TEV.teslaEV_SetDistUnit( distUnit )

        self.forceUpdateISYdrivers()
    '''   

    id = 'evstatus'
    commands = { 'UPDATE': ISYupdate, 
                 'WAKEUP' : evWakeUp,
                 'HONKHORN' : evHonkHorn,
                 'FLASHLIGHT' : evFlashLights,
                 'DOORS' : evControlDoors,
                 'SUNROOF' : evControlSunroof,
                 'TRUNK' : evOpenTrunk,
                 'FRUNK' : evOpenFrunk,
                 'HOMELINK' : evHomelink,
                }


    drivers = [
            {'driver': 'ST', 'value': 0, 'uom': 2},
            
            {'driver': 'GV1', 'value': 99, 'uom': 25},  #center_display_state
            {'driver': 'GV2', 'value': 99, 'uom': 25},  # Homelink Nearby
            {'driver': 'GV0', 'value': 99, 'uom': 25},  # nbr homelink devices
            {'driver': 'GV3', 'value': 99, 'uom': 25},  #locked
            {'driver': 'GV4', 'value': 0, 'uom': 116},  #odometer
            {'driver': 'GV5', 'value': 99, 'uom': 25},  #state (on line)
            {'driver': 'GV6', 'value': 99, 'uom': 25},  #fd_window
            {'driver': 'GV7', 'value': 99, 'uom': 25},  #fp_window
            {'driver': 'GV8', 'value': 99, 'uom': 25},  #rd_window
            {'driver': 'GV9', 'value': 99, 'uom': 25},  #rp_window
            {'driver': 'GV10', 'value': 0, 'uom': 51}, #sun_roof_percent_open
            {'driver': 'GV11', 'value': 0, 'uom': 25}, #trunk
            {'driver': 'GV12', 'value': 0, 'uom': 25}, #frunk
            {'driver': 'GV13', 'value': 99, 'uom': 25}, #car State
            {'driver': 'GV16', 'value': 99, 'uom': 25}, #longitude
            {'driver': 'GV17', 'value': 99, 'uom': 25}, #longitude
            {'driver': 'GV18', 'value': 99, 'uom': 25}, #latitude   
            {'driver': 'GV19', 'value': 0, 'uom': 20},  #Last combined update Hours           
            {'driver': 'GV20', 'value': 0, 'uom': 20},  #Last update hours                        
            ]


