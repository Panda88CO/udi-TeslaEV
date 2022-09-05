#!/usr/bin/env python3

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=logging.DEBUG)

import time

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
        logging.info('Start Tesla EV charge Node: {}'.format(self.EVid))  
        self.setDriver('ST', 1, True, True)
        self.nodeReady = True
        #self.updateISYdrivers()

        

    def stop(self):
        logging.debug('stop - Cleaning up')
    
    def poll(self):
        
        logging.debug('Charge node {}'.format(self.EVid) )
        if self.nodeReady:
            self.updateISYdrivers()
    
    def chargeNodeReady (self):
        return(self.nodeReady )
   
    def cond2ISY(self, condition):
        if condition == None:
            return(99)
        elif condition:
            return(1)
        else:
            return(0)

    def latch2ISY(self, state):
        if state.lower() == 'engaged':
            return(1)
        elif state.lower() == 'blocking':
            return(2)
        elif state.lower() == 'disengaged':
            return(0)
        else:
            return(99)

    def state2ISY(self, state): # Still TBD - 
        stateL = state.lower()
        if stateL == 'disconnected':
            return(0)
        elif stateL == 'nopower':
            return(1)          
        elif stateL == 'starting':
            return(2)
        elif stateL == 'charging':
            return(3)
        elif stateL == 'stopped':
            return(4)
        elif stateL == 'complete':
            return(5)
        else:
            return(99)  

    def forceUpdateISYdrivers(self):
        logging.debug('forceUpdateISYdrivers: {}'.format(self.EVid))
        time.sleep(1)
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()

    def updateISYdrivers(self):
        try:
            logging.info('ChargeNode updateISYdrivers {}'.format(self.EVid))
            logging.debug('ChargeNode updateISYdrivers {}'.format(self.TEV.teslaEV_GetChargingInfo(self.EVid)))
            #if self.TEV.isConnectedToEV():
            logging.debug('GV1: {} '.format(self.TEV.teslaEV_FastChargerPresent(self.EVid)))
            self.setDriver('GV1', self.cond2ISY(self.TEV.teslaEV_FastChargerPresent(self.EVid)), True, True)
            logging.debug('GV2: {} '.format(self.TEV.teslaEV_ChargePortOpen(self.EVid)))
            self.setDriver('GV2', self.cond2ISY(self.TEV.teslaEV_ChargePortOpen(self.EVid)), True, True)
            logging.debug('GV3: {}'.format(self.TEV.teslaEV_ChargePortLatched(self.EVid)))
            self.setDriver('GV3', self.cond2ISY(self.TEV.teslaEV_ChargePortLatched(self.EVid)), True, True)
            if self.TEV.teslaEV_GetBatteryLevel(self.EVid) != None:
                logging.debug('BATLVL: {}'.format(self.TEV.teslaEV_GetBatteryLevel(self.EVid)))
                self.setDriver('BATLVL', self.TEV.teslaEV_GetBatteryLevel(self.EVid), True, True, 51)
            else:
                self.setDriver('BATLVL', 99, True, True, 25)
            if self.TEV.teslaEV_MaxChargeCurrent(self.EVid) != None:
                logging.debug('GV5: {}'.format(self.TEV.teslaEV_MaxChargeCurrent(self.EVid)))
                self.setDriver('GV5', self.TEV.teslaEV_MaxChargeCurrent(self.EVid), True, True, 1)
            else:
                self.setDriver('GV5', 99, True, True, 25)
            logging.debug('GV6: {}'.format(self.TEV.teslaEV_ChargeState(self.EVid)))     
            self.setDriver('GV6',self.state2ISY(self.TEV.teslaEV_ChargeState(self.EVid)), True, True)
            logging.debug('GV7: {}'.format(self.TEV.teslaEV_ChargingRequested(self.EVid)))
            self.setDriver('GV7', self.cond2ISY(self.TEV.teslaEV_ChargingRequested(self.EVid)), True, True)
            if self.TEV.teslaEV_GetChargingPower(self.EVid) != None:
                logging.debug('GV8: {}'.format(self.TEV.teslaEV_GetChargingPower(self.EVid)))
                self.setDriver('GV8', self.TEV.teslaEV_GetChargingPower(self.EVid), True, True, 30)
            else:
                self.setDriver('GV8', 99, True, True, 25)
            if self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid) != None:
                logging.debug('GV9: {}'.format(self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid)))
                self.setDriver('GV9', self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid), True, True, 51)
            else:
                self.setDriver('GV9', 99, True, True, 25)

            logging.debug('GV20: {}'.format(self.TEV.teslaEV_GetTimeSinceLastChargeUpdate(self.EVid)))
            self.setDriver('GV20', self.TEV.teslaEV_GetTimeSinceLastChargeUpdate(self.EVid), True, True, 58)

        except Exception as e:
            logging.error('updateISYdrivers charge node failed: {}'.format(e))

    def ISYupdate (self, command):
        logging.info('ISY-update called')
        self.TEV.teslaEV_UpdateCloudInfo(self.EVid)
        self.updateISYdrivers()
     

    def evChargePort (self, command):
        logging.info('evChargePort called')
        chargePort = int(float(command.get('value')))
        self.TEV.teslaEV_Wake(self.EVid)
        if chargePort == 1:
            self.TEV.teslaEV_ChargePort(self.EVid, 'open')
        elif chargePort == 0:
            self.TEV.teslaEV_ChargePort(self.EVid, 'close')
        else:
            logging.debug('Wrong parameter passed to evChargePort : {}'.format(chargePort))
   
        self.forceUpdateISYdrivers()
        #self.setDriver('GV2', self.cond2ISY(self.TEV.teslaEV_ChargePortOpen(self.EVid)), True, True)

    def evChargeControl (self, command):
        logging.info('evChargeControl called')
        chargeCtrl = int(float(command.get('value')))
        if chargeCtrl == 1:
            self.TEV.teslaEV_Charging(self.EVid, 'start')
        elif chargeCtrl == 0:
            self.TEV.teslaEV_Charging(self.EVid, 'stop')
        else:
            logging.debug('Wrong parameter passed to evChargeControl : {}'.format(chargeCtrl))
      
        self.forceUpdateISYdrivers()
        #self.setDriver('GV6',self.state2ISY(self.TEV.teslaEV_ChargeState(self.EVid)), True, True)
        #self.setDriver('GV7', self.cond2ISY(self.TEV.teslaEV_ChargingRequested(self.EVid)), True, True)


    def evSetBatteryChargeLimit (self, command):
        logging.info('evSetBatteryChargeLimit called')
        batLimitPercent = float(command.get('value'))
        self.TEV.teslaEV_Wake(self.EVid)
        self.TEV.teslaEV_SetChargeLimit(self.EVid, batLimitPercent)

        self.forceUpdateISYdrivers()
        #if self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid) != None:
        #    logging.debug('GV9: {}'.format(self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid)))
        #    self.setDriver('GV9', self.TEV.teslaEV_GetBatteryMaxCharge(self.EVid), True, True, 51)
        #else:
        #    self.setDriver('GV9', 99, True, True, 25)

    def evSetCurrentChargeLimit (self, command):
        logging.info('evSetCurrentChargeLimit called')
        
        ampLimit = int(float(command.get('value')))
        self.TEV.teslaEV_Wake(self.EVid)
        self.TEV.teslaEV_SetChargeLimitAmps(self.EVid, ampLimit)

        self.forceUpdateISYdrivers()
        #if self.TEV.teslaEV_MaxChargeCurrent(self.EVid) != None:
        #    logging.debug('GV5: {}'.format(self.TEV.teslaEV_MaxChargeCurrent(self.EVid)))
        #    self.setDriver('GV5', self.TEV.teslaEV_MaxChargeCurrent(self.EVid), True, True, 1)
        #else:
        #    self.setDriver('GV5', 99, True, True, 25)


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
            {'driver': 'GV5', 'value': 0, 'uom': 1},  #charge_current_request_max
            {'driver': 'GV6', 'value': 99, 'uom': 25},  #charging_state
            {'driver': 'GV7', 'value': 0, 'uom': 25},  #charge_enable_request
            {'driver': 'GV8', 'value': 99, 'uom':30},  #charger_power
            {'driver': 'GV9', 'value': 0, 'uom': 51},  #bat charge_limit_soc
            {'driver': 'GV20', 'value': 0, 'uom': 58},  #Last update Epoch


            ]
            


