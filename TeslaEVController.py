#!/usr/bin/env python3

import sys
import time 


try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=30)


from TeslaEVStatusNode import teslaEV_StatusNode
from TeslaCloudEVapi  import teslaCloudEVapi



class TeslaEVController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super(TeslaEVController, self).__init__(polyglot, primary, address, name)
        logging.setLevel(10)
        self.poly = polyglot
        self.n_queue = []
        self.TEV = None
        logging.info('_init_ Tesla EV Controller ')
        self.ISYforced = False
        self.name = 'Tesla EV Info'
        self.primary = primary
        self.address = address
        #self.tokenPassword = ""
        self.Rtoken = None
        self.dUnit = 1 #  Miles = 1, Kilometer = 0
        self.supportParams = ['REFRESH_TOKEN', 'DIST_UNIT']

        self.Parameters = Custom(polyglot, 'customParams')      
        self.Notices = Custom(polyglot, 'notices')

        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.handleParams)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        



        #logging.debug('self.address : ' + str(self.address))
        #logging.debug('self.name :' + str(self.name))
        self.hb = 0

        self.connected = False
        self.nodeDefineDone = False
        self.statusNodeReady = False

        self.poly.updateProfile()
        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.setDriver('ST', 1, True, True)

        self.tempUnit = 0 # C
        self.distUnit = 0 # KM

        #self.poly.setLogLevel('debug')
        logging.info('Controller init DONE')

    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()


    def start(self):
        logging.info('start')
        #self.Parameters.load(customParams)
        #self.poly.updateProfile()
        #self.poly.setCustomParamsDoc()
        '''
        for param in self.supportParams:
            if param not in self.Parameters:
                self.Parameters[param] = ''
        '''
        logging.debug('start params: {}'.format(self.Parameters))
        self.tesla_initialize()
        self.createNodes()

        # Wait for things to initialize....
        # Poll for current values (and update drivers)
        #self.TEV.pollSystemData('all')          
        #self.updateISYdrivers('all')
        #self.systemReady = True


    def stop(self):
        self.Notices.clear()
        if self.TEV:
            self.TEV.disconnectTEV()
        self.setDriver('ST', 0 , True, True)
        logging.debug('stop - Cleaning up')
        self.poly.stop()

    def query(self,command=None):
        """
        Optional.

        The query method will be called when the ISY attempts to query the
        status of the node directly.  You can do one of two things here.
        You can send the values currently held by Polyglot back to the
        ISY by calling reportDriver() or you can actually query the 
        device represented by the node and report back the current 
        status.
        """
        nodes = self.poly.getNodes()
        for node in nodes:
            nodes[node].reportDrivers()

    '''
    This may be called multiple times with different settings as the user
    could be enabling or disabling the various types of access.  So if the
    user changes something, we want to re-initialize.
    '''

    def tesla_initialize(self):
        logging.info('starting Login process')
        try:
            logging.debug('token = {}'.format(self.Rtoken))
            while self.Rtoken == '':
                logging.info('Waiting for token')
                time.sleep(10)
            self.TEV = teslaCloudEVapi(self.Rtoken)
            self.connected = self.TEV.isConnectedToEV()
            if not self.connected:
                logging.error ('Failed to get acces to Tesla Cloud')
                exit()
            else:
                self.setDriver('GV0', 1, True, True)
                self.TEV.teslaEV_SetDistUnit(self.dUnit)
        except Exception as e:
            logging.debug('Exception Controller start: '+ str(e))
            logging.error('Did not connect to Tesla Cloud ')

        logging.debug ('Controller - initialization done')

    def createNodes(self):
        try:
            self.vehicleList = self.TEV.teslaEV_GetIdList()
            logging.debug('vehicleList: {}'.format(self.vehicleList))
            self.GV1 =len(self.vehicleList)
            self.setDriver('GV1', self.GV1, True, True)
            self.setDriver('GV0', 1, True, True)
            for vehicle in range(0,len(self.vehicleList)):
                vehicleId = self.vehicleList[vehicle]
                self.TEV.teslaEV_UpdateCloudInfo(vehicleId)
                vehicleInfo = self.TEV.teslaEV_GetInfo(vehicleId)
                logging.info('EV info: {} = {}'.format(vehicleId, vehicleInfo))
                nodeName = vehicleInfo['display_name']
                
                nodeAdr = 'vehicle'+str(vehicle+1)
                if not self.poly.getNode(nodeAdr):
                    logging.info('Creating Status node for {}'.format(nodeAdr))
                    statusNode = teslaEV_StatusNode(self.poly, nodeAdr, nodeAdr, nodeName, vehicleId, self.TEV)
                    self.poly.addNode(statusNode )             
                    self.wait_for_node_done()     
                    self.statusNodeReady = True
                    
            self.longPoll()
        except Exception as e:
            logging.error('Exception Controller start: '+ str(e))
            logging.info('Did not obtain data from EV ')




    def handleLevelChange(self, level):
        logging.info('New log level: {}'.format(level))

    def handleParams (self, customParams ):
        logging.debug('handleParams')
        #supportParams = ['REFRESH_TOKEN', 'TOKEN_PASSWORD']
        supportParams = ['REFRESH_TOKEN', 'DIST_UNIT']
        self.Parameters.load(customParams)

        logging.debug('handleParams load - {} {}'.format(customParams, self.Parameters))
        #logging.debug(self.Parameters)  ### TEMP
        self.poly.Notices.clear()
        self.cloudAccess = False
        '''
        for param in customParams:
            if param not in supportParams:
                del self.Parameters[param]
                logging.debug ('erasing key: ' + str(param))
        '''
        '''
        if 'TOKEN_PASSWORD' in customParams:
            self.tokenPassword = self.Parameters['TOKEN_PASSWORD']
            if self.tokenPassword == "":
                self.poly.Notices['tp'] = 'Enter a Password to encrypt Tokens stored in Files'
            else:
                if 'tp' in self.poly.Notices:
                    self.poly.Notices.delete('tp')
        else:
            self.poly.Notices['tp'] = 'Enter a Password to encrypt Tokens stored in Files'
            self.tokenPassword == ""
        '''
        if 'REFRESH_TOKEN' in customParams:
            logging.debug('REFRESH_TOKEN')
            self.Rtoken = self.Parameters['REFRESH_TOKEN']
            if self.Rtoken  == '':
                self.poly.Notices['ct'] = 'Missing Cloud Refresh Token'

            else:
                if 'ct' in self.poly.Notices:
                    self.poly.Notices.delete('ct')                   
        else:
            self.poly.Notices['ct'] = 'Missing Cloud Refresh Token'
            self.Rtoken  = ''
           
        if 'DIST_UNIT' in customParams:
            logging.debug('DIST_UNIT')
            temp  = self.Parameters['DIST_UNIT']
            if temp == '':
                self.poly.Notices['du'] = 'Missing Distance Unit ((M)iles/(K)ilometers)'
            else:
                if temp[0] == 'k' or temp[0] == 'K':
                    self.dUnit = 0
                    if 'du' in self.poly.Notices:
                        self.poly.Notices.delete('du')
                                    
                    self.poly.Notices.delete('du')
                elif temp[0] == 'm' or temp[0] == 'M':
                    self.dUnit = 1
                    if 'du' in self.poly.Notices:
                        self.poly.Notices.delete('du')
            
                
                            
        else:
            self.poly.Notices['ct'] = 'Missing Cloud Refresh Token'
            self.Rtoken  = ''

               
        if self.Rtoken == '':
            self.poly.Notices['ct'] = 'Please enter the Tesla Refresh Token - see readme for futher info '
        else:

            self.tesla_initialize()
        logging.debug('done with parameter processing')
        

    def heartbeat(self):
        logging.debug('heartbeat: ' + str(self.hb))
        if self.hb == 0:
            self.reportCmd('DON',2)
            self.hb = 1
        else:
            self.reportCmd('DOF',2)
            self.hb = 0
        
    def systemPoll(self, pollList):
        logging.debug('systemPoll')
        if self.TEV:
            if self.TEV.isConnectedToEV(): 
                if 'longPoll' in pollList:
                    self.longPoll()
                elif 'shortPoll' in pollList:
                    self.shortPoll()
            else:
                logging.info('Waiting for system/nodes to initialize')


    def shortPoll(self):
        logging.info('Tesla EV Controller shortPoll(HeartBeat)')
        self.heartbeat()    
        if self.TEV.isConnectedToEV():
            for vehicle in range(0,len(self.vehicleList)):
                 self.TEV.teslaEV_getLatestCloudInfo(self.vehicleList[vehicle])
            try:
                nodes = self.poly.getNodes()
                for node in nodes:
                    #if node != 'controller'    
                    logging.debug('Controller poll  node {}'.format(node) )
                    nodes[node].poll()
            except Exception as E:
                logging.info('Not all nodes ready: {}'.format(E))

            self.Rtoken  = self.TEV.getRtoken()
            if self.Rtoken  != self.Parameters['REFRESH_TOKEN']:
                self.Parameters['REFRESH_TOKEN'] = self.Rtoken 
        
    def longPoll(self):
        logging.info('Tesla EV  Controller longPoll - connected = {}'.format(self.TEV.isConnectedToEV()))
        
        if self.TEV.isConnectedToEV():
            for vehicle in range(0,len(self.vehicleList)):
                 self.TEV.teslaEV_UpdateCloudInfo(self.vehicleList[vehicle])
            try:
                nodes = self.poly.getNodes()
                for node in nodes:
                    #if node != 'controller'    
                    logging.debug('Controller poll  node {}'.format(node) )
                    nodes[node].poll()
            except Exception as E:
                logging.info('Not all nodes ready: {}'.format(E))

            self.Rtoken  = self.TEV.getRtoken()
            if self.Rtoken  != self.Parameters['REFRESH_TOKEN']:
                self.Parameters['REFRESH_TOKEN'] = self.Rtoken 


    def poll(self): # dummey poll function 
        self.updateISYdrivers()
        pass

    def updateISYdrivers(self):
        logging.debug('System updateISYdrivers - Controller')       
        value = self.TEV.isConnectedToEV()
        self.setDriver('GV0', value, True, True)
        self.setDriver('GV1', self.GV1, True, True)





    def ISYupdate (self, command):
        logging.debug('ISY-update called')

        self.longPoll()

 
    id = 'controller'
    commands = { 'UPDATE': ISYupdate ,
                
                }

    drivers = [
            {'driver': 'ST', 'value':0, 'uom':2},
            {'driver': 'GV0', 'value':0, 'uom':25},  
            {'driver': 'GV1', 'value':0, 'uom':107},
            ]
            # ST - node started
            # GV0 Access to TeslaApi
            # GV1 Number of EVs



if __name__ == "__main__":
    try:
        logging.info('Starting TeslaEV Controller')
        polyglot = udi_interface.Interface([])
        polyglot.start('0.1.32')
        polyglot.updateProfile()
        polyglot.setCustomParamsDoc()
        TeslaEVController(polyglot, 'controller', 'controller', 'Tesla EVs')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
