#!/usr/bin/env python3

#from os import truncate
import sys
import time 
import os

try:
    import udi_interface
    logging = udi_interface.LOGGER
    Custom = udi_interface.Custom
except ImportError:
    import logging
    logging.basicConfig(level=30)


#from TeslaEVInfo import tesla_info
#from TeslaPWCtrlNodeNode import teslaPWSetupNode
from TeslaEVStatusNode import teslaEV_StatusNode
from TeslaCloudEVapi  import teslaCloudEVapi

#NODES_DEBUG = True
NODES_DEBUG = False



class TeslaEVController(udi_interface.Node):
    def __init__(self, polyglot, primary, address, name):
        super().__init__(polyglot, primary, address, name)
        self.poly = polyglot

        logging.info('_init_ Tesla EV Controller - 1')
        self.ISYforced = False
        self.name = 'Tesla EV Info'
        self.primary = primary
        self.address = address


        self.poly.subscribe(self.poly.START, self.start, address)
        self.poly.subscribe(self.poly.LOGLEVEL, self.handleLevelChange)
        self.poly.subscribe(self.poly.CUSTOMPARAMS, self.handleParams)
        self.poly.subscribe(self.poly.POLL, self.systemPoll)
        self.poly.subscribe(self.poly.ADDNODEDONE, self.node_queue)
        self.n_queue = []

        self.Parameters = Custom(polyglot, 'customparams')
        self.Notices = Custom(polyglot, 'notices')
       
        logging.debug('self.address : ' + str(self.address))
        logging.debug('self.name :' + str(self.name))
        self.hb = 0

        self.connected = False
        self.nodeDefineDone = False
        self.statusNodeReady = False

        self.poly.ready()
        self.poly.addNode(self)
        self.wait_for_node_done()
        self.node = self.poly.getNode(self.address)
        self.node.setDriver('ST', 1, True, True)

        self.poly.setLogLevel('debug')
        logging.debug('Controller init DONE')

    def node_queue(self, data):
        self.n_queue.append(data['address'])

    def wait_for_node_done(self):
        while len(self.n_queue) == 0:
            time.sleep(0.1)
        self.n_queue.pop()


    def start(self):
        logging.debug('start')
        self.tesla_initialize()
        # Wait for things to initialize....

 


        # Poll for current values (and update drivers)
        #self.TEV.pollSystemData('all')          
        #self.updateISYdrivers('all')
        #self.systemReady = True
   

    '''
    This may be called multiple times with different settings as the user
    could be enabling or disabling the various types of access.  So if the
    user changes something, we want to re-initialize.
    '''
    def tesla_initialize(self):
        logging.debug('starting Login process')
        #try:
            #del self.Parameters['REFRESH_TOKEN']
        self.TEV = teslaCloudEVapi()
        self.connected = self.TEV.isConnectedToEV()
        if not self.connected:
            logging.info ('Failed to get acces to Tesla Cloud')
            exit()
        if NODES_DEBUG:
            if (os.path.exists('./EVlist.txt')):
                dataFile = open('./EVlist.txt', 'r')
                self.vehicleList = dataFile.read()
                dataFile.close()
            if (os.path.exists('./EVinfo.txt')):
                dataFile = open('./EVinfo.txt', 'r')
                vehicleInfo = dataFile.read()
                dataFile.close()

                nodeName = vehicleInfo['response']['display_name']
                nodeAdr = 'vehicle'+str(vehicle+1)
                if not self.poly.getNode(nodeAdr):
                    logging.info('Creating Status node for:  {} {} {} {}'.format( self.address, nodeAdr, nodeName, vehicleId,))
                    node = teslaEV_StatusNode(self.poly, self.address, nodeAdr, nodeName, vehicleId, self.TEV)
                    self.poly.addNode(node)             
                    self.wait_for_node_done()                    
        else:
            self.vehicleList = self.TEV.teslaEV_GetIdList()
            self.GV1 =len(self.vehicleList)
            self.setDriver('GV1', self.GV1)
            for vehicle in range(0,len(self.vehicleList)):
                vehicleId = self.vehicleList[vehicle]
                vehicleInfo = self.TEV.teslaEV_GetInfo(vehicleId)
                logging.info('EV info: {} = {}'.format(vehicleId, vehicleInfo))
                nodeName = vehicleInfo['display_name']
                
                nodeAdr = 'vehicle'+str(vehicle+1)
                if not self.poly.getNode(nodeAdr):
                    logging.info('Creating Status node for {}'.format(nodeAdr))
                    self.statusNode = teslaEV_StatusNode(self.poly, self.address, nodeAdr, nodeName, vehicleId, self.TEV)
                    self.poly.addNode(self.statusNode )             
                    self.wait_for_node_done()     
                    self.statusNodeReady = True
                    
        self.longPoll()

        #except Exception as e:
        #    logging.error('Exception Controller start: '+ str(e))
        #    logging.info('Did not connect to EV ')
       
        logging.debug ('Controller - initialization done')

    def handleLevelChange(self, level):
        logging.info('New log level: {}'.format(level))

    def handleParams (self, userParam ):
        logging.debug('handleParams')
        supportParams = ['REFRESH_TOKEN']
        self.Parameters.load(userParam)

        logging.debug('handleParams load')
        #logging.debug(self.Parameters)  ### TEMP
        self.poly.Notices.clear()
        self.cloudAccess = False
        for param in userParam:
            if param not in supportParams:
                del self.Parameters[param]
                logging.debug ('erasing key: ' + str(param))

        if 'REFRESH_TOKEN' in userParam:
            cloud_token = userParam['REFRESH_TOKEN']
            if cloud_token != '':
                if (os.path.exists('./inputToken.txt')):
                    
                    dataFile = open('./inputToken.txt', 'r')
                    tmpToken = dataFile.read()
                    dataFile.close()
                    if tmpToken != cloud_token:
                        logging.info('Newer input from config')
                        dataFile = open('./inputToken.txt', 'w')
                        dataFile.write( cloud_token)
                        dataFile.close()
                        dataFile = open('./refreshToken.txt', 'w')
                        dataFile.write( cloud_token)
                        dataFile.close()   
                        self.Rtoken = cloud_token
                    elif (os.path.exists('./refreshToken.txt')): #assume refreshToken is newer
                        dataFile = open('./refreshToken.txt', 'r')
                        self.Rtoken = dataFile.read()
                        cloud_token = self.Rtoken
                        dataFile.close() 
                    else: #InputToken must exist (this should never trigger)
                        dataFile = open('./refreshToken.txt', 'w') 
                        dataFile.write( cloud_token)
                        dataFile.close()                   
                        self.Rtoken = cloud_token

                else: #first time input - must overwrite refreshToken as well 
                    dataFile = open('./inputToken.txt', 'w')
                    dataFile.write( cloud_token)
                    dataFile.close()
                    dataFile = open('./refreshToken.txt', 'w')
                    dataFile.write( cloud_token)
                    dataFile.close()                        
                    self.Rtoken = cloud_token    
                                 
            else: # nothing has changed - use refreshToken 
                if (os.path.exists('./refreshToken.txt')):
                    dataFile = open('./refreshToken.txt', 'r')
                    self.Rtoken = dataFile.read()
                    cloud_token = self.Rtoken
                    dataFile.close()
                    
        else: #no token provided yet 
            if (os.path.exists('./refreshToken.txt')):
                dataFile = open('./refreshToken.txt', 'r')
                self.Rtoken = dataFile.read() 
                cloud_token = self.Rtoken  
                dataFile.close()
                noFile = False
            else:
                self.poly.Notices['ct'] = 'Missing Cloud Refresh Token'
                cloud_token = ''
               
        if cloud_token == '':
            self.poly.Notices['ct'] = 'Please enter the Tesla Refresh Token - see readme for futher info '
        else:
            logging.debug('Cloud access is valid, configure....')
            self.cloudAccess = True
            self.tesla_initialize( )
        logging.info('Rtoken: {}'.format(self.Rtoken))
        logging.debug('done with parameter processing')
        
    def stop(self):
        #self.removeNoticesAll()
        if self.TEV:
            self.TEV.disconnectTEV()
        self.setDriver('ST', 0 )
        logging.debug('stop - Cleaning up')
        self.poly.stop()

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
        #if self.TEV.pollSystemData('critical'):
        #    for node in self.poly.nodes():
        #        node.updateISYdrivers('critical')
        #else:
        #    logging.info('Problem polling data from Tesla system') 

        
    def longPoll(self):
        logging.info('Tesla EV  Controller longPoll - connected = {}'.format(self.TEV.isConnectedToEV()))
        if self.statusNode.subnodesReady() and self.statusNodeReady:
            for node in self.poly.nodes():
                #if node != 'controller'    
                logging.debug('Controller poll  node {}'.format(node) )
                node.poll()
        else:
            logging.info('Waiting for all nodes to be created')


    def poll(self): # dummey poll function 
        pass

    def updateISYdrivers(self, level):
        logging.debug('System updateISYdrivers - ' + str(level))       
        if level == 'all':
            value = self.TEV.isNodeServerUp()

            self.setDriver('GV0', value)
            self.setDriver('GV1', self.GV1)
            logging.debug('CTRL Update ISY drivers : GV0, GV1  value: {}, {}'.format(value. self.GV1))

        elif level == 'critical':
            value = self.TEV.isNodeServerUp()
            self.setDriver('GV0', value)   
            logging.debug('CTRL Update ISY drivers : GV2  value:' + str(value) )
        else:
            logging.error('Wrong parameter passed: ' + str(level))
 

    def ISYupdate (self, command):
        logging.debug('ISY-update called')

        self.longPoll()
        #if self.TEV.pollSystemData('all'):
        #    self.updateISYdrivers('all')
        #    #self.reportDrivers()
        #    for node in self.nodes:
        #        #logging.debug('Node : ' + node)
        #        if node != self.address :
        #            self.nodes[node].longPoll()
 
    id = 'controller'
    commands = { 'UPDATE': ISYupdate }
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
        #logging.info('Starting Tesla Power Wall Controller')
        polyglot = udi_interface.Interface([])
        polyglot.start()
        polyglot.updateProfile()
        polyglot.setCustomParamsDoc()
        TeslaEVController(polyglot, 'controller', 'controller', 'Tesla EVs')
        polyglot.runForever()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
